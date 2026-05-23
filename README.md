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
<img width="865" height="695" alt="image" src="https://github.com/user-attachments/assets/66cfc81a-9f67-4617-b941-823943302d5f" />


### 🧠 AI 設定
你需要為三個 AI 角色分別設定 API 端點、模型名稱與 API Key：
- **架構生成 AI**：負責理解需求、規劃架構
- **基礎設施部署 AI**：負責產生 CloudFormation 模板
- **程式碼生成 AI**：負責產生網站前端、後端程式碼
<img width="865" height="800" alt="image" src="https://github.com/user-attachments/assets/70eae1e1-7591-438f-a7e3-80e46b7cc6e2" />
另有一個 **助手 AI**（懸浮球），可隨時提問雲端架構相關問題。


### 🚀 部署流程
1. **選擇資源組**：勾選你要部署到的 AWS 帳號
<img width="865" height="447" alt="image" src="https://github.com/user-attachments/assets/fe398af6-2064-4eb0-8e0d-39059967bcaa" />


2. **輸入需求描述**：用自然語言寫下你想部署什麼（例如「部署一個計時器網站」）
<img width="865" height="698" alt="image" src="https://github.com/user-attachments/assets/bbf03c20-82bc-4c95-9080-e9559c425d59" />
3. **開始架構分析**：AI 會先分析你的需求並顯示架構計畫
<img width="865" height="698" alt="image" src="https://github.com/user-attachments/assets/330cb7bd-b285-4d20-8d0c-8c2e53a2c775" />
4. **確認架構**：你可以直接確認，或輸入修改意見
<img width="865" height="516" alt="image" src="https://github.com/user-attachments/assets/0e8b8094-a940-417a-af9d-0ac299f3f00a" />

5. **點擊部署**：系統會依序建立基礎設施、生成並上傳程式碼

<img width="865" height="665" alt="image" src="https://github.com/user-attachments/assets/1946b9bf-d446-4d78-aa50-941da6bb61f8" />

6. **等待結果**：部署完成後，你會看到網站 URL、API 端點、資源清單及 CloudFormation 連結
<img width="865" height="747" alt="image" src="https://github.com/user-attachments/assets/75a12bc2-d5c6-4876-a71f-46dbfe018d92" />

所有步驟都有進度條顯示，失敗時會顯示人類可讀的錯誤原因。

</details>

<details>
<summary><b>🇨🇳 简体中文</b></summary>

## 简介
**Prompt-to-Cloud** 是一个全自动的 AI 云端部署实验平台。你只需要用自然语言描述你想部署的应用，AI 就会依次完成架构设计、CloudFormation 模板生成、基础设施部署、代码生成与上传，最终给你一个可以直接访问的网站或 API。

## 原理
整个平台由三个 AI 角色协作完成部署：
1. **架构生成 AI**：分析你的需求，决定需要哪些云端资源，并输出架构图（文字描述）与资源清单。
2. **基础设施部署 AI**：根据架构计划生成符合 AWS 规范的 CloudFormation 模板，并在你的 AWS 账号中创建资源。
3. **代码生成 AI**：针对需要代码的资源（如 S3 静态网页、Lambda 函数），自动生成并上传代码。

平台不会存储你的 AWS 密钥，所有操作都使用你当次输入的凭据，安全且隔离。

## 界面介绍

### 📦 资源组
资源组是一组 AWS 账号的设定组合，包含：
- AWS 访问密钥（Access Key / Secret Key）
- 区域（Region）
- 可用的 AWS 服务清单（例如 EC2、S3、Lambda）
你可以创建多个资源组，部署时勾选要使用的组别，AI 就会在对应的账号中创建资源。
<img width="865" height="695" alt="image" src="https://github.com/user-attachments/assets/8c5708d0-9608-4691-9be8-dbeb9420ac6d" />



### 🧠 AI 设置
你需要为三个 AI 角色分别设置 API 端点、模型名称与 API Key：
- **架构生成 AI**：负责理解需求、规划架构
- **基础设施部署 AI**：负责生成 CloudFormation 模板
- **代码生成 AI**：负责生成网站前端、后端代码
<img width="865" height="800" alt="image" src="https://github.com/user-attachments/assets/639495bb-29a5-43cb-927a-c073047f69c9" />

另有一个 **助手 AI**（悬浮球），可随时提问云端架构相关问题。

### 🚀 部署流程
1. **选择资源组**：勾选你要部署到的 AWS 账号
<img width="865" height="447" alt="image" src="https://github.com/user-attachments/assets/66fd95ac-610b-40f2-bba7-72ba178cb66f" />

2. **输入需求描述**：用自然语言写下你想部署什么（例如“部署一个计时器网站”）
<img width="865" height="698" alt="image" src="https://github.com/user-attachments/assets/5c4d4377-6ddf-4caa-85dc-570570b2f81a" />

3. **开始架构分析**：AI 会先分析你的需求并显示架构计划
<img width="865" height="516" alt="image" src="https://github.com/user-attachments/assets/43fbd63f-ffa1-44cb-a6a3-cabec63df588" />

4. **确认架构**：你可以直接确认，或输入修改意见
5. **点击部署**：系统会依次创建基础设施、生成并上传代码
<img width="865" height="665" alt="image" src="https://github.com/user-attachments/assets/cba17903-9a85-4988-9469-d9b43d58a724" />

6. **等待结果**：部署完成后，你会看到网站 URL、API 端点、资源清单及 CloudFormation 链接
<img width="865" height="747" alt="image" src="https://github.com/user-attachments/assets/e6d22628-deb1-4756-a67f-2bcc4647a5b6" />

所有步骤都有进度条显示，失败时会显示人类可读的错误原因。

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
<img width="865" height="695" alt="image" src="https://github.com/user-attachments/assets/5547f472-771f-4370-ae2e-176defebb5f3" />

You can create multiple resource groups and select which ones to use for a deployment.

### 🧠 AI Configuration
You supply an API endpoint, model name, and API key for each AI role:
- **Architecture AI** – Understands requirements and plans infrastructure
- **Infrastructure Deployment AI** – Generates CloudFormation templates
- **Code Generation AI** – Creates frontend and backend code
<img width="865" height="800" alt="image" src="https://github.com/user-attachments/assets/f3020d65-f507-4f4b-8f27-de4cbed0b1bf" />

A floating **Assistant AI** widget is also available for ad‑hoc cloud architecture questions.

### 🚀 Deployment Flow
1. **Select resource groups** – Choose which AWS accounts to deploy to
<img width="865" height="447" alt="image" src="https://github.com/user-attachments/assets/91642418-de1b-462e-8ef4-25ec90467aa7" />

2. **Write a description** – Describe what you want in plain language
3. **Run architecture analysis** – The AI proposes an architecture plan
<img width="865" height="698" alt="image" src="https://github.com/user-attachments/assets/526e4bd4-127a-482b-a0a6-a6e1d69cab83" />

4. **Confirm or refine** – Accept the plan or provide modification requests
5. **Deploy** – Infrastructure is provisioned, code is generated and uploaded automatically
<img width="865" height="516" alt="image" src="https://github.com/user-attachments/assets/2e6916ab-2b08-4d0c-9547-af8d56625a38" />
<img width="865" height="665" alt="image" src="https://github.com/user-attachments/assets/6b770fc5-1292-4963-bf12-72604a2056cf" />


6. **Get results** – View the website URL, API endpoint, resource list, and a link to the CloudFormation stack
<img width="865" height="747" alt="image" src="https://github.com/user-attachments/assets/563dc2c5-69e2-4cb7-9ddf-6aa965157103" />

A progress bar keeps you informed at every stage, and any failures are explained in clear, human-readable messages.

</details>
