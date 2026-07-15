// frontend/app.js

// State management
const state = {
    workspaceFiles: [],
    openTabs: [],
    activeFile: null,
    activeView: 'editor', // 'editor' | 'dashboard'
    isSplit: false,
    pipelineState: 'idle', // 'idle' | 'running' | 'done'
    modules: {}, // Schema: { [name]: { status, retryCount, confidence, complexity, runs: [] } }
    activeStream: null,
    currentThinkingBubble: null,
    currentOrchestratorBubble: null,
    currentActiveWorker: null
};

// Monaco editor elements
let editorInstance = null;
let leftEditorInstance = null;
let rightEditorInstance = null;

// Initialize Monaco Editors
function initMonaco() {
    require(['vs/editor/editor.main'], function () {
        // Create main single editor
        editorInstance = monaco.editor.create(document.getElementById('monaco-editor-container'), {
            value: `// Welcome to Legacy Migration Harness Multi-Agent IDE.\n// Select a file from the workspace or click "Start Migration" to begin.`,
            language: 'javascript',
            theme: 'vs-dark',
            automaticLayout: true,
            readOnly: false,
            minimap: { enabled: false }
        });

        // Create split left/right editors
        leftEditorInstance = monaco.editor.create(document.getElementById('monaco-left-container'), {
            value: '',
            language: 'javascript',
            theme: 'vs-dark',
            automaticLayout: true,
            readOnly: true,
            minimap: { enabled: false }
        });

        rightEditorInstance = monaco.editor.create(document.getElementById('monaco-right-container'), {
            value: '',
            language: 'javascript',
            theme: 'vs-dark',
            automaticLayout: true,
            readOnly: false,
            minimap: { enabled: false }
        });
    });
}

// Detect language from file path
function getEditorLanguage(filePath) {
    if (!filePath) return 'plaintext';
    const ext = filePath.split('.').pop().toLowerCase();
    switch (ext) {
        case 'frm':
        case 'bas':
        case 'cls':
            return 'vb';
        case 'cbl':
        case 'cpy':
            return 'cobol';
        case 'cs':
            return 'csharp';
        case 'json':
            return 'json';
        case 'md':
            return 'markdown';
        default:
            return 'plaintext';
    }
}

// Check counterpart for split view
function getCounterpartPath(filePath) {
    if (!filePath) return null;
    
    if (filePath.includes('InvoiceController.cs') || filePath.includes('InvoiceViewModel.cs') || filePath.includes('InvoiceTests.cs')) {
        return {
            left: 'source/frmInvoice.frm',
            right: 'output/InvoiceController.cs'
        };
    }
    if (filePath.includes('frmInvoice.frm') || filePath.includes('INVOICE.cbl')) {
        return {
            left: filePath,
            right: 'output/InvoiceController.cs'
        };
    }
    if (filePath.includes('CustomerController.cs') || filePath.includes('CustomerViewModel.cs')) {
        return {
            left: 'source/frmCustomer.frm',
            right: 'output/CustomerController.cs'
        };
    }
    if (filePath.includes('frmCustomer.frm')) {
        return {
            left: filePath,
            right: 'output/CustomerController.cs'
        };
    }
    if (filePath.includes('BillingProcessor.cs')) {
        return {
            left: 'source/billing_proc.cbl',
            right: 'output/BillingProcessor.cs'
        };
    }
    if (filePath.includes('billing_proc.cbl')) {
        return {
            left: filePath,
            right: 'output/BillingProcessor.cs'
        };
    }
    return null;
}

// Load workspace file list
async function loadWorkspaceTree() {
    try {
        const response = await fetch('/api/workspace/files');
        const data = await response.json();
        state.workspaceFiles = data;
        renderFileTree(data);
    } catch (e) {
        console.error("Failed to load file tree", e);
    }
}

// Render File Tree list dynamically
function renderFileTree(nodes, container = document.getElementById('files-tree-root'), depth = 0) {
    if (depth === 0) {
        container.innerHTML = '';
        if (nodes.length === 0) {
            container.innerHTML = '<div class="loading-spinner">Empty workspace</div>';
            return;
        }
    }
    
    nodes.forEach(node => {
        const div = document.createElement('div');
        div.className = `tree-node ${node.type}`;
        div.style.paddingLeft = `${depth * 12 + (node.type === 'file' ? 20 : 8)}px`;
        
        const icon = document.createElement('i');
        if (node.type === 'directory') {
            icon.className = 'fa-solid fa-folder-closed';
        } else {
            icon.className = 'fa-regular fa-file-code';
        }
        
        const label = document.createElement('span');
        label.textContent = node.name;
        
        div.appendChild(icon);
        div.appendChild(label);
        
        if (state.activeFile === node.path) {
            div.classList.add('active-node');
        }
        
        div.addEventListener('click', (e) => {
            e.stopPropagation();
            if (node.type === 'file') {
                openFile(node.path);
            } else {
                // Toggle folder open/closed icon
                const isClosed = icon.classList.contains('fa-folder-closed');
                icon.className = isClosed ? 'fa-solid fa-folder-open' : 'fa-solid fa-folder-closed';
                // Show/hide children nodes
                let sibling = div.nextElementSibling;
                while (sibling && sibling.dataset.depth > depth) {
                    sibling.style.display = isClosed ? 'flex' : 'none';
                    sibling = sibling.nextElementSibling;
                }
            }
        });
        
        div.dataset.depth = depth;
        container.appendChild(div);
        
        if (node.children) {
            renderFileTree(node.children, container, depth + 1);
        }
    });
}

// Open File in editor
async function openFile(filePath) {
    try {
        state.activeFile = filePath;
        
        // Hide welcome screen
        document.getElementById('editor-welcome-screen').style.display = 'none';
        
        // Add tab if not exists
        if (!state.openTabs.includes(filePath)) {
            state.openTabs.push(filePath);
        }
        
        const response = await fetch(`/api/workspace/file?path=${filePath}`);
        const data = await response.json();
        
        if (data.error) {
            alert("Error loading file: " + data.error);
            return;
        }

        renderTabs();
        updateActiveNodeClass();

        const lang = getEditorLanguage(filePath);
        
        if (state.isSplit) {
            const counterparts = getCounterpartPath(filePath);
            if (counterparts) {
                // Load left pane (legacy source)
                const leftRes = await fetch(`/api/workspace/file?path=${counterparts.left}`);
                const leftData = await leftRes.json();
                
                // Load right pane (converted MVC C#)
                const rightRes = await fetch(`/api/workspace/file?path=${counterparts.right}`);
                const rightData = await rightRes.json();
                
                if (leftEditorInstance && rightEditorInstance) {
                    const leftModel = monaco.editor.createModel(leftData.content || '', getEditorLanguage(counterparts.left));
                    const rightModel = monaco.editor.createModel(rightData.content || '', getEditorLanguage(counterparts.right));
                    leftEditorInstance.setModel(leftModel);
                    rightEditorInstance.setModel(rightModel);
                }
            } else {
                // Not splitable, fallback to single pane
                toggleSplitMode(false);
                if (editorInstance) {
                    const model = monaco.editor.createModel(data.content, lang);
                    editorInstance.setModel(model);
                }
            }
        } else {
            if (editorInstance) {
                const model = monaco.editor.createModel(data.content, lang);
                editorInstance.setModel(model);
            }
        }
    } catch (e) {
        console.error("Error opening file", e);
    }
}

// Render active tabs above editor
function renderTabs() {
    const container = document.getElementById('active-file-tabs');
    container.innerHTML = '';
    
    if (state.openTabs.length === 0) {
        container.innerHTML = '<span class="no-files-tab">No file open</span>';
        document.getElementById('editor-welcome-screen').style.display = 'flex';
        return;
    }
    
    state.openTabs.forEach(tabPath => {
        const tab = document.createElement('div');
        tab.className = `file-tab ${state.activeFile === tabPath ? 'active' : ''}`;
        
        const label = document.createElement('span');
        label.textContent = tabPath.split('/').pop();
        label.title = tabPath;
        label.addEventListener('click', () => openFile(tabPath));
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'close-tab-btn';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeTab(tabPath);
        });
        
        tab.appendChild(label);
        tab.appendChild(closeBtn);
        container.appendChild(tab);
    });
}

// Close a file tab
function closeTab(tabPath) {
    const idx = state.openTabs.indexOf(tabPath);
    if (idx !== -1) {
        state.openTabs.splice(idx, 1);
    }
    
    if (state.activeFile === tabPath) {
        if (state.openTabs.length > 0) {
            openFile(state.openTabs[Math.max(0, idx - 1)]);
        } else {
            state.activeFile = null;
            document.getElementById('editor-welcome-screen').style.display = 'flex';
            renderTabs();
            updateActiveNodeClass();
        }
    } else {
        renderTabs();
    }
}

// Highlight the active file inside tree explorer
function updateActiveNodeClass() {
    document.querySelectorAll('.tree-node.file').forEach(el => {
        const text = el.querySelector('span').textContent;
        const isActive = state.activeFile && state.activeFile.endsWith(text);
        if (isActive) {
            el.classList.add('active-node');
        } else {
            el.classList.remove('active-node');
        }
    });
}

// Toggle Split Editor View
function toggleSplitMode(forceState = null) {
    state.isSplit = forceState !== null ? forceState : !state.isSplit;
    
    const singleContainer = document.getElementById('monaco-editor-container');
    const splitContainer = document.getElementById('monaco-split-container');
    const btn = document.getElementById('btn-toggle-split');
    
    if (state.isSplit) {
        singleContainer.style.display = 'none';
        splitContainer.style.display = 'flex';
        btn.classList.add('active');
        btn.querySelector('span').textContent = "Single View";
        if (state.activeFile) {
            openFile(state.activeFile); // reload split models
        }
    } else {
        singleContainer.style.display = 'block';
        splitContainer.style.display = 'none';
        btn.classList.remove('active');
        btn.querySelector('span').textContent = "Split View";
        if (state.activeFile) {
            openFile(state.activeFile); // reload single model
        }
    }
}

// Switch between Code Editor tab and Dashboard tab
function switchView(viewName) {
    state.activeView = viewName;
    
    const editorBtn = document.getElementById('tab-editor');
    const dashBtn = document.getElementById('tab-dashboard');
    
    const editorContent = document.getElementById('editor-view');
    const dashContent = document.getElementById('dashboard-view');
    const editorActions = document.getElementById('editor-actions-bar');
    
    if (viewName === 'editor') {
        editorBtn.classList.add('active');
        dashBtn.classList.remove('active');
        
        editorContent.style.display = 'flex';
        dashContent.style.display = 'none';
        editorActions.style.display = 'flex';
        
        // Quick layout refresh
        if (editorInstance) editorInstance.layout();
        if (leftEditorInstance) leftEditorInstance.layout();
        if (rightEditorInstance) rightEditorInstance.layout();
    } else {
        editorBtn.classList.remove('active');
        dashBtn.classList.add('active');
        
        editorContent.style.display = 'none';
        dashContent.style.display = 'flex';
        editorActions.style.display = 'none';
        
        // Reset dashboard alert badge count
        const alertBadge = document.getElementById('dashboard-alert-badge');
        alertBadge.style.display = 'none';
        alertBadge.textContent = '0';
        
        renderDashboardTable();
    }
}

// Custom resizable pane logic using raw dragging listener
function initResizablePanes() {
    const resizer = document.getElementById('pane-resizer');
    const leftPane = document.getElementById('left-pane');
    const rightPane = document.getElementById('right-pane');
    
    let isDragging = false;
    
    resizer.addEventListener('mousedown', function (e) {
        isDragging = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    });
    
    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;
        const totalWidth = window.innerWidth;
        const dragX = e.clientX;
        
        // Enforce boundary spacing
        if (dragX > 250 && dragX < totalWidth - 250) {
            const leftWidthPercent = (dragX / totalWidth) * 100;
            const rightWidthPercent = 100 - leftWidthPercent;
            
            leftPane.style.flex = `0 0 ${leftWidthPercent}%`;
            rightPane.style.flex = `0 0 ${rightWidthPercent}%`;
            
            // Re-layout Monaco editors to adapt container size changes
            if (editorInstance) editorInstance.layout();
            if (leftEditorInstance) leftEditorInstance.layout();
            if (rightEditorInstance) rightEditorInstance.layout();
        }
    });
    
    document.addEventListener('mouseup', function () {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

// Simple Markdown parser utility
function parseMarkdown(text) {
    if (!text) return '';
    // Format bold headers
    let html = text.replace(/^### (.*$)/gim, '<h4>$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2>$1</h2>');
    // Format bullet points
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.wrapLists ? html : html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    // Format bold text
    html = html.replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>');
    // Format code block
    html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');
    // Line breaks
    html = html.replace(/\n/gim, '<br>');
    return html;
}

// Append messages to Orchestrator Chat log
function appendChatMessage(role, title, content) {
    const chatContainer = document.getElementById('chat-messages-container');
    
    const msgBubble = document.createElement('div');
    msgBubble.className = `msg-bubble ${role === 'user' ? 'user' : 'system'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.innerHTML = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';
    
    const msgContent = document.createElement('div');
    msgContent.className = 'msg-content';
    
    const h4 = document.createElement('h4');
    h4.textContent = title;
    
    const body = document.createElement('div');
    body.className = 'msg-body-text';
    body.innerHTML = parseMarkdown(content);
    
    msgContent.appendChild(h4);
    msgContent.appendChild(body);
    msgBubble.appendChild(avatar);
    msgBubble.appendChild(msgContent);
    
    chatContainer.appendChild(msgBubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return body;
}

// Append or update streaming thinking logs accordion
function updateThinkingLog(thinkingText) {
    const chatContainer = document.getElementById('chat-messages-container');
    
    if (!state.currentThinkingBubble) {
        // Create new thinking block
        const block = document.createElement('div');
        block.className = 'thinking-block';
        
        const header = document.createElement('div');
        header.className = 'thinking-header';
        header.innerHTML = '<span><i class="fa-solid fa-brain fa-spin-slow"></i> Agent Thinking Process...</span><i class="fa-solid fa-chevron-down"></i>';
        
        const content = document.createElement('div');
        content.className = 'thinking-content';
        content.style.display = 'block';
        
        header.addEventListener('click', () => {
            const isVisible = content.style.display === 'block';
            content.style.display = isVisible ? 'none' : 'block';
            header.querySelector('.fa-chevron-down').className = isVisible ? 'fa-solid fa-chevron-right' : 'fa-solid fa-chevron-down';
        });
        
        block.appendChild(header);
        block.appendChild(content);
        chatContainer.appendChild(block);
        
        state.currentThinkingBubble = content;
    }
    
    state.currentThinkingBubble.textContent += thinkingText;
    state.currentThinkingBubble.scrollTop = state.currentThinkingBubble.scrollHeight;
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Collapse the thinking accordion once LLM completes reasoning
function finishThinkingLog() {
    if (state.currentThinkingBubble) {
        const header = state.currentThinkingBubble.parentElement.querySelector('.thinking-header');
        header.innerHTML = '<span><i class="fa-solid fa-brain"></i> Agent Thinking complete</span><i class="fa-solid fa-chevron-right"></i>';
        state.currentThinkingBubble.style.display = 'none'; // Collapse it
        state.currentThinkingBubble = null;
    }
}

// Update Active Worker Status Grid Chips
function updateWorkerChips(activeRole) {
    // Reset all chips
    document.querySelectorAll('.worker-chip').forEach(el => {
        el.className = 'worker-chip idle';
    });
    
    if (!activeRole) return;
    
    const targetChip = document.getElementById(`chip-${activeRole}`);
    if (targetChip) {
        targetChip.className = 'worker-chip active';
    }
}

// Live statistics calculations
function updateDashboardStats() {
    let total = 0;
    let converted = 0;
    let progress = 0;
    let escalated = 0;
    
    Object.values(state.modules).forEach(m => {
        total++;
        if (m.status === 'done') converted++;
        else if (m.status === 'converting' || m.status === 'validating') progress++;
        else if (m.status === 'escalated') escalated++;
    });
    
    document.getElementById('stat-total').textContent = total || 3;
    document.getElementById('stat-converted').textContent = converted;
    document.getElementById('stat-progress').textContent = progress;
    document.getElementById('stat-escalated').textContent = escalated;
    
    const rate = total > 0 ? Math.round((converted / total) * 100) : 0;
    document.getElementById('stat-rate').textContent = `${rate}%`;
}

// Render Dashboard table row by row
function renderDashboardTable() {
    const tbody = document.getElementById('dashboard-modules-body');
    tbody.innerHTML = '';
    
    const keys = Object.keys(state.modules);
    if (keys.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-table-row">No modules discovered yet. Start the migration.</td>
            </tr>`;
        return;
    }
    
    keys.forEach(key => {
        const mod = state.modules[key];
        const tr = document.createElement('tr');
        
        // complexity color coding class helper
        const complexityClass = mod.complexity || 'Medium';
        const confidenceText = mod.confidence ? `${Math.round(mod.confidence * 100)}%` : '-';
        
        tr.innerHTML = `
            <td><strong>${key}</strong></td>
            <td><span class="complexity-tag ${complexityClass}">${complexityClass}</span></td>
            <td><span class="status-pill ${mod.status}">${mod.status.toUpperCase()}</span></td>
            <td><span class="retry-badge">${mod.retryCount}/3</span></td>
            <td><strong>${confidenceText}</strong></td>
            <td>
                <button class="view-log-btn" onclick="openDrawer('${key}')">
                    <i class="fa-solid fa-magnifying-glass-chart"></i> View Details
                </button>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

// Open detail Drawer panel (Slide-out)
window.openDrawer = function(moduleName) {
    const mod = state.modules[moduleName];
    if (!mod) return;
    
    document.getElementById('drawer-module-title').textContent = moduleName;
    document.getElementById('detail-drawer').classList.add('open');
    
    // Draw timeline runs
    const timeline = document.getElementById('drawer-timeline-content');
    timeline.innerHTML = '';
    
    if (!mod.runs || mod.runs.length === 0) {
        timeline.innerHTML = '<p class="text-muted">No runs executed yet.</p>';
        document.getElementById('drawer-build-log').textContent = 'No build log.';
        document.getElementById('drawer-test-log').textContent = 'No test log.';
        document.getElementById('drawer-qa-report').innerHTML = '<p>No QA review generated.</p>';
        return;
    }
    
    mod.runs.forEach(run => {
        const item = document.createElement('div');
        item.className = `timeline-item ${run.status}`;
        
        item.innerHTML = `
            <div class="timeline-header">
                <span>Run Retry Loop #${run.retry} (${run.stage.toUpperCase()})</span>
                <span class="status-pill ${run.status === 'success' ? 'done' : 'escalated'}">${run.status.toUpperCase()}</span>
            </div>
            <div class="timeline-desc">Status report: Completed execution block inside dotnet sandbox wrapper.</div>
        `;
        
        // Clicking timeline item loads its specific build, test and QA logs
        item.addEventListener('click', () => {
            document.querySelectorAll('.timeline-item').forEach(el => el.style.borderColor = 'var(--border-color)');
            item.style.borderColor = 'var(--color-primary)';
            loadRunLogs(run);
        });
        
        timeline.appendChild(item);
    });
    
    // Auto load last run logs
    const lastRun = mod.runs[mod.runs.length - 1];
    loadRunLogs(lastRun);
};

// Set logs tab text values
function loadRunLogs(run) {
    document.getElementById('drawer-build-log').textContent = run.build_log || 'No build outputs generated.';
    document.getElementById('drawer-test-log').textContent = run.test_log || 'No test cases executed.';
    
    const qaBox = document.getElementById('drawer-qa-report');
    if (run.qa_review) {
        qaBox.innerHTML = parseMarkdown(run.qa_review);
    } else {
        qaBox.innerHTML = '<p class="text-muted">No QA report for this execution stage.</p>';
    }
}

// Reset workspace files and dashboard state
async function resetWorkspace() {
    if (state.pipelineState === 'running') {
        alert("Cannot reset while pipeline migration is active!");
        return;
    }
    
    if (!confirm("Are you sure you want to reset workspace files and clear the pipeline history?")) return;
    
    try {
        await fetch('/api/workspace/reset', { method: 'POST' });
        state.modules = {};
        state.openTabs = [];
        state.activeFile = null;
        
        // Refresh GUI
        renderTabs();
        document.getElementById('editor-welcome-screen').style.display = 'flex';
        document.getElementById('chat-messages-container').innerHTML = `
            <div class="msg-bubble system">
                <div class="avatar"><i class="fa-solid fa-robot"></i></div>
                <div class="msg-content">
                    <h4>System Orchestrator</h4>
                    <p>Workspace cleared and reset successfully. Ready to run new migration loop demonstration.</p>
                </div>
            </div>
        `;
        
        updateWorkerChips(null);
        document.getElementById('pipeline-status-text').className = 'pipeline-badge idle';
        document.getElementById('pipeline-status-text').textContent = 'Pipeline Idle';
        
        await loadWorkspaceTree();
        updateDashboardStats();
        renderDashboardTable();
    } catch (e) {
        console.error(e);
    }
}

// Trigger streaming pipeline migration
function startMigration() {
    if (state.pipelineState === 'running') return;
    
    state.pipelineState = 'running';
    state.modules = {};
    
    // UI states
    const btn = document.getElementById('btn-run-migration');
    btn.disabled = true;
    btn.className = 'chat-action-btn stop';
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running';
    
    const badge = document.getElementById('pipeline-status-text');
    badge.className = 'pipeline-badge running';
    badge.textContent = 'Migrating';
    
    // Clear screen
    document.getElementById('chat-messages-container').innerHTML = '';
    appendChatMessage('system', 'System Orchestrator', 'Starting migration execution sequence...');
    
    // Open Server-Sent Events stream connection
    const source = new EventSource('/api/agent/stream');
    state.activeStream = source;
    
    source.onmessage = function (event) {
        const data = JSON.parse(event.data);
        handleStreamEvent(data);
    };
    
    source.onerror = function (err) {
        console.error("SSE stream error", err);
        source.close();
        finishMigration('error');
    };
}

// Process SSE streamed event packet
function handleStreamEvent(data) {
    switch (data.type) {
        case 'thinking_delta':
            updateThinkingLog(data.content);
            break;
            
        case 'text_delta':
            finishThinkingLog();
            if (!state.currentOrchestratorBubble) {
                state.currentOrchestratorBubble = appendChatMessage('system', 'System Orchestrator', '');
            }
            state.currentOrchestratorBubble.innerHTML += parseMarkdown(data.content);
            document.getElementById('chat-messages-container').scrollTop = document.getElementById('chat-messages-container').scrollHeight;
            break;
            
        case 'module_status':
            // Reset active orchestrator text accumulator
            state.currentOrchestratorBubble = null;
            
            const modName = data.module;
            if (!state.modules[modName]) {
                // Initialize default metrics
                const complexity = modName === 'frmCustomer.frm' ? 'Low' : 'High';
                state.modules[modName] = {
                    status: data.status,
                    retryCount: data.retry_count || 0,
                    confidence: null,
                    complexity: complexity,
                    runs: []
                };
            } else {
                state.modules[modName].status = data.status;
                state.modules[modName].retryCount = data.retry_count;
            }
            
            // Map worker chips active state depending on stage status
            if (data.status === 'converting') {
                updateWorkerChips('conversion_worker');
            } else if (data.status === 'validating') {
                updateWorkerChips('build_validate_worker');
            } else if (data.status === 'escalated') {
                updateWorkerChips('qa_review_worker');
                // Trigger alert badge count
                incrementDashboardBadge();
            } else if (data.status === 'done') {
                updateWorkerChips(null);
            }
            
            updateDashboardStats();
            renderDashboardTable();
            break;
            
        case 'build_result':
            const bMod = data.module;
            if (state.modules[bMod]) {
                const retryVal = state.modules[bMod].retryCount;
                // Query default templates matching retry logs from samples if fails
                const mockRunData = getMockRunLogs(bMod, retryVal);
                
                state.modules[bMod].runs.push({
                    retry: retryVal,
                    stage: 'build',
                    status: data.status,
                    build_log: mockRunData.build_log,
                    test_log: mockRunData.test_log,
                    qa_review: mockRunData.qa_review
                });
            }
            break;
            
        case 'test_result':
            const tMod = data.module;
            if (state.modules[tMod]) {
                const runList = state.modules[tMod].runs;
                const activeRun = runList[runList.length - 1];
                if (activeRun) {
                    activeRun.stage = 'test';
                    activeRun.status = data.status;
                }
            }
            break;
            
        case 'diff_report':
            // logs update captured inside module run timelines
            updateWorkerChips('qa_review_worker');
            break;
            
        case 'confidence_score':
            const cMod = data.module;
            if (state.modules[cMod]) {
                state.modules[cMod].confidence = data.score;
            }
            updateDashboardStats();
            renderDashboardTable();
            break;
            
        case 'file_update':
            // Refresh local workspace trees dynamically!
            loadWorkspaceTree().then(() => {
                // If this is the active open file, refresh the code editor viewport!
                if (state.activeFile === data.path) {
                    openFile(data.path);
                }
            });
            break;
            
        case 'done':
            state.activeStream.close();
            finishMigration('done');
            break;
    }
}

// Increment validation alert bubble badge
function incrementDashboardBadge() {
    if (state.activeView === 'dashboard') return;
    const badge = document.getElementById('dashboard-alert-badge');
    badge.style.display = 'inline-block';
    const count = parseInt(badge.textContent || '0') + 1;
    badge.textContent = count;
}

// Get mock log files templates dynamically based on real pipeline state
function getMockRunLogs(moduleName, retryIndex) {
    // Fallback constants
    const defaultVal = {
        build_log: "Build complete successfully.",
        test_log: "xUnit tests run: Passed.",
        qa_review: "QA audit passed."
    };
    
    // Simulate query index matching samples
    if (moduleName.includes("Invoice")) {
        const list = [
            {
                build_log: "CS0246: The type or namespace name 'ICobolInterop' could not be found...",
                test_log: "Tests not run due to build error.",
                qa_review: "### QA Review\n**Compile Error**: Missing interop helper declarations."
            },
            {
                build_log: "Build completed successfully.",
                test_log: "xUnit invoice tests: VAT calculation Assert Mismatch. Expected 1650, got 1500.",
                qa_review: "### QA Review\n**Logic Mismatch**: Rounding and VAT logic missing product operand multiplication."
            },
            {
                build_log: "Build completed successfully.",
                test_log: "xUnit invoice tests: Passed. 1/1 tests successful.",
                qa_review: "### QA Review\n**Passed** on retry 2. Code execution verification completed."
            }
        ];
        return list[retryIndex] || defaultVal;
    }
    if (moduleName.includes("Customer")) {
        return {
            build_log: "Restore done.\nBuild completed: 0 Errors.",
            test_log: "xUnit tests: Test_Load_Customer_Profile: Passed\nTest_Save_Customer_Profile: Passed.",
            qa_review: "### QA Review\n**Passed** on initial attempt."
        };
    }
    if (moduleName.includes("billing")) {
        const list = [
            {
                build_log: "CS0103: REDEFINES_BillingBlock does not exist...",
                test_log: "Tests not run.",
                qa_review: "### QA Review\n**Structure Error**: REDEFINES mapping layout alignment failed."
            },
            {
                build_log: "CS0579: Duplicate 'StructLayout' attribute.",
                test_log: "Tests not run.",
                qa_review: "### QA Review\n**Attribute Error**: Duplicate tags added."
            },
            {
                build_log: "Build Success.",
                test_log: "BillingTests failed: expected numeric precision values mismatch.",
                qa_review: "### QA Review\n**Logic Mismatch**: status checks missed enum check state 'E'."
            },
            {
                build_log: "Build Success.",
                test_log: "BillingTests failed: EBCDIC character set translation signs conversion error.",
                qa_review: "### QA Review\n**Max Retry (3/3) Escalated**: Interop layout parsing failed signs mapping."
            }
        ];
        return list[retryIndex] || defaultVal;
    }
    return defaultVal;
}

// Finalize simulation migration loop run
function finishMigration(status) {
    state.pipelineState = 'idle';
    finishThinkingLog();
    
    const btn = document.getElementById('btn-run-migration');
    btn.disabled = false;
    btn.className = 'chat-action-btn';
    btn.innerHTML = '<i class="fa-solid fa-play"></i> Start';
    
    const badge = document.getElementById('pipeline-status-text');
    if (status === 'done') {
        badge.className = 'pipeline-badge done';
        badge.textContent = 'Complete';
        updateWorkerChips(null);
    } else {
        badge.className = 'pipeline-badge error';
        badge.textContent = 'Stopped';
        updateWorkerChips(null);
    }
}

// Page load event setup
window.addEventListener('DOMContentLoaded', () => {
    initMonaco();
    initResizablePanes();
    loadWorkspaceTree();
    
    // Sidebar btn routing
    document.getElementById('btn-show-explorer').addEventListener('click', () => switchView('editor'));
    document.getElementById('btn-show-dashboard').addEventListener('click', () => switchView('dashboard'));
    
    // Tab header routing
    document.getElementById('tab-editor').addEventListener('click', () => switchView('editor'));
    document.getElementById('tab-dashboard').addEventListener('click', () => switchView('dashboard'));
    
    // Action bar triggers
    document.getElementById('btn-toggle-split').addEventListener('click', () => toggleSplitMode());
    document.getElementById('btn-reset').addEventListener('click', resetWorkspace);
    document.getElementById('welcome-btn-run').addEventListener('click', startMigration);
    document.getElementById('btn-run-migration').addEventListener('click', startMigration);
    document.getElementById('btn-refresh-files').addEventListener('click', loadWorkspaceTree);
    
    // Drawer buttons setup
    document.getElementById('btn-close-drawer').addEventListener('click', () => {
        document.getElementById('detail-drawer').classList.remove('open');
    });
    
    // Drawer tabs navigation triggers
    document.querySelectorAll('.drawer-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.drawer-tab-btn').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.drawer-tab-content').forEach(el => el.classList.remove('active'));
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });
});
