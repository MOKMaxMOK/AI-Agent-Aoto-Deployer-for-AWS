"""本地运行需要 Python 3.7+，先安装依赖：pip install flask boto3。

启动服务：python local_server.py，默认监听 http://localhost:5000。

修改前端 script.js 中的 LAMBDA_URL 为 http://localhost:5000/（保留结尾斜杠）。

本地版不会自动配置 AWS 凭证，请通过前端输入框提供有效的 DevUser 密钥（仍需对应服务完整权限）。

S3 账户级公开访问阻止仍须关闭，否则部署会失败。

调试时修改代码会自动重启（debug=True），生产环境请设为 False。"""

from flask import Flask, request, jsonify
import json
import urllib.request
import urllib.error
import boto3
import time
import socket
import io
import zipfile

app = Flask(__name__)

# ---------- 原 lambda_handler 的邏輯，改成 Flask route ----------
@app.route('/', methods=['POST', 'OPTIONS'])
def handle_request():
    if request.method == 'OPTIONS':
        return _resp(200, {})

    try:
        body = request.get_json(force=True)
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

# ---------- 以下三個處理函數保持與 Lambda 版完全一致 ----------
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


def handle_deploy_infra(body):
    # 完整代碼與 Lambda 版相同，此處為節省空間僅保留結構，實際貼上完整函數
    # 請將你現有的 Lambda 版 `handle_deploy_infra` 函數完整複製到這裡
    pass

def handle_upload_code(body):
    # 同樣，請將 Lambda 版 `handle_upload_code` 完整貼上
    pass

# ---------- 輔助函數：call_ai ----------
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

# ---------- 回應輔助 ----------
def _resp(code, body):
    response = jsonify(body)
    response.status_code = code
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "OPTIONS,POST"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

# ---------- 啟動服務 ----------
if __name__ == '__main__':
    print("Local AI Deploy Server running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)