// ========== Global State ==========
// ==============================================
// 🌐 Deployment Type (change according to your environment):
//
// If you have deployed the backend to AWS Lambda:
//   Replace the line below with your Lambda Function URL, e.g.:
//   const LAMBDA_URL = 'https://xxxx.lambda-url.ap-east-1.on.aws/';
//
// If you are running the backend locally (python local_server.py):
//   Keep the default localhost address:
//   const LAMBDA_URL = 'http://localhost:5000/';
// ==============================================
const LAMBDA_URL = 'your banckend API endpoint here'; // TODO: replace with your actual backend endpoint
//=================================================



let resourceGroups = [];
let editingId = null;
// AI Configuration (imageAI removed)
let architectAI = { endpoint: '', model: '', apiKey: '' };
let deployAI = { endpoint: '', model: '', apiKey: '' };
let codeAI = { endpoint: '', model: '', apiKey: '' };
let assistantAI = { endpoint: '', model: '', apiKey: '' };
let currentArchitecture = null;
let currentInfraResult = null;

// ========== DOM References (Image-related removed) ==========
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
const progressArea = document.getElementById('progressArea');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

// ========== Local Storage (imageAI removed) ==========
function loadFromStorage() {
    const savedGroups = localStorage.getItem('resourceGroups');
    if (savedGroups) {
        resourceGroups = JSON.parse(savedGroups);
    } else {
        resourceGroups = [{
            id: Date.now().toString(),
            name: 'Example Dev Account',
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

// ========== Resource Group UI (Unchanged) ==========
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
                        <span class="meta-item">⚙️ ${escapeHtml(group.services || 'None')}</span> 
                    </div> 
                </div> 
                <div class="resource-actions"> 
                    <button class="btn btn-sm edit-btn">✏️ Edit</button> 
                    <button class="btn btn-sm btn-danger delete-btn">🗑️ Delete</button> 
                </div> 
            </div> 
            <div class="edit-form"> 
                <div class="form-group"> 
                    <label>Resource Group Name</label> 
                    <input type="text" class="edit-name" value="${escapeHtml(group.name)}"> 
                </div> 
                <div class="form-group"> 
                    <label>Available Services (comma-separated, check spelling)</label> 
                    <input type="text" class="edit-services" value="${escapeHtml(group.services)}"> 
                </div> 
                <div class="form-group"> 
                    <label>AWS Region</label> 
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
                    <button class="btn btn-primary save-edit-btn">Save</button> 
                    <button class="btn cancel-edit-btn">Cancel</button> 
                </div> 
            </div>`;
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
        alert('At least one resource group must be kept.');
        return;
    }
    resourceGroups = resourceGroups.filter(g => g.id !== id);
    saveToStorage();
    renderResourceGroups();
}

function addNewGroup() {
    const newGroup = {
        id: Date.now().toString(),
        name: 'New Resource Group',
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
                    <span>⚙️ ${escapeHtml(group.services || 'None')}</span> 
                </div> 
            </div>`;
        deployGroupSelector.appendChild(card);
    });
}

// ========== Collapsible Logic ==========
function initCollapsibles() {
    document.querySelectorAll('.collapsible .card-header').forEach(header => {
        const card = header.closest('.collapsible');
        card.classList.remove('collapsed');
        header.addEventListener('click', () => {
            card.classList.toggle('collapsed');
        });
    });
}

// ========== AI Configuration (imageAI removed) ==========
function saveAISettings() {
    architectAI = { endpoint: architectEndpoint.value.trim(), model: architectModel.value.trim(), apiKey: architectKey.value.trim() };
    deployAI = { endpoint: deployEndpoint.value.trim(), model: deployModel.value.trim(), apiKey: deployKey.value.trim() };
    codeAI = { endpoint: codeEndpoint.value.trim(), model: codeModel.value.trim(), apiKey: codeKey.value.trim() };
    assistantAI = { endpoint: assistantEndpoint.value.trim(), model: assistantModel.value.trim(), apiKey: assistantKey.value.trim() };
    saveToStorage();
    alert('AI settings saved.');
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
    alert('Settings reset.');
}

// Progress Bar
function setProgress(percent, text) {
    progressArea.style.display = 'block';
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

function hideProgress() {
    progressArea.style.display = 'none';
}

// ========== Phase 1: Architecture Analysis ==========
async function analyzeArchitecture() {
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    if (selectedIds.length === 0) { alert('Please select at least one resource group.'); return; }
    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));
    const description = document.getElementById('description').value.trim();
    if (!description) { alert('Please enter a deployment description.'); return; }

    if (!architectAI.endpoint || !architectAI.model || !architectAI.apiKey) {
        alert('Please fill in the endpoint, model, and API Key for "Architecture Generation AI" in the AI settings.');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = 'Analyzing architecture...';
    setProgress(10, 'Performing architecture analysis...');

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
        setProgress(25, 'Architecture analysis complete. Please confirm the architecture plan.');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = ` <strong>📐 Architecture Plan: </strong> <br>${escapeHtml(data.architecture || 'None')}`;

        confirmArea.style.display = 'block';
        confirmArea.innerHTML = `
            <div style="margin-top:1rem;">
                <p>Confirm to proceed with deployment, or enter modification requests:</p>
                <textarea id="modifyInput" rows="2" placeholder="Enter modification requests (optional)..."></textarea>
                <button class="btn btn-primary" id="confirmDeployBtn">✅ Confirm & Proceed with Deployment</button>
                <button class="btn" id="cancelBtn">Cancel</button>
            </div>`;
        document.getElementById('confirmDeployBtn').addEventListener('click', deployInfrastructure);
        document.getElementById('cancelBtn').addEventListener('click', () => {
            confirmArea.style.display = 'none';
            deployBtn.disabled = false;
            deployBtn.textContent = '🚀 Start Architecture Analysis';
            hideProgress();
        });

    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = ` <span style="color:#c43f27;">❌ Architecture analysis failed: ${err.message}</span>`;
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 Start Architecture Analysis';
    }
}

async function deployInfrastructure() {
    const modifyText = document.getElementById('modifyInput')?.value.trim() || '';
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));
    const description = document.getElementById('description').value.trim();
    const finalDescription = modifyText ? `${description}\nUser Modification Requests: ${modifyText}` : description;

    if (!deployAI.endpoint || !deployAI.model || !deployAI.apiKey) {
        alert('Please fill in the endpoint, model, and API Key for "Infrastructure Deployment AI" in the AI settings.');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = 'Deploying infrastructure...';
    confirmArea.style.display = 'none';
    setProgress(30, 'Generating CloudFormation templates and deploying infrastructure...');

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
        setProgress(60, 'Infrastructure deployment complete. Preparing code injection...');
        await uploadCode();

    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = ` <span style="color:#c43f27;">❌ Infrastructure deployment failed: ${err.message}</span>`;
        hideProgress();
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 Start Architecture Analysis';
    }
}

async function uploadCode() {
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));

    if (!codeAI.endpoint || !codeAI.model || !codeAI.apiKey) {
        alert('Please fill in the endpoint, model, and API Key for "Code Generation AI" in the AI settings.');
        return;
    }

    setProgress(70, 'Generating and uploading code...');

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

        // Image generation removed, no longer calling generateImagesIfNeeded

        setProgress(100, 'Deployment complete!');
        hideProgress();
        resultDiv.style.display = 'block';
        showSuccessResult(currentInfraResult, data.results);

    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `<span style="color:#c43f27;">❌ Code upload failed: ${err.message}</span>`;
        hideProgress();
    } finally {
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 Start Architecture Analysis';
    }
}

// quickTest and generateImagesIfNeeded functions removed (not needed)
function showSuccessResult(infraResult, codeResults) {
    let html = '<div class="success-card">';
    html += `<h3>✅ Deployment Successful</h3>`;
    const outputs = infraResult.outputs || {};
    const region = infraResult.region || 'us-east-1';
    let websiteURL = outputs.WebsiteURL || null;
    let apiEndpoint = outputs.ApiEndpoint || null;

    // If no WebsiteURL, automatically construct S3 static website URL from resource_mapping
     
    if (!websiteURL && infraResult.resource_mapping) {
        const bucketPhyId = Object.values(infraResult.resource_mapping).find(id => id && id.startsWith('ai-deploy-'));
        if (bucketPhyId) {
            
            const dotFormatRegions = ['ap-east-1', 'me-central-1'];
            if (dotFormatRegions.includes(region)) {
                websiteURL = `http://${bucketPhyId}.s3-website.${region}.amazonaws.com`;
            } else {
                websiteURL = `http://${bucketPhyId}.s3-website-${region}.amazonaws.com`;
            }
        }
    }

    if (websiteURL) {
        html += ` <p>🌐 Website URL: <a href="${websiteURL}" target="_blank">${websiteURL}</a></p>`;
    }
    if (apiEndpoint) {
        html += ` <p>🔗 API Endpoint: <a href="${apiEndpoint}" target="_blank">${apiEndpoint}</a></p>`;
    }

    if (infraResult.resource_mapping) {
        html += ' <p><strong>📋 Deployed Resources:</strong></p><ul>';
        for (const [logicalId, physicalId] of Object.entries(infraResult.resource_mapping)) {
            html += ` <li>${logicalId} → ${physicalId}</li>`;
        }
        html += '</ul>';
    }

    if (infraResult.console_url) {
        html += ` <p><a href="${infraResult.console_url}" target="_blank">🔍 View CloudFormation Stack</a></p>`;
    }

    if (codeResults && codeResults.length > 0) {
        html += ' <p><strong>📝 Code Upload Status:</strong></p><ul>';
        codeResults.forEach(r => {
            if (r.error) {
                html += ` <li style="color:#c43f27;">⚠️ ${r.group}: ${r.error}</li>`;
            } else {
                html += ` <li>✅ ${r.group}: ${r.message || 'Upload complete'}</li>`;
            }
        });
        html += '</ul>';
    }

    // Image display removed

    html += '</div>';
    resultDiv.innerHTML = html;
}

// ========== Phase 2: Confirm & Deploy (Deprecated, kept for reference) ==========
async function executeDeployWithConfirmation() {
    const modifyText = document.getElementById('modifyInput')?.value.trim() || '';
    const selectedIds = Array.from(deployGroupSelector.querySelectorAll('input:checked')).map(cb => cb.value);
    if (selectedIds.length === 0) { alert('Please select at least one resource group.'); return; }

    const groups = resourceGroups.filter(g => selectedIds.includes(g.id));
    const description = document.getElementById('description').value.trim();
    const finalDescription = modifyText ? `${description}\n\nUser Modification Requests: ${modifyText}` : description;

    if (!deployAI.endpoint || !deployAI.model || !deployAI.apiKey) {
        alert('Please fill in the endpoint, model, and API Key for "Deployment AI" in the AI settings.');
        return;
    }

    deployBtn.disabled = true;
    deployBtn.textContent = 'Deploying...';
    confirmArea.style.display = 'none';
    resultDiv.style.display = 'block';
    resultDiv.style.color = '#3e3a37';
    resultDiv.textContent = 'Deploying...';

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
            let text = '✅ Deployment request sent:<br>';
            if (data.results && Array.isArray(data.results)) {
                data.results.forEach(r => {
                    if (r.error) {
                        text += `⚠️ ${r.group || 'Unknown'}: ${r.error}<br>`;
                    } else {
                        text += `📦 ${r.group || 'Unknown'}: Stack "${r.stack_name}" (${r.status})<br>`;
                    }
                });
            } else {
                text += `<pre style="white-space:pre-wrap;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
            }
            resultDiv.innerHTML = text;
        } else {
            resultDiv.style.color = '#c43f27';
            resultDiv.textContent = '❌ Deployment failed: ' + (data.error || JSON.stringify(data, null, 2));
        }
    } catch (err) {
        resultDiv.style.color = '#c43f27';
        resultDiv.textContent = '❌ Request failed: ' + err.message;
    } finally {
        deployBtn.disabled = false;
        deployBtn.textContent = '🚀 Start Architecture Analysis';
    }
}

// ========== Floating Assistant Panel Control ==========
function openChatPanel() {
    chatPanel.classList.add('active');
    floatingBall.classList.add('hidden');
}

function closeChatPanel() {
    chatPanel.classList.remove('active');
    floatingBall.classList.remove('hidden');
}

// ========== Message Rendering (with code highlighting & copy) ==========
function renderMessageContent(text) {
    const parts = text.split(/(`[\s\S]*?`)/g);
    const container = document.createDocumentFragment();
    parts.forEach(part => {
        if (part.startsWith('`')) {
            const codeMatch = part.match(/`(\w+)?\n?([\s\S]*?)`/);
            const lang = codeMatch?.[1] || '';
            const code = codeMatch?.[2] || part.replace(/`/g, '');
            const codeBlock = document.createElement('div');
            codeBlock.className = 'code-block';
            codeBlock.innerHTML = `
                <div class="code-header"> 
                    <span>${escapeHtml(lang || 'code')}</span> 
                    <button class="code-copy-btn">Copy Code</button> 
                </div> 
                <div class="code-content">${escapeHtml(code.trimEnd())}</div>`;
            codeBlock.querySelector('.code-copy-btn').addEventListener('click', () => {
                navigator.clipboard.writeText(code.trimEnd()).then(() => {
                    const btn = codeBlock.querySelector('.code-copy-btn');
                    btn.textContent = 'Copied!';
                    setTimeout(() => btn.textContent = 'Copy Code', 2000);
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
    copyBtn.textContent = 'Copy';
    copyBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = 'Copied!';
            setTimeout(() => copyBtn.textContent = 'Copy', 2000);
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
        appendMessage('assistant', '⚠️ Please first fill in the endpoint, model, and API Key for the Assistant AI in the AI settings.');
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
                    { role: "system", content: "You are a friendly cloud architecture assistant, helping answer AWS and deployment-related questions." },
                    { role: "user", content: question }
                ]
            })
        });
        const data = await res.json();
        const reply = data?.choices?.[0]?.message?.content || '(Unable to retrieve reply)';
        appendMessage('assistant', reply);
    } catch (err) {
        appendMessage('assistant', '❌ Request failed: ' + err.message);
    }
}

// ========== Utility Functions ==========
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ========== Event Binding & Initialization ==========
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