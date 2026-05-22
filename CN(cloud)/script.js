// ========== 全域狀態 ==========
// ==============================================
// 🌐 部署类型选择（请根据你的运行环境修改）：
//
// 如果你把后端部署在 AWS Lambda 云端：
//   将下面这行改为你的 Lambda Function URL（例如：
//   const LAMBDA_URL = 'https://xxxx.lambda-url.ap-east-1.on.aws/';
//
// 如果你在本地运行后端（python local_server.py）：
//   使用默认的 localhost 地址即可：
//   const LAMBDA_URL = 'http://localhost:5000/';
// ==============================================
const LAMBDA_URL = 'your banckend API endpoint here';  //你的後端端點
//================================================



let resourceGroups = [];
let editingId = null;

// AI 設定
let architectAI = { endpoint: '', model: '', apiKey: '' };
let deployAI = { endpoint: '', model: '', apiKey: '' };
let codeAI = { endpoint: '', model: '', apiKey: '' };
let assistantAI = { endpoint: '', model: '', apiKey: '' };

let currentArchitecture = null;
let currentInfraResult = null;

// ========== DOM 參照（已移除圖片相關） ==========
const resourceList = document.getElementById('resourceGroupsList');
const groupCountSpan = document.getElementById('groupCount');
const addGroupBtn = document.getElementById('addGroupBtn');
const deployGroupSelector = document.getElementById('deployGroupSelector');
const deployBtn = document.getElementById('deployBtn');
const resultDiv = document.getElementById('result');
const confirmArea = document.getElementById('confirmArea');

const architectEndpoint = document.getElementById('architectEndpoint');
const architectModel = document.getElementById('architectModel');
const architectKey = document.getElementById('architectKey');
const deployEndpoint = document.getElementById('deployEndpoint');
const deployModel = document.getElementById('deployModel');
const deployKey = document.getElementById('deployKey');
const assistantEndpoint = document.getElementById('assistantEndpoint');
const assistantModel = document.getElementById('assistantModel');
const assistantKey = document.getElementById('assistantKey');

const floatingBall = document.getElementById('floatingBall');
const chatPanel = document.getElementById('chatPanel');
const chatClose = document.getElementById('chatClose');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');

const codeEndpoint = document.getElementById('codeEndpoint');
const codeModel = document.getElementById('codeModel');
const codeKey = document.getElementById('codeKey');

// ========== 本地儲存（已移除 imageAI） ==========
function loadFromStorage() {
    const savedGroups = localStorage.getItem('resourceGroups');
    if (savedGroups) {
        resourceGroups = JSON.parse(savedGroups);
    } else {
        resourceGroups = [{
            id: Date.now().toString(),
            name: '範例開發帳號',
            services: 'EC2, S3',
            accessKey: '',
            secretKey: '',
            region: 'us-east-1'
        }];
    }

    const savedArchitect = localStorage.getItem('architectAI');
    if (savedArchitect) architectAI = JSON.parse(savedArchitect);

    const savedDeploy = localStorage.getItem('deployAI');
    if (savedDeploy) deployAI = JSON.parse(savedDeploy);

    const savedCode = localStorage.getItem('codeAI');
    if (savedCode) codeAI = JSON.parse(savedCode);

    const savedAssistant = localStorage.getItem('assistantAI');
    if (savedAssistant) assistantAI = JSON.parse(savedAssistant);
}

function saveToStorage() {
    localStorage.setItem('resourceGroups', JSON.stringify(resourceGroups));
    localStorage.setItem('architectAI', JSON.stringify(architectAI));
    localStorage.setItem('deployAI', JSON.stringify(deployAI));
    localStorage.setItem('codeAI', JSON.stringify(codeAI));
    localStorage.setItem('assistantAI', JSON.stringify(assistantAI));
}

function populateAIFields() {
    architectEndpoint.value = architectAI.endpoint || '';
    architectModel.value = architectAI.model || '';
    architectKey.value = architectAI.apiKey || '';
    deployEndpoint.value = deployAI.endpoint || '';
    deployModel.value = deployAI.model || '';
    deployKey.value = deployAI.apiKey || '';
    codeEndpoint.value = codeAI.endpoint || '';
    codeModel.value = codeAI.model || '';
    codeKey.value = codeAI.apiKey || '';
    assistantEndpoint.value = assistantAI.endpoint || '';
    assistantModel.value = assistantAI.model || '';
    assistantKey.value = assistantAI.apiKey || '';
}

// ========== 資源組 UI (保持不變) ==========
function renderResourceGroups() {
    resourceList.innerHTML = '';
    resourceGroups.forEach(group => {
        const item = document.createElement('div');
        item.className = 'resource-item';
        item.dataset.id = group.id;
        item.innerHTML = `
      <div class="resource-main">
        <div class="resource-info">
          <div class="resource-name">${escapeHtml(group.name)}</div>
          <div class="resource-meta">
            <span class="meta-item">🌍 ${escapeHtml(group.region)}</span>
            <span class="meta-item">⚙️ ${escapeHtml(group.services || '無')}</span>
          </div>
        </div>
        <div class="resource-actions">
          <button class="btn btn-sm edit-btn">✏️ 編輯</button>
          <button class="btn btn-sm btn-danger delete-btn">🗑️ 刪除</button>
        </div>
      </div>
      <div class="edit-form">
        <div class="form-group">
          <label>資源組名稱</label>
          <input type="text" class="edit-name" value="${escapeHtml(group.name)}">
        </div>
        <div class="form-group">
          <label>可用服務（逗號分隔，注意拼寫）</label>
          <input type="text" class="edit-services" value="${escapeHtml(group.services)}">
        </div>
        <div class="form-group">
          <label>AWS 區域</label>
          <input type="text" class="edit-region" value="${escapeHtml(group.region)}">
        </div>
        <div class="form-group">
          <label>AWS Access Key ID</label>
          <input type="text" class="edit-access-key" value="${escapeHtml(group.accessKey || '')}">
        </div>
        <div class="form-group">
          <label>AWS Secret Access Key</label>
          <input type="password" class="edit-secret-key" value="${escapeHtml(group.secretKey || '')}">
        </div>
        <div class="btn-group">
          <button class="btn btn-primary save-edit-btn">儲存</button>
          <button class="btn cancel-edit-btn">取消</button>
        </div>
      </div>
    `;
        resourceList.appendChild(item);
        item.querySelector('.edit-btn').addEventListener('click', () => openEditForm(group.id));
        item.querySelector('.delete-btn').addEventListener('click', () => deleteGroup(group.id));
        item.querySelector('.save-edit-btn').addEventListener('click', () => saveEdit(group.id, item));
        item.querySelector('.cancel-edit-btn').addEventListener('click', () => closeEditForm(item));
    });
    updateGroupCount();
    renderDeploymentSelectors();
}

function updateGroupCount() {
    groupCountSpan.textContent = resourceGroups.length;
}

function openEditForm(id) {
    document.querySelectorAll('.edit-form.active').forEach(form => form.classList.remove('active'));
    const item = document.querySelector(`.resource-item[data-id="${id}"]`);
    if (item) item.querySelector('.edit-form').classList.add('active');
}

function closeEditForm(item) {
    item.querySelector('.edit-form').classList.remove('active');
}

function saveEdit(id, item) {
    const group = resourceGroups.find(g => g.id === id);
    if (!group) return;
    group.name = item.querySelector('.edit-name').value.trim();
    group.services = item.querySelector('.edit-services').value.trim();
    group.region = item.querySelector('.edit-region').value.trim();
    group.accessKey = item.querySelector('.edit-access-key').value.trim();
    group.secretKey = item.querySelector('.edit-secret-key').value.trim();
    closeEditForm(item);
    saveToStorage();
    renderResourceGroups();
}

function deleteGroup(id) {
    if (resourceGroups.length <= 1) {
        alert('至少保留一個資源組');
        return;
    }
    resourceGroups = resourceGroups.filter(g => g.id !== id);
    saveToStorage();
    renderResourceGroups();
}

function addNewGroup() {
    const newGroup = {
        id: Date.now().toString(),
        name: '新資源組',
        services: '',
        accessKey: '',
        secretKey: '',
        region: 'us-east-1'
    };
    resourceGroups.push(newGroup);
    saveToStorage();
    renderResourceGroups();
    openEditForm(newGroup.id);
}

function renderDeploymentSelectors() {
    deployGroupSelector.innerHTML = '';
    resourceGroups.forEach(group => {
        const card = document.createElement('label');
        card.className = 'resource-select-card';
        card.innerHTML = `
      <input type="checkbox" value="${group.id}" checked>
      <div class="select-card-body">
        <div class="select-card-title">${escapeHtml(group.name)}</div>
        <div class="select-card-meta">
          <span>🌍 ${escapeHtml(group.region)}</span>
          <span>⚙️ ${escapeHtml(group.services || '無')}</span>
        </div>
      </div>
    `;
        deployGroupSelector.appendChild(card);
    });
}

// ========== 摺疊邏輯 ==========
function initCollapsibles() {
    document.querySelectorAll('.collapsible .card-header').forEach(header => {
        const card = header.closest('.collapsible');
        card.classList.remove('collapsed');
        header.addEventListener('click', () => {
            card.classList.toggle('collapsed');
        });
    });
}

// ========== AI 設定（已移除 imageAI） ==========
function saveAISettings() {
    architectAI = { endpoint: architectEndpoint.value.trim(), model: architectModel.value.trim(), apiKey: architectKey.value.trim() };
    deployAI = { endpoint: deployEndpoint.value.trim(), model: deployModel.value.trim(), apiKey: deployKey.value.trim() };
    codeAI = { endpoint: codeEndpoint.value.trim(), model: codeModel.value.trim(), apiKey: codeKey.value.trim() };
    assistantAI = { endpoint: assistantEndpoint.value.trim(), model: assistantModel.value.trim(), apiKey: assistantKey.value.trim() };
    saveToStorage();
    alert('AI 設定已儲存');
}

function resetAISettings() {
    architectAI = { endpoint: '', model: '', apiKey: '' };
    deployAI = { endpoint: '', model: '', apiKey: '' };
    codeAI = { endpoint: '', model: '', apiKey: '' };
    assistantAI = { endpoint: '', model: '', apiKey: '' };
    localStorage.removeItem('architectAI');
    localStorage.removeItem('deployAI');
    localStorage.removeItem('codeAI');
    localStorage.removeItem('assistantAI');
    populateAIFields();
    alert('設定已重置');
}

//進度條
function setProgress(percent, text) {
    progressArea.style.display = 'block';
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

function hideProgress() {
    progressArea.style.display = 'none';
}

// ========== 第一階段：架構分析 ==========
async function analyzeArchitecture() {
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    if (selectedIds.length === 0) { alert('請至少選擇一個資源組'); return; }

    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));
    const description = document.getElementById('description').value.trim();
    if (!description) { alert('請輸入部署描述'); return; }

    if (!architectAI.endpoint || !architectAI.model || !architectAI.apiKey) {
        alert('請在 AI 設定中填寫「架構生成 AI」的端點、模型和 API Key');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = '架構分析中...';
    setProgress(10, '正在進行架構分析...');

    const payload = {
        action: 'architect',
        resource_groups: groups.map(g => ({
            name: g.name,
            services: g.services.split(',').map(s => s.trim()).filter(Boolean),
            region: g.region
        })),
        architect_ai: {
            endpoint: document.getElementById('architectEndpoint').value.trim(),
            model: document.getElementById('architectModel').value.trim(),
            api_key: document.getElementById('architectKey').value.trim()
        },
        description: description
    };

    try {
        const res = await fetch(LAMBDA_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Unknown error');

        currentArchitecture = data;
        setProgress(25, '架構分析完成，請確認架構方案。');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<strong>📐 架構方案：</strong><br>${escapeHtml(data.architecture || '無')}`;

        confirmArea.style.display = 'block';
        confirmArea.innerHTML = `
      <div style="margin-top:1rem;">
        <p>確認無誤後可繼續部署，或輸入修改意見：</p>
        <textarea id="modifyInput" rows="2" placeholder="輸入修改意見（可選）..."></textarea>
        <button class="btn btn-primary" id="confirmDeployBtn">✅ 確認並繼續部署</button>
        <button class="btn" id="cancelBtn">取消</button>
      </div>
    `;
        document.getElementById('confirmDeployBtn').addEventListener('click', deployInfrastructure);
        document.getElementById('cancelBtn').addEventListener('click', () => {
            confirmArea.style.display = 'none';
            deployBtn.disabled = false;
            deployBtn.textContent = '🚀 開始架構分析';
            hideProgress();
        });

    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<span style="color:#c43f27;">❌ 架構分析失敗：${err.message}</span>`;
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 開始架構分析';
    }
}

async function deployInfrastructure() {
    const modifyText = document.getElementById('modifyInput')?.value.trim() || '';
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));
    const description = document.getElementById('description').value.trim();
    const finalDescription = modifyText ? `${description}\n用戶修改意見：${modifyText}` : description;

    if (!deployAI.endpoint || !deployAI.model || !deployAI.apiKey) {
        alert('請在 AI 設定中填寫「基礎設施部署 AI」的端點、模型和 API Key');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = '部署基礎設施中...';
    confirmArea.style.display = 'none';
    setProgress(30, '正在生成 CloudFormation 模板並部署基礎設施...');

    const payload = {
        action: 'deploy_infra',
        resource_groups: groups.map(g => ({
            name: g.name,
            services: g.services.split(',').map(s => s.trim()).filter(Boolean),
            aws_access_key: g.accessKey,
            aws_secret_key: g.secretKey,
            region: g.region
        })),
        deploy_ai: {
            endpoint: document.getElementById('deployEndpoint').value.trim(),
            model: document.getElementById('deployModel').value.trim(),
            api_key: document.getElementById('deployKey').value.trim()
        },
        architecture: currentArchitecture.architecture,
        resources: currentArchitecture.resources,
        description: finalDescription
    };

    try {
        const res = await fetch(LAMBDA_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Deploy failed');

        const infraResult = data.results[0];
        if (infraResult.error) {
            throw new Error(infraResult.error);
        }

        currentInfraResult = infraResult;
        setProgress(60, '基礎設施部署完成，準備注入程式碼...');
        await uploadCode();

    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<span style="color:#c43f27;">❌ 基礎設施部署失敗：${err.message}</span>`;
        hideProgress();
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 開始架構分析';
    }
}

async function uploadCode() {
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));

    if (!codeAI.endpoint || !codeAI.model || !codeAI.apiKey) {
        alert('請在 AI 設定中填寫「程式碼生成 AI」的端點、模型和 API Key');
        return;
    }

    setProgress(70, '正在生成並上傳程式碼...');

    const payload = {
        action: 'upload_code',
        resource_groups: groups.map(g => ({
            name: g.name,
            aws_access_key: g.accessKey,
            aws_secret_key: g.secretKey,
            region: g.region
        })),
        code_ai: {
            endpoint: document.getElementById('codeEndpoint').value.trim(),
            model: document.getElementById('codeModel').value.trim(),
            api_key: document.getElementById('codeKey').value.trim()
        },
        architecture: currentArchitecture.architecture,
        resources: currentArchitecture.resources,
        resource_mapping: currentInfraResult.resource_mapping,
        description: document.getElementById('description').value.trim()
    };

    try {
        const res = await fetch(LAMBDA_URL, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Code upload failed');

        // 圖片生成已移除，不再呼叫 generateImagesIfNeeded

        setProgress(100, '部署完成！');
        hideProgress();
        resultDiv.style.display = 'block';
        showSuccessResult(currentInfraResult, data.results);

    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<span style="color:#c43f27;">❌ 程式碼上傳失敗：${err.message}</span>`;
        hideProgress();
    } finally {
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 開始架構分析';
    }
}

// 已移除 quickTest 和 generateImagesIfNeeded 函數（不需要）

function showSuccessResult(infraResult, codeResults) {
    let html = '<div class="success-card">';
    html += `<h3>✅ 部署成功</h3>`;

    const outputs = infraResult.outputs || {};
    const region = infraResult.region || 'us-east-1';
    let websiteURL = outputs.WebsiteURL || null;
    let apiEndpoint = outputs.ApiEndpoint || null;

    // 若没有 WebsiteURL，从 resource_mapping 自动构造 S3 静态网站 URL
    if (!websiteURL && infraResult.resource_mapping) {
        const bucketPhyId = Object.values(infraResult.resource_mapping).find(id => id && id.startsWith('ai-deploy-'));
        if (bucketPhyId) {
            // ap-east-1 和 me-central-1 需要使用点 (.) 格式的网站端点
            const dotFormatRegions = ['ap-east-1', 'me-central-1'];
            if (dotFormatRegions.includes(region)) {
                websiteURL = `http://${bucketPhyId}.s3-website.${region}.amazonaws.com`;
            } else {
                websiteURL = `http://${bucketPhyId}.s3-website-${region}.amazonaws.com`;
            }
        }
    }

    if (websiteURL) {
        html += `<p>🌐 網站 URL：<a href="${websiteURL}" target="_blank">${websiteURL}</a></p>`;
    }
    if (apiEndpoint) {
        html += `<p>🔗 API 端點：<a href="${apiEndpoint}" target="_blank">${apiEndpoint}</a></p>`;
    }

    if (infraResult.resource_mapping) {
        html += '<p><strong>📋 已部署資源：</strong></p><ul>';
        for (const [logicalId, physicalId] of Object.entries(infraResult.resource_mapping)) {
            html += `<li>${logicalId} → ${physicalId}</li>`;
        }
        html += '</ul>';
    }

    if (infraResult.console_url) {
        html += `<p><a href="${infraResult.console_url}" target="_blank">🔍 查看 CloudFormation 堆疊</a></p>`;
    }

    if (codeResults && codeResults.length > 0) {
        html += '<p><strong>📝 程式碼上傳狀態：</strong></p><ul>';
        codeResults.forEach(r => {
            if (r.error) {
                html += `<li style="color:#c43f27;">⚠️ ${r.group}: ${r.error}</li>`;
            } else {
                html += `<li>✅ ${r.group}: ${r.message || '上傳完成'}</li>`;
            }
        });
        html += '</ul>';
    }

    // 圖片顯示已移除

    html += '</div>';
    resultDiv.innerHTML = html;
}

// ========== 第二階段：確認並部署（已廢棄，但保留無妨） ==========
async function executeDeployWithConfirmation() {
    const modifyText = document.getElementById('modifyInput')?.value.trim() || '';

    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    if (selectedIds.length === 0) { alert('請至少選擇一個資源組'); return; }

    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));
    const description = document.getElementById('description').value.trim();
    const finalDescription = modifyText ? `${description}\n\n用戶修改意見：${modifyText}` : description;

    if (!deployAI.endpoint || !deployAI.model || !deployAI.apiKey) {
        alert('請在 AI 設定中填寫「部署 AI」的端點、模型和 API Key');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = '部署中...';
    confirmArea.style.display = 'none';
    resultDiv.style.display = 'block';
    resultDiv.style.color = '#3e3a37';
    resultDiv.textContent = '正在部署...';

    const payload = {
        action: 'deploy',
        resource_groups: groups.map(g => ({
            name: g.name,
            services: g.services.split(',').map(s => s.trim()).filter(Boolean),
            aws_access_key: g.accessKey,
            aws_secret_key: g.secretKey,
            region: g.region
        })),
        deploy_ai: {
            endpoint: deployAI.endpoint,
            model: deployAI.model,
            api_key: deployAI.apiKey
        },
        description: finalDescription,
        architecture: currentArchitecture
    };

    try {
        const res = await fetch(LAMBDA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            resultDiv.style.color = '#2b6b4f';
            let text = '✅ 部署請求已發送：<br>';
            if (data.results && Array.isArray(data.results)) {
                data.results.forEach(r => {
                    if (r.error) {
                        text += `⚠️ ${r.group || '未知'}：${r.error}<br>`;
                    } else {
                        text += `📦 ${r.group || '未知'}：Stack "${r.stack_name}" (${r.status})<br>`;
                    }
                });
            } else {
                text += `<pre style="white-space:pre-wrap;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
            }
            resultDiv.innerHTML = text;
        } else {
            resultDiv.style.color = '#c43f27';
            resultDiv.textContent = '❌ 部署失敗：' + (data.error || JSON.stringify(data, null, 2));
        }
    } catch (err) {
        resultDiv.style.color = '#c43f27';
        resultDiv.textContent = '❌ 請求失敗：' + err.message;
    } finally {
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 開始架構分析';
    }
}

// ========== 大型助手面板控制 ==========
function openChatPanel() {
    chatPanel.classList.add('active');
    floatingBall.classList.add('hidden');
}
function closeChatPanel() {
    chatPanel.classList.remove('active');
    floatingBall.classList.remove('hidden');
}

// ========== 訊息渲染（含代碼高亮與複製） ==========
function renderMessageContent(text) {
    const parts = text.split(/(```[\s\S]*?```)/g);
    const container = document.createDocumentFragment();
    parts.forEach(part => {
        if (part.startsWith('```')) {
            const codeMatch = part.match(/```(\w+)?\n?([\s\S]*?)```/);
            const lang = codeMatch?.[1] || '';
            const code = codeMatch?.[2] || part.replace(/```/g, '');
            const codeBlock = document.createElement('div');
            codeBlock.className = 'code-block';
            codeBlock.innerHTML = `
        <div class="code-header">
          <span>${escapeHtml(lang || 'code')}</span>
          <button class="code-copy-btn">複製代碼</button>
        </div>
        <div class="code-content">${escapeHtml(code.trimEnd())}</div>
      `;
            codeBlock.querySelector('.code-copy-btn').addEventListener('click', () => {
                navigator.clipboard.writeText(code.trimEnd()).then(() => {
                    const btn = codeBlock.querySelector('.code-copy-btn');
                    btn.textContent = '已複製';
                    setTimeout(() => btn.textContent = '複製代碼', 2000);
                });
            });
            container.appendChild(codeBlock);
        } else if (part.trim()) {
            const span = document.createElement('span');
            span.textContent = part;
            container.appendChild(span);
        }
    });
    return container;
}

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    msgDiv.appendChild(renderMessageContent(text));
    const copyBtn = document.createElement('button');
    copyBtn.className = 'message-copy-btn';
    copyBtn.textContent = '複製';
    copyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = '已複製';
            setTimeout(() => copyBtn.textContent = '複製', 2000);
        });
    });
    msgDiv.appendChild(copyBtn);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendChatMessage() {
    const question = chatInput.value.trim();
    if (!question) return;
    appendMessage('user', question);
    chatInput.value = '';

    const assistantEndpointVal = assistantEndpoint.value.trim();
    const assistantModelVal = assistantModel.value.trim();
    const assistantKeyVal = assistantKey.value.trim();

    if (!assistantEndpointVal || !assistantModelVal || !assistantKeyVal) {
        appendMessage('assistant', '⚠️ 請先在 AI 設定中填寫助手 AI 的端點、模型與 API Key');
        return;
    }

    try {
        const res = await fetch(assistantEndpointVal, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${assistantKeyVal}`
            },
            body: JSON.stringify({
                model: assistantModelVal,
                messages: [
                    { role: "system", content: "你是一位友善的雲端架構助手，協助回答 AWS 與部署相關問題。" },
                    { role: "user", content: question }
                ]
            })
        });
        const data = await res.json();
        const reply = data?.choices?.[0]?.message?.content || '（無法取得回覆）';
        appendMessage('assistant', reply);
    } catch (err) {
        appendMessage('assistant', '❌ 請求失敗：' + err.message);
    }
}

// ========== 工具函數 ==========
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ========== 事件綁定與啟動 ==========
document.addEventListener('DOMContentLoaded', () => {
    loadFromStorage();
    populateAIFields();
    renderResourceGroups();
    initCollapsibles();

    addGroupBtn.addEventListener('click', addNewGroup);
    document.getElementById('saveAIBtn').addEventListener('click', saveAISettings);
    document.getElementById('resetAIBtn').addEventListener('click', resetAISettings);

    deployBtn.addEventListener('click', analyzeArchitecture);

    floatingBall.addEventListener('click', openChatPanel);
    chatClose.addEventListener('click', closeChatPanel);
    chatPanel.addEventListener('click', (e) => {
        if (e.target === chatPanel) closeChatPanel();
    });

    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
});