"""Requires Python 3.7+, install dependencies: pip install flask boto3.

Start the server: python local_server.py, listening at http://localhost:5000.

Change the LAMBDA_URL in the frontend script.js to http://localhost:5000/ (keep the trailing slash).

AWS credentials are not stored locally; provide a valid DevUser Access Key / Secret Key via the frontend. The user must have full permissions for the required services (CloudFormation, S3, Lambda, API Gateway, IAM).

Account-level S3 Block Public Access must still be disabled, otherwise deployments will fail.

The server runs with debug=True for auto‑reload during development; set to False for production use."""

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
        "You are an AWS cloud architect. Based on the user's request and available services, output a **strict JSON object** (no markdown).\n"
        "The JSON must contain:\n"
        '- "architecture": string, a brief textual description of the architecture.\n'
        '- "resources": array, each element must contain:\n'
        '    - "logical_id": CloudFormation logical ID (e.g., "MyBucket")\n'
        '    - "type": CloudFormation resource type (e.g., "AWS::S3::Bucket")\n'
        '    - "description": short description of the resource\n'
        '    - "needs_code": boolean, whether additional code upload is required\n'
        '    - "code_files": array, if needs_code is true, list all required filenames and descriptions (e.g., [{"filename": "index.html", "description": "main page"}]); otherwise empty array []\n'
        "You **must** use only the services from the available list. If the request cannot be fully satisfied, clearly indicate the missing services in the architecture description.\n"
        "For any S3 bucket requiring public access, use BucketPolicy instead of ACL."
    )
    user_prompt = f"Available services: {services_str}\nRequest: {description}"

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
                "warning": "AI did not output valid JSON. Plain text used, subsequent automatic deployment may be affected."
            })
    except Exception as e:
        return _resp(500, {"error": f"Architect AI failed: {str(e)}"})

# ⚠️ Insert your complete handle_deploy_infra and handle_upload_code with English prompts here.
# They should be exactly the same logic as the Lambda version, only with English strings.
def handle_deploy_infra(body):
    # ... paste your full English version of handle_deploy_infra ...
    pass

def handle_upload_code(body):
    # ... paste your full English version of handle_upload_code ...
    pass

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
        raise Exception(f"AI call failed: {err_msg}")

def _resp(code, body):
    response = jsonify(body)
    response.status_code = code
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "OPTIONS,POST"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

if __name__ == '__main__':
    print("Local AI Deploy Server (EN) running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)