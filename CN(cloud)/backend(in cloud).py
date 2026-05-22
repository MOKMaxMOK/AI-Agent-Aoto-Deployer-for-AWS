"""将代码上传到 AWS Lambda，运行时设为 Python 3.12，超时至少 300 秒，内存 128 MB。

为 Lambda 配置 Function URL（AuthType 设为 NONE），并确保资源策略允许公开调用。

使用的 AWS 凭证（DevUser）需要以下完全权限：AWSCloudFormationFullAccess、AmazonS3FullAccess、AWSLambda_FullAccess、AmazonAPIGatewayAdministrator 以及 IAMFullAccess（或更细粒度的同等权限）。

务必关闭 S3 账户级“阻止公共访问”：四个阻止开关均设为 false，否则静态网站无法公开访问。

若部署时出现 s3:PutBucketPolicy 被拒，请检查上一步以及桶级 PublicAccessBlockConfiguration 是否被代码自动修补为允许。

首次调用如遇 CORS 错误，请等待片刻后重试；代码已处理 OPTIONS 预检，确保 Function URL 配置正确即可。"""



import json
import urllib.request
import urllib.error
import boto3
import time
import socket
import io
import zipfile

def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return _resp(200, {})

    try:
        body = json.loads(event.get("body", "{}"))
    except Exception:
        return _resp(400, {"error": "Invalid JSON body"})

    action = body.get("action", "")
    if action == "architect":
        return handle_architect(body)
    elif action == "deploy_infra":
        return handle_deploy_infra(body)
    elif action == "upload_code":
        return handle_upload_code(body)
    else:
        return _resp(400, {"error": f"Unknown action: {action}"})

# ==================== 架構生成 ====================
def handle_architect(body):
    resource_groups = body.get("resource_groups", [])
    architect_ai = body.get("architect_ai", {})
    description = body.get("description", "")

    if not resource_groups or not description:
        return _resp(400, {"error": "Missing resource_groups or description"})
    if not architect_ai.get("endpoint") or not architect_ai.get("model") or not architect_ai.get("api_key"):
        return _resp(400, {"error": "Missing architect_ai config"})

    all_services = set()
    for g in resource_groups:
        for s in g.get("services", []):
            if isinstance(s, str):
                all_services.add(s.strip())
    services_str = ", ".join(sorted(all_services)) if all_services else "無"

    system_prompt = (
        "你是一位 AWS 雲端架構師。請根據使用者需求與可用服務清單，輸出**嚴格的 JSON 物件**（不要任何 markdown 標記）。\n"
        "JSON 必須包含以下欄位：\n"
        '- "architecture": 字串，架構的簡要文字描述。\n'
        '- "resources": 陣列，每個元素必須包含：\n'
        '    - "logical_id": CloudFormation 邏輯 ID（如 "MyBucket"）\n'
        '    - "type": CloudFormation 資源類型（如 "AWS::S3::Bucket"）\n'
        '    - "description": 該資源的簡短說明\n'
        '    - "needs_code": 布林值，是否需要額外上傳程式碼（如 S3 網頁、Lambda 函式碼）\n'
        '    - "code_files": 陣列，如果 needs_code 為 true，則**必須列出所有需要的檔案名稱與簡述**（例如 [{"filename": "index.html", "description": "主頁"}]）；若 false 則可為空陣列 []。\n'
        "你**只能**使用可用服務清單中的服務。若需求無法完全滿足，請在 architecture 中明確指出缺失的服務。\n"
        "對於任何需要公開訪問的 S3 網站，請使用 BucketPolicy 而非 ACL 來授權。"
    )
    user_prompt = f"可用服務：{services_str}\n需求：{description}"

    try:
        raw = call_ai(
            endpoint=architect_ai["endpoint"],
            api_key=architect_ai["api_key"],
            model=architect_ai["model"],
            system=system_prompt,
            user=user_prompt
        )
        try:
            result = json.loads(raw)
            if not isinstance(result, dict) or "architecture" not in result or "resources" not in result:
                raise ValueError("Missing fields")
            return _resp(200, result)
        except (json.JSONDecodeError, ValueError) as e:
            return _resp(200, {
                "architecture": raw,
                "resources": [],
                "warning": "AI 未輸出有效 JSON，已使用純文字，後續自動部署可能受影響。"
            })
    except Exception as e:
        return _resp(500, {"error": f"Architect AI 失敗: {str(e)}"})

# ==================== 基礎設施部署（含智能重試與S3修補） ====================
def handle_deploy_infra(body):
    resource_groups = body.get("resource_groups", [])
    deploy_ai = body.get("deploy_ai", {})
    description = body.get("description", "")
    architecture = body.get("architecture", "")
    resources = body.get("resources", [])

    if not resource_groups or not description:
        return _resp(400, {"error": "Missing resource_groups or description"})
    if not deploy_ai.get("endpoint") or not deploy_ai.get("model") or not deploy_ai.get("api_key"):
        return _resp(400, {"error": "Missing deploy_ai config"})

    results = []
    for group in resource_groups:
        try:
            services_raw = group.get("services", [])
            if isinstance(services_raw, str):
                allowed_services = [s.strip() for s in services_raw.split(",") if s.strip()]
            else:
                allowed_services = [s.strip() for s in services_raw if s.strip()]

            res_desc = "\n".join([
                f"{r.get('logical_id','')} ({r.get('type','')}): {r.get('description','')}"
                for r in resources
            ]) if resources else "（無特定資源列表）"

            # 当前组的区域
            region = group.get("region", "us-east-1")

            # 原始用户提示（重试时可能附加错误）
            original_user_prompt = (
                f"你需要為一個 AWS 帳號建立 CloudFormation 模板。\n"
                f"**嚴格只能使用以下服務**：{', '.join(allowed_services)}\n"
                f"部署區域：{region}\n"
                f"需求描述：{description}\n"
                f"架構設計建議：\n{architecture}\n"
                f"設計中應包含的資源邏輯 ID 與類型（必須使用這些 Logical ID，且類型必須匹配）：\n{res_desc}\n"
                "請輸出一個純 JSON CloudFormation 模板（無 Markdown 代碼塊，無解釋）。\n"
                "模板中**不要包含任何程式碼內容**（Lambda 的 Code 屬性留空，S3 不需要上傳物件）。\n"
                "重要：所有 S3 存儲桶不得設定 AccessControl 或 BucketAcl，必須改用 BucketPolicy。\n"
                f"**絕對禁止**在模板中創建任何未在以下服務清單中列出的資源類型：{', '.join(allowed_services)}。如果需要數據庫，必須用 S3 代替 DynamoDB。\n"
                "所有 S3 桶的 Properties 中，必須包含以下 PublicAccessBlockConfiguration 設定以確保後續 BucketPolicy 能正常創建：\n"
                "{\n"
                '  "BlockPublicAcls": false,\n'
                '  "BlockPublicPolicy": false,\n'
                '  "IgnorePublicAcls": false,\n'
                '  "RestrictPublicBuckets": false\n'
                "}\n"
                f"**注意**：在定義 Outputs 時，WebsiteURL 必須使用正確的 S3 網站端點格式，例如：http://your-bucket.s3-website-{region}.amazonaws.com。"
            )

            attempt = 0
            max_attempts = 2
            last_error = None
            success = False

            while attempt < max_attempts and not success:
                attempt += 1
                try:
                    # 生成模板（第一次正常，第二次附带错误）
                    if attempt == 1:
                        user_prompt = original_user_prompt
                    else:
                        user_prompt = (
                            f"之前的部署失敗，錯誤原因如下：\n{last_error}\n"
                            f"請根據此錯誤修正 CloudFormation 模板，然後輸出新的純 JSON 模板。\n"
                            + original_user_prompt
                        )

                    template_str = call_ai(
                        endpoint=deploy_ai["endpoint"],
                        api_key=deploy_ai["api_key"],
                        model=deploy_ai["model"],
                        system="你是 AWS CloudFormation 專家，只輸出符合服務限制的 JSON 模板。若部署失敗，請根據錯誤訊息修正。",
                        user=user_prompt
                    )

                    template_json = json.loads(template_str)
                    resources_in_tpl = template_json.get("Resources", {})
                    invalid_types = []
                    for rname, rdef in resources_in_tpl.items():
                        rtype = rdef.get("Type", "")
                        if rtype.startswith("AWS::"):
                            svc = rtype.split("::")[1]
                            if svc not in allowed_services:
                                invalid_types.append(f"{rname} ({rtype})")
                    if invalid_types:
                        results.append({
                            "group": group.get("name", "unknown"),
                            "error": f"AI 生成的模板包含未授權的服務：{', '.join(invalid_types)}",
                            "error_code": "FORBIDDEN_SERVICE"
                        })
                        break

                    # ----- 自动修补模板（保证可靠性）-----
                    # 1. 修补所有 S3 桶，并建立桶与策略的依赖关系
                    bucket_to_policy = {}
                    for rname, rdef in resources_in_tpl.items():
                        if rdef.get("Type") == "AWS::S3::BucketPolicy":
                            bucket_ref = rdef.get("Properties", {}).get("Bucket", {}).get("Ref")
                            if bucket_ref:
                                bucket_to_policy[bucket_ref] = rname

                    for rname, rdef in resources_in_tpl.items():
                        if rdef.get("Type") == "AWS::S3::Bucket":
                            props = rdef.setdefault("Properties", {})
                            # 移除可能引起冲突的属性
                            props.pop("AccessControl", None)
                            props.pop("BucketAcl", None)
                            # 强制设置公开访问阻止全部为 false，确保后续 BucketPolicy 成功
                            props["PublicAccessBlockConfiguration"] = {
                                "BlockPublicAcls": False,
                                "IgnorePublicAcls": False,
                                "BlockPublicPolicy": False,
                                "RestrictPublicBuckets": False
                            }
                            # 让对应的 BucketPolicy 显式依赖此桶
                            if rname in bucket_to_policy:
                                policy = resources_in_tpl[bucket_to_policy[rname]]
                                depends_on = policy.setdefault("DependsOn", [])
                                if isinstance(depends_on, str):
                                    depends_on = [depends_on]
                                if rname not in depends_on:
                                    depends_on.append(rname)
                                policy["DependsOn"] = depends_on

                        # 2. 修补所有 IAM 角色，为 Lambda 执行角色附加 S3 完全权限
                        if rdef.get("Type") == "AWS::IAM::Role":
                            props = rdef.setdefault("Properties", {})
                            managed_policies = props.setdefault("ManagedPolicyArns", [])
                            s3_policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
                            if s3_policy_arn not in managed_policies:
                                managed_policies.append(s3_policy_arn)
                            props["ManagedPolicyArns"] = managed_policies

                    # 重新序列化修补后的模板
                    template_str = json.dumps(template_json)
                    # --------------------------------------

                    # 建立堆叠
                    session = boto3.Session(
                        aws_access_key_id=group.get("aws_access_key"),
                        aws_secret_access_key=group.get("aws_secret_key"),
                        region_name=region
                    )
                    cf = session.client("cloudformation")
                    stack_name = f"ai-deploy-{int(time.time())}"
                    cf.create_stack(
                        StackName=stack_name,
                        TemplateBody=template_str,
                        Capabilities=["CAPABILITY_NAMED_IAM", "CAPABILITY_AUTO_EXPAND"]
                    )

                    # 等待堆叠创建完成
                    waiter = cf.get_waiter('stack_create_complete')
                    waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 30})

                    # 成功，获取输出
                    stack_info = cf.describe_stacks(StackName=stack_name)['Stacks'][0]
                    outputs = {o['OutputKey']: o.get('OutputValue', '') for o in stack_info.get('Outputs', [])}
                    resource_map = {}
                    paginator = cf.get_paginator('list_stack_resources')
                    for page in paginator.paginate(StackName=stack_name):
                        for res in page['StackResourceSummaries']:
                            resource_map[res['LogicalResourceId']] = res.get('PhysicalResourceId', '')

                    results.append({
                        "group": group.get("name", "unknown"),
                        "stack_name": stack_name,
                        "status": "CREATE_COMPLETE",
                        "outputs": outputs,
                        "resource_mapping": resource_map,
                        "console_url": f"https://{region}.console.aws.amazon.com/cloudformation/home?region={region}#/stacks/stackinfo?stackId={stack_name}",
                        "region": region
                    })
                    success = True

                except Exception as e:
                    last_error = str(e)
                    # 如果是等待超时，尝试获取失败原因
                    if "Waiter" in str(type(e).__name__):
                        try:
                            stack_info = cf.describe_stacks(StackName=stack_name)['Stacks'][0]
                            status = stack_info.get('StackStatus', 'UNKNOWN')
                            if 'FAILED' in status or 'ROLLBACK' in status:
                                events = cf.describe_stack_events(StackName=stack_name).get('StackEvents', [])
                                fail_reasons = []
                                for event in events:
                                    if 'FAILED' in event.get('ResourceStatus', '') and event.get('ResourceStatusReason'):
                                        fail_reasons.append(event['ResourceStatusReason'])
                                last_error = "; ".join(fail_reasons) if fail_reasons else last_error
                            else:
                                results.append({
                                    "group": group.get("name", "unknown"),
                                    "stack_name": stack_name,
                                    "status": status,
                                    "error": "堆棧創建超時，請手動檢查 CloudFormation",
                                    "console_url": f"https://{region}.console.aws.amazon.com/cloudformation/home?region={region}#/stacks/stackinfo?stackId={stack_name}"
                                })
                                success = True
                                continue
                        except:
                            pass

                    # 判断是否为权限问题（直接结束，不重试）
                    if any(keyword in last_error.lower() for keyword in [
                        "access denied", "not authorized", "unauthorized",
                        "permission", "forbidden", "lack of permission",
                        "no identity-based policy", "insufficient"
                    ]):
                        results.append({
                            "group": group.get("name", "unknown"),
                            "error": f"權限不足，無法部署：{last_error}",
                            "error_code": "ACCESS_DENIED"
                        })
                        success = True

                    # 如果不是权限问题且还有重试次数，则继续循环
                    if not success and attempt >= max_attempts:
                        results.append({
                            "group": group.get("name", "unknown"),
                            "error": f"部署失敗 (已重試 {attempt} 次)：{last_error}",
                            "error_code": "DEPLOY_FAILED"
                        })
                        success = True

        except Exception as e:
            results.append({
                "group": group.get("name", "unknown"),
                "error": f"基礎設施部署流程異常: {str(e)}",
                "error_code": "DEPLOY_FAILED"
            })

    return _resp(200, {"results": results})
# ==================== 程式碼上傳（含驗證與重試） ====================
def handle_upload_code(body):
    resource_groups = body.get("resource_groups", [])
    code_ai = body.get("code_ai", {})
    architecture = body.get("architecture", "")
    resources = body.get("resources", [])
    resource_mapping = body.get("resource_mapping", {})
    description = body.get("description", "")

    if not code_ai.get("endpoint") or not code_ai.get("model") or not code_ai.get("api_key"):
        return _resp(400, {"error": "Missing code_ai config"})

    # 找出需要程式碼的資源
    code_resources = [r for r in resources if r.get("needs_code", False)]
    if not code_resources:
        return _resp(200, {"results": [], "message": "沒有需要上傳的程式碼資源。"})

    # 建立資源描述和映射文字
    resources_desc = "\n".join([
        f"{r['logical_id']} ({r['type']}): 需要文件 {', '.join([f['filename'] for f in r.get('code_files', [])])}"
        for r in code_resources
    ])
    mapping_desc = "\n".join([f"{k} -> {v}" for k, v in resource_mapping.items()])

    system_prompt = (
        "你是一位程式碼生成專家。根據使用者提供的架構描述與資源需求，生成對應的程式碼檔案。\n"
        "輸出必須為嚴格的 JSON 物件（不要 markdown）：\n"
        "{\n"
        '  "s3": { "<物理桶名>": { "<檔案名稱>": "<檔案內容>" } },\n'
        '  "lambda": { "<函數名>": { "<檔案名稱>": "<檔案內容>" } }\n'
        "}\n"
        "注意：對於 S3 桶，物理桶名已在資源映射中提供；對於 Lambda，請提供函數的實體名稱（也是物理 ID）。\n"
        "程式碼內容應根據需求完整且可運行。如果無法生成某個檔案，請將其值設為空字串 \"\"，不要省略。"
    )

    results = []
    for group in resource_groups:
        session = boto3.Session(
            aws_access_key_id=group.get("aws_access_key"),
            aws_secret_access_key=group.get("aws_secret_key"),
            region_name=group.get("region", "us-east-1")
        )
        s3_client = session.client("s3")
        lambda_client = session.client("lambda")

        max_attempts = 2
        attempt = 0
        all_upload_success = False
        upload_errors = []

        while attempt < max_attempts and not all_upload_success:
            attempt += 1
            upload_errors = []
            if attempt == 1:
                user_prompt = (
                    f"架構描述：{architecture}\n"
                    f"原始需求：{description}\n"
                    f"需要程式碼的資源：\n{resources_desc}\n"
                    f"資源映射（邏輯ID → 物理ID）：\n{mapping_desc}\n"
                    "請生成所有要求的程式碼檔案。"
                )
            else:
                # 重試時附上缺失信息
                missing_info = "\n".join(upload_errors)
                user_prompt = (
                    f"上一次程式碼上傳後，發現以下文件缺失或上傳失敗：\n{missing_info}\n"
                    f"請重新生成這些缺失的文件，再次輸出完整的 JSON。\n"
                    f"原始需求：{description}\n"
                    f"架構描述：{architecture}\n"
                    f"資源映射：\n{mapping_desc}\n"
                )

            # 調用 AI 生成代碼
            try:
                raw = call_ai(
                    endpoint=code_ai["endpoint"],
                    api_key=code_ai["api_key"],
                    model=code_ai["model"],
                    system=system_prompt,
                    user=user_prompt
                )
                code_data = json.loads(raw)
            except Exception as e:
                # AI 調用失敗不重試，直接記錄錯誤
                err_msg = str(e).encode("ascii", errors="replace").decode("ascii")
                results.append({
                    "group": group.get("name", "unknown"),
                    "error": f"程式碼 AI 調用失敗: {err_msg}",
                    "error_code": "CODE_AI_FAILED"
                })
                break

            # 上傳 S3 文件
            s3_files = code_data.get("s3", {})
            for bucket_name, files in s3_files.items():
                for filename, content in files.items():
                    if not content:
                        content = f"<!-- Placeholder for {filename} -->"
                    content_type = "text/html" if filename.endswith(".html") else "text/plain"
                    try:
                        s3_client.put_object(
                            Bucket=bucket_name,
                            Key=filename,
                            Body=content,
                            ContentType=content_type
                        )
                    except Exception as e:
                        upload_errors.append(f"S3 上傳失敗 {bucket_name}/{filename}: {str(e)}")

            # 上傳 Lambda 代碼（打包成 zip）
            lambda_files = code_data.get("lambda", {})
            for func_name, files in lambda_files.items():
                if not files:
                    continue
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for fname, fcontent in files.items():
                        if not fcontent:
                            fcontent = "# Placeholder code"
                        zf.writestr(fname, fcontent)
                zip_buffer.seek(0)
                try:
                    lambda_client.update_function_code(
                        FunctionName=func_name,
                        ZipFile=zip_buffer.read()
                    )
                except Exception as e:
                    upload_errors.append(f"Lambda 更新失敗 {func_name}: {str(e)}")

            # 驗證上傳結果（檢查 S3 文件是否存在）
            missing_files = []
            for resource in code_resources:
                logical_id = resource["logical_id"]
                phy_id = resource_mapping.get(logical_id)
                if not phy_id:
                    continue
                if resource["type"].startswith("AWS::S3::Bucket"):
                    for file_info in resource.get("code_files", []):
                        filename = file_info["filename"]
                        try:
                            s3_client.head_object(Bucket=phy_id, Key=filename)
                        except Exception:
                            missing_files.append(f"S3 桶 {phy_id} 中缺失文件 {filename}")
            if missing_files:
                upload_errors += missing_files

            # 如果沒有錯誤，則成功
            if not upload_errors:
                all_upload_success = True

        # 輸出最終結果
        if all_upload_success:
            results.append({
                "group": group.get("name", "unknown"),
                "status": "CODE_UPLOADED",
                "resource_mapping": resource_mapping,
                "message": "所有程式碼上傳完成"
            })
        else:
            # 如果前面已經因 AI 失敗直接記錄，這裡不再重複
            if not results:  # 避免重複添加錯誤
                error_summary = "; ".join(upload_errors) if upload_errors else "未知錯誤"
                results.append({
                    "group": group.get("name", "unknown"),
                    "error": f"程式碼上傳未完全成功 (已嘗試 {attempt} 次): {error_summary}",
                    "error_code": "CODE_UPLOAD_FAILED",
                    "resource_mapping": resource_mapping
                })

    return _resp(200, {"results": results})

# ==================== AI 呼叫輔助（修正編碼） ====================
def call_ai(endpoint, api_key, model, system, user):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.2
    }).encode("utf-8")

    req = urllib.request.Request(endpoint, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    })

    try:
        print(f"Calling AI: {endpoint} with model {model}")
        socket.setdefaulttimeout(60)
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            # 自動判斷編碼
            content_type = resp.headers.get('Content-Type', '')
            encoding = 'utf-8'
            if 'charset=' in content_type:
                encoding = content_type.split('charset=')[-1].strip()
            data = json.loads(raw.decode(encoding, errors='ignore'))
            content = data["choices"][0]["message"]["content"]
            if content.startswith("```"):
                lines = content.splitlines()
                if lines[-1].strip() == "```":
                    content = "\n".join(lines[1:-1])
                else:
                    content = "\n".join(lines[1:])
            return content.strip()
    except urllib.error.HTTPError as e:
        body = ''
        if e.fp:
            body = e.read().decode("utf-8", errors="ignore")
        raise Exception(f"AI API HTTP {e.code}: {e.reason} - {body}")
    except Exception as e:
        err_msg = str(e).encode("ascii", errors="replace").decode("ascii")
        raise Exception(f"AI 呼叫失敗: {err_msg}")

# ==================== 回應輔助 ====================
def _resp(code, body):
    return {
        "statusCode": code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
            "Access-Control-Allow-Headers": "Content-Type",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }