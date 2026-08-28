function fillScenario(text) {
    document.getElementById('requestText').value = text;
}

function updateEmployeeDetails() {
    // Optional helper when switching employee dropdown
}

document.getElementById('ticketForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const reqText = document.getElementById('requestText').value.trim();
    if (!reqText) return alert('Please enter an IT issue description.');

    const empSelect = document.getElementById('employeeSelect');
    const selectedOption = empSelect.options[empSelect.selectedIndex];
    const empEmail = empSelect.value;
    const empName = selectedOption.dataset.name;

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Executing Multi-Agent Pipeline...';

    const pipelineStatus = document.getElementById('pipelineStatus');
    pipelineStatus.className = 'badge-waiting running';
    pipelineStatus.innerText = 'Running Pipeline';

    // Reset pipeline visual states
    document.getElementById('finalOutcome').classList.add('hidden');
    for (let i = 1; i <= 5; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        stepEl.className = 'agent-step';
        stepEl.querySelector('.step-status').innerText = 'Pending';
        const outEl = document.getElementById(`out-${i}`);
        outEl.classList.add('hidden');
        outEl.innerHTML = '';
    }

    // Step 1 Active animation
    setStepActive(1, 'Analyzing & Classifying...');

    try {
        const resp = await fetch('/submit_ticket', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_text: reqText,
                employee_email: empEmail,
                employee_name: empName
            })
        });

        const data = await resp.json();
        if (!data.success) {
            alert('Workflow Error: ' + data.error);
            resetSubmitBtn();
            return;
        }

        // Animate sequential step outputs smoothly
        await animatePipelineTrace(data);

    } catch (err) {
        alert('Network Error: ' + err.message);
        resetSubmitBtn();
    }
});

function setStepActive(stepNum, statusText) {
    const stepEl = document.getElementById(`step-${stepNum}`);
    stepEl.className = 'agent-step active';
    stepEl.querySelector('.step-status').innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${statusText}`;
}

function setStepDone(stepNum, outputHtml) {
    const stepEl = document.getElementById(`step-${stepNum}`);
    stepEl.className = 'agent-step done';
    stepEl.querySelector('.step-status').innerHTML = '<i class="fa-solid fa-check"></i> Complete';
    const outEl = document.getElementById(`out-${stepNum}`);
    outEl.innerHTML = outputHtml;
    outEl.classList.remove('hidden');
}

async function animatePipelineTrace(data) {
    const trace = data.trace;
    const delay = (ms) => new Promise(r => setTimeout(r, ms));

    for (let i = 0; i < trace.length; i++) {
        const item = trace[i];
        const stepNum = item.step;
        setStepActive(stepNum, 'Processing...');
        await delay(500);

        let contentHtml = '';
        if (stepNum === 1) {
            // Manager Agent
            contentHtml = `<strong>Category:</strong> ${item.data.category} | <strong>Urgency:</strong> ${item.data.urgency}<br><strong>Summary:</strong> ${item.data.summary}`;
        } else if (stepNum === 2) {
            // Troubleshooting Agent
            contentHtml = `<strong>Hypothesis:</strong> ${item.data.hypothesis}<br><strong>Diagnostic Steps:</strong><br>${item.data.diagnostic_steps}`;
        } else if (stepNum === 3) {
            // Knowledge Agent
            contentHtml = `<strong>Matched SOP:</strong> ${item.data.article_title} (Type: ${item.data.solution_type})<br><strong>Procedure:</strong><br>${item.data.standard_procedure}`;
        } else if (stepNum === 4) {
            // Database Agent
            const emp = item.data.employee || {};
            const dev = item.data.device || {};
            contentHtml = `<strong>Verified Employee:</strong> ${emp.name} (${emp.role})<br><strong>Device:</strong> ${dev.hostname} (${dev.os_version}) | IP: ${dev.ip_address} | VPN State: ${dev.vpn_status}`;
        } else if (stepNum === 5) {
            // Response Agent
            const isSolved = item.data.problem_solved;
            contentHtml = `<strong>Decision:</strong> ${item.data.decision}<br><strong>Ticket Outcome:</strong> ${item.data.ticket_status} (${item.data.assigned_tier})`;
        }

        setStepDone(stepNum, contentHtml);
        await delay(300);
    }

    // Show Final Outcome
    const outcomeCard = document.getElementById('finalOutcome');
    outcomeCard.classList.remove('hidden');
    document.getElementById('ticketNumberBadge').innerText = data.ticket_number;

    const decisionBadge = document.getElementById('decisionBadge');
    if (data.problem_solved) {
        decisionBadge.className = 'decision-badge resolved';
        decisionBadge.innerHTML = '<i class="fa-solid fa-circle-check"></i> RESOLVED & CLOSED';
    } else {
        decisionBadge.className = 'decision-badge escalated';
        decisionBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ESCALATED TO HUMAN ENGINEER';
    }

    document.getElementById('finalResponseText').innerText = data.final_response;

    const pipelineStatus = document.getElementById('pipelineStatus');
    pipelineStatus.className = 'badge-waiting';
    pipelineStatus.innerText = 'Completed';

    resetSubmitBtn();
    outcomeCard.scrollIntoView({ behavior: 'smooth' });
}

function resetSubmitBtn() {
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run 5-Agent Multi-Agent Workflow';
}
