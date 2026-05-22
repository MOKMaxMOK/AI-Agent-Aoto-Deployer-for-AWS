# Prompt-to-Cloud 🚀

<details>
<summary><b>🇹🇼 繁體中文</b></summary>

## 簡介
**Prompt-to-Cloud** 是一個全自動的 AI 雲端部署實驗平台。你只需要用自然語言描述你想部署的應用，AI 就會依序完成架構設計、CloudFormation 模板生成、基礎設施部署、程式碼生成與上傳，最終給你一個可以直接訪問的網站或 API。

## 原理
整個平台由三個 AI 角色協作完成部署：
1. **架構生成 AI**：分析你的需求，決定需要哪些雲端資源，並輸出架構圖（文字描述）與資源清單。
2. **基礎設施部署 AI**：根據架構計畫產生符合 AWS 規範的 CloudFormation 模板，並在你的 AWS 帳號中建立資源。
3. **程式碼生成 AI**：針對需要程式碼的資源（如 S3 靜態網頁、Lambda 函數），自動生成並上傳程式碼。

平台不會儲存你的 AWS 金鑰，所有操作都使用你當次輸入的憑證，安全且隔離。

## 介面介紹

### 📦 資源組
資源組是一組 AWS 帳號的設定組合，包含：
- AWS 存取金鑰（Access Key / Secret Key）
- 區域（Region）
- 可用的 AWS 服務清單（例如 EC2、S3、Lambda）

你可以建立多個資源組，部署時勾選要使用的組別，AI 就會在對應的帳號中建立資源。

### 🧠 AI 設定
你需要為三個 AI 角色分別設定 API 端點、模型名稱與 API Key：
- **架構生成 AI**：負責理解需求、規劃架構
- **基礎設施部署 AI**：負責產生 CloudFormation 模板
- **程式碼生成 AI**：負責產生網站前端、後端程式碼

另有一個 **助手 AI**（懸浮球），可隨時提問雲端架構相關問題。

### 🚀 部署流程
1. **選擇資源組**：勾選你要部署到的 AWS 帳號
2. **輸入需求描述**：用自然語言寫下你想部署什麼（例如「部署一個計時器網站」）
3. **開始架構分析**：AI 會先分析你的需求並顯示架構計畫
4. **確認架構**：你可以直接確認，或輸入修改意見
5. **點擊部署**：系統會依序建立基礎設施、生成並上傳程式碼
6. **等待結果**：部署完成後，你會看到網站 URL、API 端點、資源清單及 CloudFormation 連結

所有步驟都有進度條顯示，失敗時會顯示人類可讀的錯誤原因。

</details>

<details>
<summary><b>🇬🇧 English</b></summary>

## Introduction
**Prompt-to-Cloud** is a fully automated AI cloud deployment lab. Simply describe the application you want in natural language, and the AI will sequentially handle architecture design, CloudFormation template generation, infrastructure provisioning, code generation, and upload – delivering a live website or API ready to use.

## How It Works
Three AI roles collaborate throughout the deployment:
1. **Architecture AI** – Analyzes your request, determines required cloud resources, and outputs an architecture diagram (as text) with a resource list.
2. **Infrastructure Deployment AI** – Generates a valid CloudFormation template from the architecture plan and creates the resources in your AWS account.
3. **Code Generation AI** – Writes and uploads any necessary code (e.g., static website files for S3, Lambda functions).

Your AWS credentials are never stored; they are used only for the current session, ensuring security and isolation.

## UI Overview

### 📦 Resource Groups
A resource group bundles together:
- AWS access keys (Access Key / Secret Key)
- Region
- List of allowed AWS services (e.g., EC2, S3, Lambda)

You can create multiple resource groups and select which ones to use for a deployment.

### 🧠 AI Configuration
You supply an API endpoint, model name, and API key for each AI role:
- **Architecture AI** – Understands requirements and plans infrastructure
- **Infrastructure Deployment AI** – Generates CloudFormation templates
- **Code Generation AI** – Creates frontend and backend code

A floating **Assistant AI** widget is also available for ad‑hoc cloud architecture questions.

### 🚀 Deployment Flow
1. **Select resource groups** – Choose which AWS accounts to deploy to
2. **Write a description** – Describe what you want in plain language
3. **Run architecture analysis** – The AI proposes an architecture plan
4. **Confirm or refine** – Accept the plan or provide modification requests
5. **Deploy** – Infrastructure is provisioned, code is generated and uploaded automatically
6. **Get results** – View the website URL, API endpoint, resource list, and a link to the CloudFormation stack

A progress bar keeps you informed at every stage, and any failures are explained in clear, human-readable messages.

</details>
