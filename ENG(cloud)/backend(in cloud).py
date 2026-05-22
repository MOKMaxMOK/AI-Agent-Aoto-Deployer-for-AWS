""""Deploy the code to AWS Lambda with runtime Python 3.12, timeout at least 300 seconds, memory 128 MB.

Create a Function URL for the Lambda with AuthType set to NONE and ensure the resource policy allows public invocation.

The AWS credentials (DevUser) used in the frontend must have full access to CloudFormation, S3, Lambda, API Gateway, and IAM (e.g., policies AWSCloudFormationFullAccess, AmazonS3FullAccess, AWSLambda_FullAccess, AmazonAPIGatewayAdministrator, IAMFullAccess).

Account-level S3 Block Public Access must be turned off (all four switches set to false), otherwise public bucket policies will be denied.

If s3:PutBucketPolicy fails, verify the account-level setting and check that the bucket-level PublicAccessBlockConfiguration has been auto‑patched by the backend.

CORS preflight (OPTIONS) is handled in code; if you see CORS errors on first use, refresh the page and ensure the Function URL is correctly configured."""

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

# ==================== Architecture Generation ====================
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
    services_str = ", ".join(sorted(all_services)) if all_services else "None"

    system_prompt = (
        "You are an AWS cloud architect. Based on user requirements and the list of available services, output a **strict JSON object** (no markdown formatting).\n"
        "The JSON must contain the following fields:\n"
        '- "architecture": string, a brief textual description of the architecture.\n'
        '- "resources": array, where each element must contain:\n'
        '    - "logical_id": CloudFormation logical ID (e.g., "MyBucket")\n'
        '    - "type": CloudFormation resource type (e.g., "AWS::S3::Bucket")\n'
        '    - "description": short description of the resource\n'
        '    - "needs_code": boolean, whether additional code upload is required (e.g., S3 website, Lambda function code)\n'
        '    - "code_files": array, if needs_code is true, **you must list all required filenames with brief descriptions** (e.g., [{"filename": "index.html", "description": "Main page"}]); if false, this can be an empty array [].\n'
        "You may **only** use services from the available services list. If requirements cannot be fully met, explicitly state the missing services in the architecture field.\n"
        "For any S3 website requiring public access, use BucketPolicy instead of ACL for authorization."
    )
    user_prompt = f"Available services: {services_str}\nRequirements: {description}"

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
                "warning": "AI did not output valid JSON; plain text was used instead. Automatic deployment in subsequent steps may be affected."
            })
    except Exception as e:
        return _resp(500, {"error": f"Architect AI failed: {str(e)}"})

# ==================== Infrastructure Deployment (with smart retry & S3 patching) ====================
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
            ]) if resources else "(No specific resource list)"

            # Region for current group
            region = group.get("region", "us-east-1")

            # Original user prompt (errors may be appended during retry)
            original_user_prompt = (
                f"You need to create a CloudFormation template for an AWS account.\n"
                f"**Strictly use only the following services**: {', '.join(allowed_services)}\n"
                f"Deployment region: {region}\n"
                f"Requirement description: {description}\n"
                f"Architecture design suggestions:\n{architecture}\n"
                f"Resource logical IDs and types that must be included in the design (you must use these Logical IDs and match the types):\n{res_desc}\n"
                "Please output a pure JSON CloudFormation template (no Markdown code blocks, no explanations).\n"
                "The template must **not contain any code content** (leave Lambda Code properties empty; S3 does not need object uploads).\n"
                "Important: All S3 buckets must not set AccessControl or BucketAcl; use BucketPolicy instead.\n"
                f"**Absolutely forbidden** to create any resource types in the template that are not listed in the following service list: {', '.join(allowed_services)}. If a database is needed, use S3 instead of DynamoDB.\n"
                "For all S3 buckets in Properties, you must include the following PublicAccessBlockConfiguration settings to ensure subsequent BucketPolicy creation succeeds:\n"
                "{\n"
                '  "BlockPublicAcls": false,\n'
                '  "BlockPublicPolicy": false,\n'
                '  "IgnorePublicAcls": false,\n'
                '  "RestrictPublicBuckets": false\n'
                "}\n"
                f"**Note**: When defining Outputs, WebsiteURL must use the correct S3 website endpoint format, e.g., http://your-bucket.s3-website-{region}.amazonaws.com."
            )

            attempt = 0
            max_attempts = 2
            last_error = None
            success = False

            while attempt < max_attempts and not success:
                attempt += 1
                try:
                    # Generate template (first attempt normal, second with error context)
                    if attempt == 1:
                        user_prompt = original_user_prompt
                    else:
                        user_prompt = (
                            f"Previous deployment failed. Error reason:\n{last_error}\n"
                            f"Please correct the CloudFormation template based on this error and output a new pure JSON template.\n"
                            + original_user_prompt
                        )

                    template_str = call_ai(
                        endpoint=deploy_ai["endpoint"],
                        api_key=deploy_ai["api_key"],
                        model=deploy_ai["model"],
                        system="You are an AWS CloudFormation expert. Output only JSON templates that comply with service restrictions. If deployment fails, correct based on error messages.",
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
                            "error": f"AI-generated template contains unauthorized services: {', '.join(invalid_types)}",
                            "error_code": "FORBIDDEN_SERVICE"
                        })
                        break

                    # ----- Auto-patch template (for reliability) -----
                    # 1. Patch all S3 buckets and establish dependency between bucket and policy
                    bucket_to_policy = {}
                    for rname, rdef in resources_in_tpl.items():
                        if rdef.get("Type") == "AWS::S3::BucketPolicy":
                            bucket_ref = rdef.get("Properties", {}).get("Bucket", {}).get("Ref")
                            if bucket_ref:
                                bucket_to_policy[bucket_ref] = rname

                    for rname, rdef in resources_in_tpl.items():
                        if rdef.get("Type") == "AWS::S3::Bucket":
                            props = rdef.setdefault("Properties", {})
                            # Remove potentially conflicting properties
                            props.pop("AccessControl", None)
                            props.pop("BucketAcl", None)
                            # Force public access block settings to false to ensure subsequent BucketPolicy succeeds
                            props["PublicAccessBlockConfiguration"] = {
                                "BlockPublicAcls": False,
                                "IgnorePublicAcls": False,
                                "BlockPublicPolicy": False,
                                "RestrictPublicBuckets": False
                            }
                            # Make corresponding BucketPolicy explicitly depend on this bucket
                            if rname in bucket_to_policy:
                                policy = resources_in_tpl[bucket_to_policy[rname]]
                                depends_on = policy.setdefault("DependsOn", [])
                                if isinstance(depends_on, str):
                                    depends_on = [depends_on]
                                if rname not in depends_on:
                                    depends_on.append(rname)
                                policy["DependsOn"] = depends_on

                        # 2. Patch all IAM roles: attach S3 full access policy to Lambda execution roles
                        if rdef.get("Type") == "AWS::IAM::Role":
                            props = rdef.setdefault("Properties", {})
                            managed_policies = props.setdefault("ManagedPolicyArns", [])
                            s3_policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
                            if s3_policy_arn not in managed_policies:
                                managed_policies.append(s3_policy_arn)
                            props["ManagedPolicyArns"] = managed_policies

                    # Re-serialize patched template
                    template_str = json.dumps(template_json)
                    # --------------------------------------

                    # Create stack
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

                    # Wait for stack creation to complete
                    waiter = cf.get_waiter('stack_create_complete')
                    waiter.wait(StackName=stack_name, WaiterConfig={'Delay': 10, 'MaxAttempts': 30})

                    # Success: get outputs
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
                    # If waiter timeout, try to get failure reason
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
                                    "error": "Stack creation timed out; please check CloudFormation manually",
                                    "console_url": f"https://{region}.console.aws.amazon.com/cloudformation/home?region={region}#/stacks/stackinfo?stackId={stack_name}"
                                })
                                success = True
                                continue
                        except:
                            pass

                    # Check if it's a permission issue (terminate immediately, no retry)
                    if any(keyword in last_error.lower() for keyword in [
                        "access denied", "not authorized", "unauthorized",
                        "permission", "forbidden", "lack of permission",
                        "no identity-based policy", "insufficient"
                    ]):
                        results.append({
                            "group": group.get("name", "unknown"),
                            "error": f"Insufficient permissions, cannot deploy: {last_error}",
                            "error_code": "ACCESS_DENIED"
                        })
                        success = True

                    # If not a permission issue and retries remain, continue loop
                    if not success and attempt >= max_attempts:
                        results.append({
                            "group": group.get("name", "unknown"),
                            "error": f"Deployment failed (retried {attempt} times): {last_error}",
                            "error_code": "DEPLOY_FAILED"
                        })
                        success = True

        except Exception as e:
            results.append({
                "group": group.get("name", "unknown"),
                "error": f"Infrastructure deployment process error: {str(e)}",
                "error_code": "DEPLOY_FAILED"
            })

    return _resp(200, {"results": results})

# ==================== Code Upload (with validation & retry) ====================
def handle_upload_code(body):
    resource_groups = body.get("resource_groups", [])
    code_ai = body.get("code_ai", {})
    architecture = body.get("architecture", "")
    resources = body.get("resources", [])
    resource_mapping = body.get("resource_mapping", {})
    description = body.get("description", "")

    if not code_ai.get("endpoint") or not code_ai.get("model") or not code_ai.get("api_key"):
        return _resp(400, {"error": "Missing code_ai config"})

    # Find resources that need code
    code_resources = [r for r in resources if r.get("needs_code", False)]
    if not code_resources:
        return _resp(200, {"results": [], "message": "No code upload required for any resources."})

    # Build resource description and mapping text
    resources_desc = "\n".join([
        f"{r['logical_id']} ({r['type']}): requires files {', '.join([f['filename'] for f in r.get('code_files', [])])}"
        for r in code_resources
    ])
    mapping_desc = "\n".join([f"{k} -> {v}" for k, v in resource_mapping.items()])

    system_prompt = (
        "You are a code generation expert. Based on the architecture description and resource requirements provided by the user, generate corresponding code files.\n"
        "Output must be a strict JSON object (no markdown):\n"
        "{\n"
        '  "s3": { "<physical_bucket_name>": { "<filename>": "<file_content>" } },\n'
        '  "lambda": { "<function_name>": { "<filename>": "<file_content>" } }\n'
        "}\n"
        "Note: For S3 buckets, the physical bucket name is provided in the resource mapping; for Lambda, provide the function's physical name (also the physical ID).\n"
        "Code content should be complete and runnable according to requirements. If a file cannot be generated, set its value to an empty string \"\"; do not omit it."
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
                    f"Architecture description: {architecture}\n"
                    f"Original requirements: {description}\n"
                    f"Resources requiring code:\n{resources_desc}\n"
                    f"Resource mapping (Logical ID → Physical ID):\n{mapping_desc}\n"
                    "Please generate all required code files."
                )
            else:
                # On retry, attach missing file info
                missing_info = "\n".join(upload_errors)
                user_prompt = (
                    f"After the previous code upload, the following files were missing or failed to upload:\n{missing_info}\n"
                    f"Please regenerate these missing files and output the complete JSON again.\n"
                    f"Original requirements: {description}\n"
                    f"Architecture description: {architecture}\n"
                    f"Resource mapping:\n{mapping_desc}\n"
                )

            # Call AI to generate code
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
                # AI call failure: do not retry, log error directly
                err_msg = str(e).encode("ascii", errors="replace").decode("ascii")
                results.append({
                    "group": group.get("name", "unknown"),
                    "error": f"Code AI call failed: {err_msg}",
                    "error_code": "CODE_AI_FAILED"
                })
                break

            # Upload S3 files
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
                        upload_errors.append(f"S3 upload failed {bucket_name}/{filename}: {str(e)}")

            # Upload Lambda code (packaged as zip)
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
                    upload_errors.append(f"Lambda update failed {func_name}: {str(e)}")

            # Verify upload results (check if S3 files exist)
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
                            missing_files.append(f"Missing file {filename} in S3 bucket {phy_id}")
            if missing_files:
                upload_errors += missing_files

            # If no errors, success
            if not upload_errors:
                all_upload_success = True

        # Output final result
        if all_upload_success:
            results.append({
                "group": group.get("name", "unknown"),
                "status": "CODE_UPLOADED",
                "resource_mapping": resource_mapping,
                "message": "All code files uploaded successfully"
            })
        else:
            # If AI failure was already logged earlier, avoid duplicate entries
            if not results:
                error_summary = "; ".join(upload_errors) if upload_errors else "Unknown error"
                results.append({
                    "group": group.get("name", "unknown"),
                    "error": f"Code upload not fully successful (attempted {attempt} times): {error_summary}",
                    "error_code": "CODE_UPLOAD_FAILED",
                    "resource_mapping": resource_mapping
                })

    return _resp(200, {"results": results})

# ==================== AI Call Helper (encoding fix) ====================
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
            # Auto-detect encoding
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
        raise Exception(f"AI call failed: {err_msg}")

# ==================== Response Helper ====================
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