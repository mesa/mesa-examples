/* ===========================================================
   Emergent Firms – Dashboard JS
   Chart.js for time-series, D3.js for network visualisations
   =========================================================== */

// ---------- State ----------
let currentStep = 0;
let firmOutputHistory = [];   // [{step, output}] for selected firm
let selectedFirmId = null;
let selectedAgentId = null;
let agentListPopulated = false;
let running = false;
let latestFirms = [];  // cache for badge updates on dropdown change
let userPickedFirm = false;   // true when the user manually picks a firm from the dropdown

// Firm-level history is now provided by the server (full life of each firm)

// ---------- DOM refs ----------
const $ = (sel) => document.querySelector(sel);
const stepDisplay   = $('#stepDisplay');
const statusMsg     = $('#statusMsg');
const btnInit       = $('#btnInit');
const btnReset      = $('#btnReset');
const btnStep       = $('#btnStep');
const firmSelect    = $('#firmSelect');
const agentSelect   = $('#agentSelect');
const tooltip       = $('#tooltip');
const btnRun        = $('#btnRun');

// ---------- Helpers ----------
function getParams() {
    return {
        rng:          parseInt($('#p-seed').value)       || 42,
        num_agents:   parseInt($('#p-agents').value)     || 1000,
        a:            parseFloat($('#p-a').value)        || 1.0,
        b:            parseFloat($('#p-b').value)        || 1.0,
        beta:         parseFloat($('#p-beta').value)     || 2.0,
        num_friends:  parseInt($('#p-friends').value)    || 2,
        make_friends: $('#p-makefriends').checked,
    };
}

async function api(path, body = null) {
    const opts = body !== null
        ? { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }
        : { method: body === null && !path.startsWith('/api/') ? 'GET' : 'GET' };
    if (body !== null) { opts.method = 'POST'; }
    const res = await fetch(path, opts);
    return res.json();
}

function status(msg) { statusMsg.textContent = msg; }

// ============================================================
//  Chart.js  –  Model-level time series
// ============================================================

const chartOpts = (yLabel) => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 },
    scales: {
        x: { title: { display: true, text: 'Step', color: '#8b8fa5' },
             ticks: { color: '#8b8fa5' }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { title: { display: true, text: yLabel, color: '#8b8fa5' },
             ticks: { color: '#8b8fa5' }, grid: { color: 'rgba(255,255,255,0.04)' } },
    },
    plugins: { legend: { labels: { color: '#e4e6ed', boxWidth: 12 } } },
});

function makeChart(canvasId, datasets, yLabel = '') {
    return new Chart(document.getElementById(canvasId), {
        type: 'line',
        data: { labels: [], datasets },
        options: chartOpts(yLabel),
    });
}

// Model charts
const chartFirmCount = makeChart('chartFirmCount',
    [{ label: 'Firms', data: [], borderColor: '#6c8cff', backgroundColor: 'rgba(108,140,255,0.1)', fill: true, tension: 0.3, pointRadius: 0 }], 'Count');

const chartFirmSize = makeChart('chartFirmSize', [
    { label: 'Average', data: [], borderColor: '#6c8cff', tension: 0.3, pointRadius: 0 },
    { label: 'Largest', data: [], borderColor: '#fb923c', tension: 0.3, pointRadius: 0 },
], 'Workers');

const chartOutput = makeChart('chartOutput', [
    { label: 'Total', data: [], borderColor: '#34d399', tension: 0.3, pointRadius: 0 },
    { label: 'Largest Firm', data: [], borderColor: '#fb923c', tension: 0.3, pointRadius: 0 },
], 'Output');

const chartEffort = makeChart('chartEffort', [
    { label: 'Total', data: [], borderColor: '#a78bfa', tension: 0.3, pointRadius: 0 },
    { label: 'Largest Firm', data: [], borderColor: '#fb923c', tension: 0.3, pointRadius: 0 },
], 'Effort');

// Firm detail chart – Output on left axis, Free Riders + Avg Effort on right
const chartFirmOutput = new Chart(document.getElementById('chartFirmOutput'), {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            { label: 'Output', data: [], borderColor: '#fb923c', backgroundColor: 'rgba(251,146,60,0.1)', fill: true, tension: 0.3, pointRadius: 0, yAxisID: 'y' },
            { label: 'Free Riders', data: [], borderColor: '#f87171', borderDash: [5, 3], tension: 0.3, pointRadius: 0, yAxisID: 'y1' },
            { label: 'Avg Effort', data: [], borderColor: '#38bdf8', tension: 0.3, pointRadius: 0, yAxisID: 'y2' },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
            x: { title: { display: true, text: 'Step', color: '#8b8fa5' },
                 ticks: { color: '#8b8fa5' }, grid: { color: 'rgba(255,255,255,0.04)' } },
            y:  { position: 'left', title: { display: true, text: 'Output', color: '#fb923c' },
                 ticks: { color: '#fb923c' }, grid: { color: 'rgba(255,255,255,0.04)' } },
            y1: { position: 'right', title: { display: true, text: 'Free Riders', color: '#f87171' },
                 ticks: { color: '#f87171' }, grid: { drawOnChartArea: false } },
            y2: { position: 'right', title: { display: true, text: 'Avg Effort', color: '#38bdf8' },
                 ticks: { color: '#38bdf8' }, grid: { drawOnChartArea: false },
                 min: 0, max: 1 },
        },
        plugins: { legend: { labels: { color: '#e4e6ed', boxWidth: 12 } } },
    },
});

// Agent detail chart
const chartAgentHistory = makeChart('chartAgentHistory', [
    { label: 'Effort', data: [], borderColor: '#6c8cff', tension: 0.3, pointRadius: 0 },
    { label: 'Income', data: [], borderColor: '#34d399', tension: 0.3, pointRadius: 0 },
], 'Value');


function updateModelCharts(ts) {
    const labels = ts['Number of Firms'].map((_, i) => i);
    chartFirmCount.data.labels = labels;
    chartFirmCount.data.datasets[0].data = ts['Number of Firms'];
    chartFirmCount.update();

    chartFirmSize.data.labels = labels;
    chartFirmSize.data.datasets[0].data = ts['Average Firm Size'];
    chartFirmSize.data.datasets[1].data = ts['Largest Firm Size'];
    chartFirmSize.update();

    chartOutput.data.labels = labels;
    chartOutput.data.datasets[0].data = ts['Total Output'];
    chartOutput.data.datasets[1].data = ts['Output Largest Firm'];
    chartOutput.update();

    chartEffort.data.labels = labels;
    chartEffort.data.datasets[0].data = ts['Total Effort'];
    chartEffort.data.datasets[1].data = ts['Total Effort Largest Firm'];
    chartEffort.update();
}

// ============================================================
//  Firm dropdown & view
// ============================================================

/** Composite score: rewards both size and longevity. */
function firmScore(f) {
    return f.size * Math.log2((f.age || 0) + 2);
}

function populateFirmSelect(firms) {
    // Score and sort — most interesting firms at the top
    const scored = firms.map(f => ({ ...f, score: firmScore(f) }));
    scored.sort((a, b) => b.score - a.score);

    // Remember current selection for sticky behaviour
    const prevId = selectedFirmId;
    const prevStillExists = prevId != null && scored.some(f => f.id === prevId);

    firmSelect.innerHTML = '';
    scored.forEach((f, idx) => {
        const opt = document.createElement('option');
        opt.value = String(f.id);
        opt.textContent = `#${idx + 1}  Firm ${f.id}  (${f.size} wkrs, age ${f.age}, score ${f.score.toFixed(1)})`;
        firmSelect.appendChild(opt);
    });

    // Sticky selection: keep the current firm if it still exists
    if (prevStillExists) {
        firmSelect.value = String(prevId);
    } else if (scored.length > 0) {
        // Current firm dissolved — auto-pick the top-scored firm
        firmSelect.value = String(scored[0].id);
        userPickedFirm = false;
    }
    updateFirmBadge(scored);
}

function updateFirmBadge(firms) {
    const badge = document.getElementById('firmBadge');
    const selId = parseInt(firmSelect.value);
    const f = firms.find(x => x.id === selId);
    if (f) {
        const score = f.score != null ? f.score : firmScore(f);
        badge.textContent = `Firm ${f.id}  ·  ${f.size} workers  ·  age ${f.age}  ·  score ${score.toFixed(1)}`;
    } else {
        badge.textContent = 'Firm –';
    }
}

function renderFirmStats(data) {
    const container = $('#firmStats');
    const freeRiders = (data.workers || []).filter(w => w.effort < 0.01).length;
    const efforts = (data.workers || []).map(w => w.effort);
    const avgEffort = efforts.length > 0 ? (efforts.reduce((a, b) => a + b, 0) / efforts.length) : 0;
    container.innerHTML = `
        <div class="stat-chip"><span class="stat-value">${data.size}</span><span class="stat-label">Workers</span></div>
        <div class="stat-chip"><span class="stat-value">${data.output.toFixed(2)}</span><span class="stat-label">Output</span></div>
        <div class="stat-chip"><span class="stat-value">${data.age}</span><span class="stat-label">Age</span></div>
        <div class="stat-chip"><span class="stat-value">${freeRiders}</span><span class="stat-label">Free Riders</span></div>
        <div class="stat-chip"><span class="stat-value">${avgEffort.toFixed(3)}</span><span class="stat-label">Avg Effort</span></div>
        <div class="stat-chip"><span class="stat-value">${data.internal_edges.length}</span><span class="stat-label">Internal Edges</span></div>
    `;
}

function updateFirmOutputChart(history) {
    const steps = history.step || [];
    chartFirmOutput.data.labels = steps;
    chartFirmOutput.data.datasets[0].data = history.output || [];
    chartFirmOutput.data.datasets[1].data = history.free_riders || [];
    chartFirmOutput.data.datasets[2].data = history.avg_effort || [];
    chartFirmOutput.update();
}

async function loadFirmView(firmId) {
    if (firmId == null) return;
    selectedFirmId = firmId;
    const data = await api(`/api/firm/${firmId}`);
    if (data.error) { status(data.error); return; }
    renderFirmStats(data);
    updateFirmOutputChart(data.history || {});
    drawEulerDiagram(data);
}

// ============================================================
//  Agent dropdown & view
// ============================================================

function populateAgentSelect(count) {
    if (agentListPopulated) return;
    agentSelect.innerHTML = '';
    // We'll populate on first data fetch – agents have IDs starting from 1
    // The actual IDs come from the model, but we'll defer to loadAgentView
    agentListPopulated = true;
}

function renderAgentStats(data) {
    const container = $('#agentStats');
    container.innerHTML = `
        <div class="stat-chip"><span class="stat-value">${data.effort.toFixed(3)}</span><span class="stat-label">Effort</span></div>
        <div class="stat-chip"><span class="stat-value">${data.income.toFixed(3)}</span><span class="stat-label">Income</span></div>
        <div class="stat-chip"><span class="stat-value">${data.utility.toFixed(3)}</span><span class="stat-label">Utility</span></div>
        <div class="stat-chip"><span class="stat-value">θ=${data.theta.toFixed(3)}</span><span class="stat-label">Theta</span></div>
        <div class="stat-chip"><span class="stat-value">${data.firm_id ?? '–'}</span><span class="stat-label">Firm</span></div>
        <div class="stat-chip"><span class="stat-value">${data.num_friends}</span><span class="stat-label">Friends</span></div>
    `;
}

function updateAgentChart(history) {
    const labels = history.effort.map((_, i) => i);
    chartAgentHistory.data.labels = labels;
    chartAgentHistory.data.datasets[0].data = history.effort;
    chartAgentHistory.data.datasets[1].data = history.income;
    chartAgentHistory.update();
}

async function loadAgentView(agentId) {
    if (agentId == null) return;
    selectedAgentId = agentId;
    const data = await api(`/api/agent/${agentId}`);
    if (data.error) { status(data.error); return; }
    renderAgentStats(data);
    updateAgentChart(data.history);
    drawFriendsNetwork(data);
}

// ============================================================
//  D3 – Euler Diagram  (Firm workers in a bounding ellipse)
// ============================================================

function drawEulerDiagram(firmData) {
    const container = document.getElementById('eulerContainer');
    container.innerHTML = '';
    const rect = container.getBoundingClientRect();
    const W = rect.width || 400;
    const H = Math.max(rect.height, 340);

    const svg = d3.select(container).append('svg')
        .attr('width', W).attr('height', H)
        .attr('viewBox', `0 0 ${W} ${H}`);

    const cx = W / 2, cy = H / 2;
    const rx = W * 0.42, ry = H * 0.42;
    const workers = firmData.workers || [];
    const edges = firmData.internal_edges || [];

    // Bounding ellipse
    svg.append('ellipse')
        .attr('cx', cx).attr('cy', cy).attr('rx', rx).attr('ry', ry)
        .attr('class', 'euler-boundary');

    // Firm label
    svg.append('text')
        .attr('x', cx).attr('y', cy - ry - 8)
        .attr('text-anchor', 'middle')
        .attr('class', 'euler-label')
        .text(`Firm ${firmData.id}  ·  ${workers.length} workers  ·  output ${firmData.output.toFixed(1)}`);

    if (workers.length === 0) return;

    // Lay out worker nodes inside the ellipse using force simulation
    const nodes = workers.map((w, i) => ({
        ...w,
        x: cx + (Math.random() - 0.5) * rx,
        y: cy + (Math.random() - 0.5) * ry,
    }));
    const idMap = new Map(nodes.map((n, i) => [n.id, i]));

    const links = edges
        .filter(e => idMap.has(e.source) && idMap.has(e.target))
        .map(e => ({ source: idMap.get(e.source), target: idMap.get(e.target) }));

    // Run a quick force simulation
    const sim = d3.forceSimulation(nodes)
        .force('charge', d3.forceManyBody().strength(-30))
        .force('center', d3.forceCenter(cx, cy))
        .force('collision', d3.forceCollide(8))
        .force('link', d3.forceLink(links).distance(40).strength(0.3))
        .force('ellipse', () => {
            nodes.forEach(n => {
                const dx = n.x - cx, dy = n.y - cy;
                const dist = (dx * dx) / (rx * rx * 0.85) + (dy * dy) / (ry * ry * 0.85);
                if (dist > 1) { n.x = cx + dx / Math.sqrt(dist); n.y = cy + dy / Math.sqrt(dist); }
            });
        })
        .stop();

    for (let i = 0; i < 120; i++) sim.tick();

    // Draw edges
    svg.selectAll('.link-internal')
        .data(links).enter().append('line')
        .attr('class', 'link-internal')
        .attr('x1', d => nodes[d.source.index ?? d.source].x)
        .attr('y1', d => nodes[d.source.index ?? d.source].y)
        .attr('x2', d => nodes[d.target.index ?? d.target].x)
        .attr('y2', d => nodes[d.target.index ?? d.target].y);

    // Draw nodes
    const nodeG = svg.selectAll('.worker-node')
        .data(nodes).enter().append('g')
        .attr('transform', d => `translate(${d.x},${d.y})`);

    const nodeRadius = Math.max(4, Math.min(10, 120 / Math.sqrt(workers.length)));

    nodeG.append('circle')
        .attr('r', nodeRadius)
        .attr('class', 'node-worker')
        .on('mouseover', (ev, d) => {
            tooltip.style.display = 'block';
            tooltip.innerHTML = `Worker ${d.id}<br>effort: ${d.effort}<br>income: ${d.income}<br>θ: ${d.theta}`;
        })
        .on('mousemove', (ev) => {
            tooltip.style.left = ev.pageX + 10 + 'px';
            tooltip.style.top = ev.pageY - 28 + 'px';
        })
        .on('mouseout', () => { tooltip.style.display = 'none'; });

    // Labels for small firms
    if (workers.length <= 30) {
        nodeG.append('text')
            .attr('dy', nodeRadius + 12).attr('text-anchor', 'middle')
            .attr('class', 'node-label')
            .text(d => d.id);
    }
}

// ============================================================
//  D3 – Friends Force Graph  (Agent ego network)
// ============================================================

function drawFriendsNetwork(agentData) {
    const container = document.getElementById('friendsContainer');
    container.innerHTML = '';
    const rect = container.getBoundingClientRect();
    const W = rect.width || 400;
    const H = Math.max(rect.height, 340);

    const svg = d3.select(container).append('svg')
        .attr('width', W).attr('height', H)
        .attr('viewBox', `0 0 ${W} ${H}`);

    const cx = W / 2, cy = H / 2;
    const friends = agentData.friends || [];
    const edges = agentData.edges || [];

    // Build unique firm IDs for color coding
    const firmIds = [...new Set(friends.map(f => f.firm_id).filter(x => x != null))];
    const colorScale = d3.scaleOrdinal(d3.schemeTableau10).domain(firmIds);

    // Nodes: self + friends
    const nodes = [
        { id: agentData.id, label: `You (${agentData.id})`, isSelf: true, firm_id: agentData.firm_id },
        ...friends.map(f => ({ id: f.id, label: `${f.id}`, isSelf: false, firm_id: f.firm_id, same_firm: f.same_firm })),
    ];
    const idMap = new Map(nodes.map((n, i) => [n.id, i]));

    const links = edges
        .filter(e => idMap.has(e.source) && idMap.has(e.target))
        .map(e => ({ source: idMap.get(e.source), target: idMap.get(e.target) }));

    // Force simulation
    const sim = d3.forceSimulation(nodes)
        .force('charge', d3.forceManyBody().strength(-120))
        .force('center', d3.forceCenter(cx, cy))
        .force('collision', d3.forceCollide(22))
        .force('link', d3.forceLink(links).distance(90).strength(0.6))
        .stop();

    for (let i = 0; i < 100; i++) sim.tick();

    // Clamp positions
    nodes.forEach(n => {
        n.x = Math.max(20, Math.min(W - 20, n.x));
        n.y = Math.max(20, Math.min(H - 20, n.y));
    });

    // Draw edges
    svg.selectAll('.link-friend')
        .data(links).enter().append('line')
        .attr('class', 'link-friend')
        .attr('x1', d => nodes[d.source.index ?? d.source].x)
        .attr('y1', d => nodes[d.source.index ?? d.source].y)
        .attr('x2', d => nodes[d.target.index ?? d.target].x)
        .attr('y2', d => nodes[d.target.index ?? d.target].y);

    // Draw nodes
    const nodeG = svg.selectAll('.friend-node')
        .data(nodes).enter().append('g')
        .attr('transform', d => `translate(${d.x},${d.y})`);

    nodeG.append('circle')
        .attr('r', d => d.isSelf ? 14 : 10)
        .attr('class', d => d.isSelf ? 'node-self' : 'node-worker')
        .style('fill', d => {
            if (d.isSelf) return '#34d399';
            return d.firm_id != null ? colorScale(d.firm_id) : '#555';
        })
        .on('mouseover', (ev, d) => {
            tooltip.style.display = 'block';
            tooltip.innerHTML = `Worker ${d.id}<br>firm: ${d.firm_id ?? 'none'}${d.same_firm ? ' (same)' : ''}`;
        })
        .on('mousemove', (ev) => {
            tooltip.style.left = ev.pageX + 10 + 'px';
            tooltip.style.top = ev.pageY - 28 + 'px';
        })
        .on('mouseout', () => { tooltip.style.display = 'none'; });

    // Labels
    nodeG.append('text')
        .attr('dy', d => (d.isSelf ? 14 : 10) + 14)
        .attr('text-anchor', 'middle')
        .attr('class', 'node-label')
        .style('font-size', d => d.isSelf ? '11px' : '9px')
        .text(d => d.label);
}


// ============================================================
//  Wiring
// ============================================================

// Tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-' + btn.dataset.tab).classList.add('active');

        // Load detail view data on tab switch
        if (btn.dataset.tab === 'firm' && selectedFirmId != null) loadFirmView(selectedFirmId);
        if (btn.dataset.tab === 'agent' && selectedAgentId != null) loadAgentView(selectedAgentId);
    });
});

// Firm select — user manually picks a firm to view (sticky)
firmSelect.addEventListener('change', () => {
    const id = parseInt(firmSelect.value);
    if (!isNaN(id)) {
        userPickedFirm = true;
        selectedFirmId = id;
        updateFirmBadge(latestFirms);
        loadFirmView(id);
    }
});

// Agent select
agentSelect.addEventListener('change', () => {
    const id = parseInt(agentSelect.value);
    if (!isNaN(id)) loadAgentView(id);
});

// Common handler after init/step
async function handleSnapshot(snap) {
    currentStep = snap.step;
    stepDisplay.textContent = `Step: ${currentStep}`;
    updateModelCharts(snap.timeseries);

    // Firm dropdown — scored + sticky selection
    latestFirms = snap.firms;
    populateFirmSelect(snap.firms);
    selectedFirmId = parseInt(firmSelect.value) || null;

    // Agent dropdown (first time only — workers never change)
    if (agentSelect.options.length <= 1 || agentSelect.options[0].value === '') {
        agentSelect.innerHTML = '';
        const workerIds = snap.worker_ids || [];
        workerIds.forEach((id, idx) => {
            const opt = document.createElement('option');
            opt.value = id;
            opt.textContent = `Worker ${idx + 1}  (id ${id})`;
            agentSelect.appendChild(opt);
        });
        if (workerIds.length > 0) {
            selectedAgentId = workerIds[0];
            agentSelect.value = selectedAgentId;
        }
    }

    // If firm or agent tab is active, refresh it
    const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab;
    if (activeTab === 'firm' && selectedFirmId != null) loadFirmView(selectedFirmId);
    if (activeTab === 'agent' && selectedAgentId != null) loadAgentView(selectedAgentId);
}


// Init
btnInit.addEventListener('click', async () => {
    status('Initializing model...');
    btnInit.disabled = true;
    userPickedFirm = false;
    selectedFirmId = null;
    agentListPopulated = false;
    agentSelect.innerHTML = '<option value="">loading...</option>';
    try {
        const snap = await api('/api/init', getParams());
        if (snap.error) { status('Error: ' + snap.error); return; }
        await handleSnapshot(snap);
        status(`Model initialized – ${snap.firms.length} firms`);
    } finally { btnInit.disabled = false; }
});

// Step
btnStep.addEventListener('click', async () => {
    const n = parseInt($('#stepCount').value) || 1;
    status(`Stepping ${n}...`);
    btnStep.disabled = true;
    try {
        const snap = await api('/api/step', { steps: n });
        if (snap.error) { status('Error: ' + snap.error); return; }
        await handleSnapshot(snap);
        status(`Step ${snap.step} – ${snap.firms.length} firms`);
    } finally { btnStep.disabled = false; }
});

// Reset
btnReset.addEventListener('click', async () => {
    running = false;
    btnRun.textContent = '\u25b6 Run';
    btnRun.classList.remove('running');
    status('Resetting...');
    userPickedFirm = false;
    selectedFirmId = null;
    const snap = await api('/api/reset', {});
    if (snap.error) { status('Error: ' + snap.error); return; }
    agentListPopulated = false;
    agentSelect.innerHTML = '<option value="">loading...</option>';
    await handleSnapshot(snap);
    status('Model reset');
});

// Run / Stop toggle
btnRun.addEventListener('click', () => {
    if (running) {
        running = false;
        btnRun.textContent = '\u25b6 Run';
        btnRun.classList.remove('running');
        status(`Stopped at step ${currentStep}`);
    } else {
        running = true;
        btnRun.textContent = '\u25a0 Stop';
        btnRun.classList.add('running');
        runLoop();
    }
});

async function runLoop() {
    while (running) {
        const n = parseInt($('#stepCount').value) || 1;
        try {
            const snap = await api('/api/step', { steps: n });
            if (snap.error) { running = false; status('Error: ' + snap.error); break; }
            await handleSnapshot(snap);
            status(`Running – step ${snap.step} – ${snap.firms.length} firms`);
        } catch (e) {
            running = false;
            status('Error: ' + e.message);
            break;
        }
        // Small breathing room for the UI to repaint
        await new Promise(r => setTimeout(r, 50));
    }
    btnRun.textContent = '\u25b6 Run';
    btnRun.classList.remove('running');
}
