let currentMode = 'hybrid';
let activeSources = [];

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.mode === mode);
    });
}

// Upload Handling
const dropBox = document.getElementById('dropBox');
const fileInput = document.getElementById('fileInput');

dropBox.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', async () => {
    if (!fileInput.files.length) return;
    const formData = new FormData();
    formData.append('document', fileInput.files[0]);

    dropBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Indexing Document...</span>`;

    try {
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.success) {
            addDocumentToUI(data.file);
            appendAssistantMessage(`Successfully processed and indexed **${data.file.filename}** (${data.file.pages} pages, ${data.file.chunks} vector chunks). You can now ask questions about it!`);
        } else {
            alert('Upload error: ' + data.error);
        }
    } catch (err) {
        alert('Upload failed: ' + err.message);
    } finally {
        dropBox.innerHTML = `<i class="fa-solid fa-file-arrow-up drop-icon"></i><span>Upload PDF Documents</span>`;
        fileInput.value = '';
    }
});

function addDocumentToUI(file) {
    const emptyDocs = document.getElementById('emptyDocs');
    if (emptyDocs) emptyDocs.remove();

    const docList = document.getElementById('docList');
    const pill = document.createElement('div');
    pill.className = 'doc-pill';
    pill.innerHTML = `
        <i class="fa-solid fa-file-pdf"></i>
        <div class="doc-meta">
            <span class="doc-name">${escapeHtml(file.filename)}</span>
            <span class="doc-stats">${file.pages} pages • ${file.chunks} chunks</span>
        </div>
    `;
    docList.prepend(pill);
}

async function clearDocuments() {
    if (!confirm('Clear all indexed documents and vector index?')) return;
    try {
        const resp = await fetch('/clear', { method: 'POST' });
        const data = await resp.json();
        if (data.success) {
            document.getElementById('docList').innerHTML = `
                <div class="empty-docs" id="emptyDocs">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>No documents uploaded yet. Upload PDFs to ground AI answers.</p>
                </div>
            `;
            appendAssistantMessage("Knowledge base has been cleared.");
        }
    } catch (err) {
        alert('Failed to clear: ' + err.message);
    }
}

// Chat Form
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const chatFeed = document.getElementById('chatFeed');

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = messageInput.value.trim();
    if (!query) return;

    messageInput.value = '';
    appendUserMessage(query);

    const loadingBubble = appendLoadingBubble();

    try {
        const resp = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: query, mode: currentMode })
        });
        const data = await resp.json();
        loadingBubble.remove();

        if (data.success) {
            appendAssistantMessage(data.answer, data.sources);
        } else {
            appendAssistantMessage('❌ Error: ' + (data.error || 'Failed to get answer'));
        }
    } catch (err) {
        loadingBubble.remove();
        appendAssistantMessage('❌ Network error: ' + err.message);
    }
});

function appendUserMessage(text) {
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble user';
    bubble.innerHTML = `
        <div class="bubble-avatar"><i class="fa-solid fa-user"></i></div>
        <div class="bubble-content"><p>${escapeHtml(text)}</p></div>
    `;
    chatFeed.appendChild(bubble);
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

function appendAssistantMessage(text, sources = []) {
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble assistant';
    
    let sourcesBadgeHtml = '';
    if (sources && sources.length > 0) {
        const sourceIndex = activeSources.length;
        activeSources.push(sources);
        sourcesBadgeHtml = `
            <button type="button" class="sources-badge" onclick="showSources(${sourceIndex})">
                <i class="fa-solid fa-book-bookmark"></i> ${sources.length} Source Citations
            </button>
        `;
    }

    bubble.innerHTML = `
        <div class="bubble-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="bubble-content">
            <div class="text-body">${formatMarkdown(text)}</div>
            ${sourcesBadgeHtml}
        </div>
    `;
    chatFeed.appendChild(bubble);
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

function appendLoadingBubble() {
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble assistant';
    bubble.innerHTML = `
        <div class="bubble-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="bubble-content">
            <i class="fa-solid fa-circle-notch fa-spin"></i> Retrieving embeddings and generating response...
        </div>
    `;
    chatFeed.appendChild(bubble);
    chatFeed.scrollTop = chatFeed.scrollHeight;
    return bubble;
}

function showSources(index) {
    const sources = activeSources[index];
    if (!sources) return;

    const listEl = document.getElementById('modalSourcesList');
    listEl.innerHTML = sources.map((s, idx) => `
        <div class="source-item">
            <div class="source-item-meta">
                <span><i class="fa-solid fa-file-pdf"></i> ${escapeHtml(s.source)} (Page ${s.page})</span>
                <span>Score: ${Math.round(s.score * 100)}%</span>
            </div>
            <p>${escapeHtml(s.preview)}</p>
        </div>
    `).join('');

    document.getElementById('sourcesModal').classList.remove('hidden');
}

function closeModal(e) {
    document.getElementById('sourcesModal').classList.add('hidden');
}

function formatMarkdown(text) {
    // Basic Markdown formatting helper
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
    formatted = formatted.replace(/\n\n/g, '<br><br>');
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
