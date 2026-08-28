function switchMainTab(tabId) {
    document.querySelectorAll('.tab-link').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Upload Handling
const dropBox = document.getElementById('dropBox');
const fileInput = document.getElementById('fileInput');

dropBox.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', async () => {
    if (!fileInput.files.length) return;
    const formData = new FormData();
    formData.append('document', fileInput.files[0]);

    dropBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i><span>Generating Embeddings...</span>`;

    try {
        const resp = await fetch('/upload', { method: 'POST', body: formData });
        const data = await resp.json();
        if (data.success) {
            addMaterialToUI(data.material);
            alert(`✅ Successfully indexed "${data.material.filename}" into ${data.material.backend}!`);
        } else {
            alert('Upload error: ' + data.error);
        }
    } catch (err) {
        alert('Upload failed: ' + err.message);
    } finally {
        dropBox.innerHTML = `<i class="fa-solid fa-cloud-arrow-up drop-icon"></i><span>Upload Lecture Notes / PDF</span>`;
        fileInput.value = '';
    }
});

function addMaterialToUI(mat) {
    const emptyMsg = document.getElementById('emptyMsg');
    if (emptyMsg) emptyMsg.remove();

    const matList = document.getElementById('materialList');
    const pill = document.createElement('div');
    pill.className = 'material-pill';
    pill.innerHTML = `
        <i class="fa-solid fa-book-bookmark"></i>
        <div class="material-meta">
            <span class="mat-name">${escapeHtml(mat.filename)}</span>
            <span class="mat-stats">${mat.pages} pgs • ${mat.chunks} vector chunks</span>
        </div>
    `;
    matList.prepend(pill);
}

async function clearMaterials() {
    if (!confirm('Clear all uploaded study materials?')) return;
    try {
        const resp = await fetch('/clear', { method: 'POST' });
        const data = await resp.json();
        if (data.success) {
            document.getElementById('materialList').innerHTML = `
                <div class="empty-msg" id="emptyMsg">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>Upload textbooks or study notes to begin your research session.</p>
                </div>
            `;
        }
    } catch (err) {
        alert('Failed to clear: ' + err.message);
    }
}

// Ask Crew Form
const askForm = document.getElementById('askForm');
const queryInput = document.getElementById('queryInput');
const askBtn = document.getElementById('askBtn');

askForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    askBtn.disabled = true;
    askBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Crew Running...';

    // Show loading state on notes
    document.getElementById('notesEmpty').classList.add('hidden');
    const studyCard = document.getElementById('studyCard');
    studyCard.classList.remove('hidden');
    document.getElementById('studyTitle').innerText = query;
    document.getElementById('studyBody').innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Research Agent gathering evidence, Analysis Agent formulating study notes, Review Agent verifying accuracy...';

    try {
        const resp = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        const data = await resp.json();

        if (data.success) {
            renderStudyResults(data);
        } else {
            alert('Crew Error: ' + (data.error || 'Failed to process question'));
            document.getElementById('studyBody').innerText = 'Error processing request.';
        }
    } catch (err) {
        alert('Network Error: ' + err.message);
    } finally {
        askBtn.disabled = false;
        askBtn.innerHTML = '<i class="fa-solid fa-sparkles"></i> <span>Ask Crew</span>';
    }
});

function renderStudyResults(data) {
    // 1. Render Verified Study Guide
    document.getElementById('studyTitle').innerText = data.query;
    document.getElementById('studyBody').innerText = data.final_answer;

    // 2. Render Flashcards
    const flashcardsGrid = document.getElementById('flashcardsGrid');
    const cards = data.flashcards || [];
    document.getElementById('flashcardCount').innerText = cards.length;

    if (cards.length > 0) {
        flashcardsGrid.innerHTML = cards.map((c, i) => `
            <div class="flashcard-wrapper" onclick="this.classList.toggle('flipped')">
                <div class="flashcard-inner">
                    <div class="card-front">
                        <span class="card-type">Card #${i+1} • Click to Flip</span>
                        <h4>${escapeHtml(c.front)}</h4>
                    </div>
                    <div class="card-back">
                        <p>${escapeHtml(c.back)}</p>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // 3. Render CrewAI Execution Timeline
    const timeline = document.getElementById('crewTimeline');
    const trace = data.trace || [];
    if (trace.length > 0) {
        timeline.innerHTML = trace.map(t => `
            <div class="crew-step-card">
                <div class="crew-step-header">
                    <div class="agent-badge-icon"><i class="fa-solid fa-robot"></i></div>
                    <div>
                        <h4>Step ${t.step}: ${escapeHtml(t.agent)}</h4>
                        <span class="agent-role-tag">${escapeHtml(t.role)} — ${escapeHtml(t.goal)}</span>
                    </div>
                </div>
                <div class="crew-output-box">${escapeHtml(t.output)}</div>
            </div>
        `).join('');
    }
}

function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
