/* ===========================================================
   Emergent Firms – Dashboard JS
   Chart.js for time-series, D3.js for Rank Clock & networks
   =========================================================== */

// ---------- State ----------
let currentStep = 0;
let rankClockMetric = 'size';   // 'size' | 'output'
let rankClockTopN = 25;         // 10 | 25 | 50 | 100
let pinnedFirmId = null;        // locked firm ID in Rank Clock, or null
let hoveredFirmId = null;       // hovered firm ID in Rank Clock, or null
let rankClockData = null;       // cached /api/rank_clock payload (incrementally maintained)
let rcFirmMap = new Map();      // firmId -> firm trajectory object in rankClockData.firms
let rcPrevRank1Id = null;       // tracks Rank #1 ID for incremental turnover counting
let lastAuxDomSyncMs = 0;       // throttles leaderboard/select DOM rebuilds during live Run
let selectedAgentId = null;
let loadedAgentViewStep = -1;   // step at which selectedAgentId's chart is synced
let loadedAgentViewId = null;
let agentListPopulated = false;
let running = false;

// Offscreen & display Canvas state for Rank Clock
let rcDisplayCanvas = null;
let rcBaseCanvas = null;
let rcGeom = null;              // { W, H, dpr, cx, cy, innerR, outerR, topN, maxStep }

// ---------- DOM refs ----------
const $ = (sel) => document.querySelector(sel);
const stepDisplay        = $('#stepDisplay');
const statusMsg          = $('#statusMsg');
const btnInit            = $('#btnInit');
const btnReset           = $('#btnReset');
const btnStep            = $('#btnStep');
const stepsPerTickSelect = $('#p-steps-per-tick');
const rcMetricToggle     = $('#rcMetricToggle');
const rcTopN             = $('#rcTopN');
const rcFirmFilter       = $('#rcFirmFilter');
const rcClearFocus       = $('#rcClearFocus');
const rankClockContainer = $('#rankClockContainer');
const rcLeaderboard      = $('#rcLeaderboard');
const rcFirmCountBadge   = $('#rcFirmCountBadge');
const rcSubtitle         = $('#rcSubtitle');
const agentSelect        = $('#agentSelect');
const tooltip            = $('#tooltip');
const btnRun             = $('#btnRun');
const btnEnd             = $('#btnEnd');
const btnBackToSim       = $('#btnBackToSim');
const resultsPage        = $('#resultsPage');

const MAX_STEP = 1000;

// ---------- Helpers ----------
function getParams() {
    return {
        rng:          parseInt($('#p-seed').value)        || 42,
        num_agents:   parseInt($('#p-agents').value)      || 1000,
        a:            parseFloat($('#p-a').value)         || 1.0,
        b:            parseFloat($('#p-b').value)         || 1.0,
        beta:         parseFloat($('#p-beta').value)      || 2.0,
        num_friends:  parseInt($('#p-friends').value)     || 2,
        make_friends: $('#p-makefriends').checked,
        max_friends:  parseInt($('#p-maxfriends').value)  || 10,
    };
}

function getStepsPerTick() {
    return parseInt(stepsPerTickSelect?.value, 10) || 1;
}

function getActiveTab() {
    return document.querySelector('.tab-btn.active')?.dataset.tab || 'model';
}

async function api(path, body = null) {
    const opts = body !== null
        ? { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) }
        : { method: 'GET' };
    const res = await fetch(path, opts);
    return res.json();
}

function status(msg) { statusMsg.textContent = msg; }

// ============================================================
//  Chart.js  –  Model-level time series (O(1) incremental push)
// ============================================================

const chartOpts = (yLabel, yBounds = null) => ({
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    scales: {
        x: { title: { display: true, text: 'Step', color: '#8b8fa5' },
             ticks: { color: '#8b8fa5', maxTicksLimit: 12 }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: {
             ...(yBounds || {}),
             title: { display: true, text: yLabel, color: '#8b8fa5' },
             ticks: { color: '#8b8fa5' },
             grid: { color: 'rgba(255,255,255,0.04)' },
        },
    },
    plugins: { legend: { labels: { color: '#e4e6ed', boxWidth: 12 } } },
});

function makeChart(canvasId, datasets, yLabel = '', yBounds = null) {
    return new Chart(document.getElementById(canvasId), {
        type: 'line',
        data: { labels: [], datasets },
        options: chartOpts(yLabel, yBounds),
    });
}

// Model charts
const chartFirmCount = makeChart('chartFirmCount', [
    { label: 'Firms', data: [], borderColor: '#6c8cff', backgroundColor: 'rgba(108,140,255,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
    { label: 'New Firms', data: [], borderColor: '#fb923c', borderDash: [5, 3], tension: 0.3, pointRadius: 0 },
], 'Count');

const chartFirmSize = makeChart('chartFirmSize', [
    { label: 'Average', data: [], borderColor: '#6c8cff', tension: 0.3, pointRadius: 0 },
    { label: 'Largest', data: [], borderColor: '#fb923c', tension: 0.3, pointRadius: 0 },
], 'Workers');

const chartOutput = makeChart('chartOutput', [
    { label: 'Total', data: [], borderColor: '#34d399', tension: 0.3, pointRadius: 0 },
    { label: 'Largest Firm', data: [], borderColor: '#fb923c', tension: 0.3, pointRadius: 0 },
], 'Output');

const chartEffort = makeChart('chartEffort', [
    { label: 'Total (Normalized)', data: [], borderColor: '#a78bfa', tension: 0.3, pointRadius: 0 },
    { label: 'Largest Firm', data: [], borderColor: '#fb923c', tension: 0.3, pointRadius: 0 },
], 'Normalized Effort', { min: 0, max: 0.5 });

// Agent detail chart
const chartAgentHistory = makeChart('chartAgentHistory', [
    { label: 'Effort', data: [], borderColor: '#6c8cff', tension: 0.3, pointRadius: 0 },
    { label: 'Income', data: [], borderColor: '#34d399', tension: 0.3, pointRadius: 0 },
], 'Value');


function updateModelCharts(ts) {
    // Full reset from snapshot (used on Init / Reset) — skip step 0
    const n = Math.max(0, (ts['Number of Firms'] || []).length - 1);
    const makeLabels = () => Array.from({ length: n }, (_, i) => i + 1);

    chartFirmCount.data.labels = makeLabels();
    chartFirmCount.data.datasets[0].data = ts['Number of Firms'].slice(1);
    chartFirmCount.data.datasets[1].data = ts['New Firms'].slice(1);
    chartFirmCount.update('none');

    chartFirmSize.data.labels = makeLabels();
    chartFirmSize.data.datasets[0].data = ts['Average Firm Size'].slice(1);
    chartFirmSize.data.datasets[1].data = ts['Largest Firm Size'].slice(1);
    chartFirmSize.update('none');

    chartOutput.data.labels = makeLabels();
    chartOutput.data.datasets[0].data = ts['Total Output'].slice(1);
    chartOutput.data.datasets[1].data = ts['Output Largest Firm'].slice(1);
    chartOutput.update('none');

    chartEffort.data.labels = makeLabels();
    chartEffort.data.datasets[0].data = (ts['Average Effort Overall'] || []).slice(1);
    chartEffort.data.datasets[1].data = (ts['Average Effort Largest Firm'] || []).slice(1);
    chartEffort.update('none');
}

function appendModelChartsDelta(tsDelta, sinceStep) {
    const firmsArr = tsDelta['Number of Firms'] || [];
    if (firmsArr.length === 0) return;

    const startStep = Math.max(1, sinceStep + 1);
    const newLabels = [];
    for (let i = 0; i < firmsArr.length; i++) {
        newLabels.push(startStep + i);
    }

    const pushSeries = (chart, s0, s1) => {
        chart.data.labels.push(...newLabels);
        chart.data.datasets[0].data.push(...(tsDelta[s0] || []));
        chart.data.datasets[1].data.push(...(tsDelta[s1] || []));
        chart.update('none');
    };

    pushSeries(chartFirmCount, 'Number of Firms', 'New Firms');
    pushSeries(chartFirmSize, 'Average Firm Size', 'Largest Firm Size');
    pushSeries(chartOutput, 'Total Output', 'Output Largest Firm');
    pushSeries(chartEffort, 'Average Effort Overall', 'Average Effort Largest Firm');
}

// ============================================================
//  Firm View – Rank Clock Controls, Incremental State & Leaderboard
// ============================================================

const RANK_CLOCK_PALETTE = [
    '#6c8cff', '#34d399', '#fb923c', '#f472b6', '#38bdf8',
    '#a78bfa', '#facc15', '#f87171', '#2dd4bf', '#c084fc',
    '#4ade80', '#fb7185', '#60a5fa', '#fbbf24', '#818cf8',
    '#22d3ee', '#e879f9', '#a3e635', '#f97316', '#93c5fd',
];

function firmColor(firmId) {
    const idx = ((firmId * 2654435761) >>> 0) % RANK_CLOCK_PALETTE.length;
    return RANK_CLOCK_PALETTE[idx];
}

function getActiveFocusFirmId() {
    return hoveredFirmId != null ? hoveredFirmId : pinnedFirmId;
}

function sortRankClockFirms(firms) {
    firms.sort((a, b) => {
        const aAct = a.current_rank != null ? 0 : 1;
        const bAct = b.current_rank != null ? 0 : 1;
        if (aAct !== bAct) return aAct - bAct;
        if (a.current_rank != null && b.current_rank != null && a.current_rank !== b.current_rank) {
            return a.current_rank - b.current_rank;
        }
        if (a.peak_rank !== b.peak_rank) return a.peak_rank - b.peak_rank;
        return b.steps_in_top_n - a.steps_in_top_n;
    });
}

function populateRankClockFilter(firms) {
    if (pinnedFirmId != null && !rcFirmMap.has(pinnedFirmId)) {
        pinnedFirmId = null;
    }

    rcFirmFilter.innerHTML = '';
    const allOpt = document.createElement('option');
    allOpt.value = '';
    allOpt.textContent = `All Top Firms (${firms.length})`;
    rcFirmFilter.appendChild(allOpt);

    const frag = document.createDocumentFragment();
    const limit = Math.min(firms.length, 250);
    for (let i = 0; i < limit; i++) {
        const f = firms[i];
        const opt = document.createElement('option');
        opt.value = String(f.id);
        const rankTag = f.current_rank != null ? `#${f.current_rank}` : (f.alive ? 'exited' : 'dissolved');
        opt.textContent = `Firm ${f.id} (${rankTag} · peak #${f.peak_rank})`;
        frag.appendChild(opt);
    }
    // Ensure pinned firm is selectable even if beyond top 250 historical entrants
    if (pinnedFirmId != null && !firms.slice(0, limit).some(f => f.id === pinnedFirmId)) {
        const pf = rcFirmMap.get(pinnedFirmId);
        if (pf) {
            const opt = document.createElement('option');
            opt.value = String(pf.id);
            opt.textContent = `Firm ${pf.id} (peak #${pf.peak_rank})`;
            frag.appendChild(opt);
        }
    }
    rcFirmFilter.appendChild(frag);

    rcFirmFilter.value = pinnedFirmId != null ? String(pinnedFirmId) : '';
    rcClearFocus.style.display = pinnedFirmId != null ? 'inline-block' : 'none';
}

function renderRankClockStats(data) {
    const container = $('#rankClockStats');
    if (!data) {
        container.innerHTML = '';
        return;
    }

    const focusId = getActiveFocusFirmId();
    const focused = focusId != null ? rcFirmMap.get(focusId) : null;

    if (focused) {
        const color = firmColor(focused.id);
        const statusText = focused.current_rank != null
            ? `#${focused.current_rank}`
            : (focused.alive ? 'Outside' : 'Dissolved');
        container.innerHTML = `
            <div class="stat-chip"><span class="stat-value" style="color:${color}">Firm ${focused.id}</span><span class="stat-label">Focused</span></div>
            <div class="stat-chip"><span class="stat-value">${statusText}</span><span class="stat-label">Now</span></div>
            <div class="stat-chip"><span class="stat-value">#${focused.peak_rank}</span><span class="stat-label">Peak Rank</span></div>
            <div class="stat-chip"><span class="stat-value">${focused.peak_size}</span><span class="stat-label">Peak Size</span></div>
            <div class="stat-chip"><span class="stat-value">${focused.peak_output.toFixed(1)}</span><span class="stat-label">Peak Output</span></div>
            <div class="stat-chip"><span class="stat-value">${focused.steps_in_top_n}</span><span class="stat-label">Top-${data.top_n} Steps</span></div>
        `;
        return;
    }

    const leader = (data.firms && data.firms.length > 0 && data.firms[0].current_rank === 1)
        ? data.firms[0]
        : (data.firms || []).find(f => f.current_rank === 1);
    const leaderLabel = leader ? `Firm ${leader.id}` : '–';
    const leaderSub = leader
        ? (data.metric === 'output' ? `Leader (${leader.current_output.toFixed(1)} out)` : `Leader (${leader.current_size} wkrs)`)
        : 'Current #1';

    container.innerHTML = `
        <div class="stat-chip"><span class="stat-value" style="${leader ? 'color:' + firmColor(leader.id) : ''}">${leaderLabel}</span><span class="stat-label">${leaderSub}</span></div>
        <div class="stat-chip"><span class="stat-value">${data.rank1_turnovers ?? 0}</span><span class="stat-label">#1 Turnovers</span></div>
        <div class="stat-chip"><span class="stat-value">${(data.firms || []).length}</span><span class="stat-label">Top-${data.top_n} Entrants</span></div>
        <div class="stat-chip"><span class="stat-value">${data.total_living_firms ?? 0}</span><span class="stat-label">Active Firms</span></div>
    `;
}

function renderRankClockLeaderboard(data) {
    const firms = (data && data.firms) || [];
    rcFirmCountBadge.textContent = String(firms.length);

    if (firms.length === 0) {
        rcLeaderboard.innerHTML = `<div class="rc-leaderboard-hint" style="padding:0.5rem 0;">Step the simulation to populate Top-${rankClockTopN} trajectories.</div>`;
        return;
    }

    const focusId = getActiveFocusFirmId();
    const hasFocus = focusId != null;
    const MAX_LB_ROWS = 150;
    const limit = Math.min(firms.length, MAX_LB_ROWS);
    const htmlParts = [];

    for (let i = 0; i < limit; i++) {
        const f = firms[i];
        const color = firmColor(f.id);
        let badgeClass = 'rc-lb-rank';
        let badgeText = '';
        if (f.current_rank != null) {
            badgeText = `#${f.current_rank}`;
        } else if (f.alive) {
            badgeClass += ' exited';
            badgeText = `>${data.top_n}`;
        } else {
            badgeClass += ' dissolved';
            badgeText = 'Dissolved';
        }

        const metricText = data.metric === 'output'
            ? `peak out ${f.peak_output.toFixed(1)} · peak #${f.peak_rank}`
            : `peak ${f.peak_size} wkrs · peak #${f.peak_rank}`;

        let rowCls = 'rc-lb-row';
        if (hasFocus) {
            rowCls += (f.id === focusId) ? ' active' : ' dimmed';
        }

        htmlParts.push(
            `<div class="${rowCls}" data-firm-id="${f.id}">` +
                `<span class="rc-lb-swatch" style="background:${color};box-shadow:0 0 6px ${color}66;"></span>` +
                `<div class="rc-lb-main">` +
                    `<div class="rc-lb-title"><span>Firm ${f.id}</span><span class="${badgeClass}">${badgeText}</span></div>` +
                    `<div class="rc-lb-meta">${metricText} · t=${f.first_step}–${f.last_step}</div>` +
                `</div>` +
            `</div>`
        );
    }

    if (firms.length > MAX_LB_ROWS) {
        htmlParts.push(
            `<div class="rc-leaderboard-hint" style="text-align:center;padding:0.4rem 0;">` +
            `+${firms.length - MAX_LB_ROWS} earlier entrants shown on clock` +
            `</div>`
        );
    }

    rcLeaderboard.innerHTML = htmlParts.join('');
}

function syncRankClockAuxDom(force = false) {
    if (!rankClockData) return;
    const now = performance.now();
    // Throttle auxiliary dropdown/leaderboard rebuilds during continuous Run
    if (!force && running && (now - lastAuxDomSyncMs) < 250) {
        return;
    }
    lastAuxDomSyncMs = now;
    populateRankClockFilter(rankClockData.firms || []);
    renderRankClockLeaderboard(rankClockData);
}

async function loadRankClock() {
    const data = await api(`/api/rank_clock?metric=${rankClockMetric}&top_n=${rankClockTopN}`);
    if (data.error) {
        rankClockData = { step: 0, metric: rankClockMetric, top_n: rankClockTopN, rank1_turnovers: 0, total_living_firms: 0, firms: [] };
        rcFirmMap = new Map();
        rcPrevRank1Id = null;
        syncRankClockAuxDom(true);
        renderRankClockStats(rankClockData);
        drawRankClock(rankClockData);
        return;
    }
    rankClockData = data;
    rcFirmMap = new Map((data.firms || []).map(f => [f.id, f]));
    rcPrevRank1Id = data.last_rank1_id ?? null;
    const metricLabel = data.metric === 'output' ? 'Output' : 'Firm Size';
    rcSubtitle.textContent = `Ranked by ${metricLabel} · Rank 1 at center · Rank ${data.top_n} at rim`;
    syncRankClockAuxDom(true);
    renderRankClockStats(data);
    drawRankClock(data);
}

async function applyRankClockDelta(delta, forceAuxDom = false) {
    if (
        !rankClockData ||
        rankClockData.step !== delta.since_step ||
        rankClockData.metric !== delta.metric ||
        rankClockData.top_n !== delta.top_n
    ) {
        await loadRankClock();
        return;
    }

    const stepsElapsed = delta.step - delta.since_step;
    for (const f of rankClockData.firms) {
        f.in_top_n_now = false;
        f.current_rank = null;
        if (f.alive) {
            f.age += stepsElapsed;
        }
    }

    if (delta.dissolved_ids && delta.dissolved_ids.length > 0) {
        for (let i = 0; i < delta.dissolved_ids.length; i++) {
            const df = rcFirmMap.get(delta.dissolved_ids[i]);
            if (df) {
                df.alive = false;
                df.current_size = 0;
                df.current_output = 0;
            }
        }
    }

    const newSteps = delta.new_steps || [];
    for (let sIdx = 0; sIdx < newSteps.length; sIdx++) {
        const stepNum = delta.since_step + 1 + sIdx;
        const isLatestStep = (stepNum === delta.step);
        const stepTop = newSteps[sIdx];

        if (stepTop.length > 0) {
            const r1Id = stepTop[0][0];
            if (rcPrevRank1Id !== null && r1Id !== rcPrevRank1Id) {
                rankClockData.rank1_turnovers += 1;
            }
            rcPrevRank1Id = r1Id;
        }

        for (let rIdx = 0; rIdx < stepTop.length; rIdx++) {
            const [fid, size, output, age] = stepTop[rIdx];
            const rank = rIdx + 1;
            let f = rcFirmMap.get(fid);
            if (!f) {
                f = {
                    id: fid,
                    alive: true,
                    in_top_n_now: false,
                    current_rank: null,
                    current_size: size,
                    current_output: output,
                    age: age,
                    peak_rank: rank,
                    peak_size: size,
                    peak_output: output,
                    steps_in_top_n: 0,
                    first_step: stepNum,
                    last_step: stepNum,
                    points: [],
                };
                rcFirmMap.set(fid, f);
                rankClockData.firms.push(f);
            } else {
                f.alive = true;
                if (rank < f.peak_rank) f.peak_rank = rank;
                if (size > f.peak_size) f.peak_size = size;
                if (output > f.peak_output) f.peak_output = output;
                f.last_step = stepNum;
                f.age = age;
            }
            f.steps_in_top_n += 1;
            f.points.push([stepNum, rank, size, output]);

            if (isLatestStep) {
                f.in_top_n_now = true;
                f.current_rank = rank;
                f.current_size = size;
                f.current_output = output;
            }
        }
    }

    rankClockData.step = delta.step;
    rankClockData.total_living_firms = delta.total_living_firms;
    sortRankClockFirms(rankClockData.firms);

    syncRankClockAuxDom(forceAuxDom);
    renderRankClockStats(rankClockData);
    drawRankClock(rankClockData);
}

// ============================================================
//  Agent dropdown & view (O(1) incremental updates)
// ============================================================

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
    chartAgentHistory.data.datasets[0].data = [...history.effort];
    chartAgentHistory.data.datasets[1].data = [...history.income];
    chartAgentHistory.update('none');
}

async function loadAgentView(agentId) {
    if (agentId == null) return;
    selectedAgentId = agentId;
    const data = await api(`/api/agent/${agentId}`);
    if (data.error) { status(data.error); return; }
    renderAgentStats(data);
    updateAgentChart(data.history);
    drawFriendsNetwork(data);
    loadedAgentViewId = agentId;
    loadedAgentViewStep = currentStep;
}

async function applyAgentViewDelta(agentDelta) {
    if (!agentDelta || agentDelta.error) return;
    const hist = agentDelta.history || {};
    if (loadedAgentViewId !== agentDelta.id || loadedAgentViewStep !== hist.since_step) {
        await loadAgentView(selectedAgentId);
        return;
    }
    renderAgentStats(agentDelta);
    const effDelta = hist.effort_delta || [];
    const incDelta = hist.income_delta || [];
    if (effDelta.length > 0) {
        const baseLen = chartAgentHistory.data.labels.length;
        for (let i = 0; i < effDelta.length; i++) {
            chartAgentHistory.data.labels.push(baseLen + i);
        }
        chartAgentHistory.data.datasets[0].data.push(...effDelta);
        chartAgentHistory.data.datasets[1].data.push(...incDelta);
        chartAgentHistory.update('none');
    }
    drawFriendsNetwork(agentDelta);
    loadedAgentViewStep = currentStep;
}

// ============================================================
//  HiDPI Canvas – Rank Clock  (Batty 2006 polar rank-trajectory)
// ============================================================

const RC_GAP_RAD     = (16 * Math.PI) / 180;          // 16° corridor at 12 o'clock for rank labels
const RC_START_ANGLE = -Math.PI / 2 + RC_GAP_RAD / 2; // just clockwise of 12 o'clock
const RC_SWEEP_ANGLE = 2 * Math.PI - RC_GAP_RAD;      // 344° clockwise sweep
const RC_END_ANGLE   = RC_START_ANGLE + RC_SWEEP_ANGLE;

function rcRankTicks(topN) {
    if (topN <= 10) return [1, 3, 5, 8, 10];
    if (topN <= 25) return [1, 5, 10, 15, 20, 25];
    if (topN <= 50) return [1, 10, 20, 30, 40, 50];
    return [1, 25, 50, 75, 100];
}

function rcStepTicks(maxStep) {
    if (maxStep <= 0) return [];
    if (maxStep === 1) return [1];
    const raw = d3.ticks(1, maxStep, 8).filter(s => Number.isInteger(s) && s > 1 && s < maxStep);
    const interior = raw.filter(s => {
        const ratio = (s - 1) / (maxStep - 1);
        return ratio >= 0.08 && ratio <= 0.92;
    });
    return [1, ...interior, maxStep];
}

function rcAngleOfStep(step, maxStep) {
    if (maxStep <= 1) return RC_START_ANGLE;
    return RC_START_ANGLE + ((step - 1) / (maxStep - 1)) * RC_SWEEP_ANGLE;
}

function rcRadiusOfRank(rank, topN, innerR, outerR) {
    if (topN <= 1) return innerR;
    return innerR + ((rank - 1) / (topN - 1)) * (outerR - innerR);
}

function ensureRankClockCanvas() {
    if (!rankClockContainer) return null;
    const rect = rankClockContainer.getBoundingClientRect();
    const W = Math.max(Math.floor(rect.width) || 560, 320);
    const H = Math.max(Math.floor(rect.height) || 460, 360);
    const dpr = window.devicePixelRatio || 1;

    if (!rcDisplayCanvas || rcDisplayCanvas.parentNode !== rankClockContainer) {
        rankClockContainer.innerHTML = '';
        rcDisplayCanvas = document.createElement('canvas');
        rankClockContainer.appendChild(rcDisplayCanvas);
        bindRankClockCanvasEvents(rcDisplayCanvas);
    }
    if (!rcBaseCanvas) {
        rcBaseCanvas = document.createElement('canvas');
    }

    const pw = Math.round(W * dpr);
    const ph = Math.round(H * dpr);
    if (rcDisplayCanvas.width !== pw || rcDisplayCanvas.height !== ph) {
        rcDisplayCanvas.width = pw;
        rcDisplayCanvas.height = ph;
        rcDisplayCanvas.style.width = `${W}px`;
        rcDisplayCanvas.style.height = `${H}px`;
        rcBaseCanvas.width = pw;
        rcBaseCanvas.height = ph;
    }
    return { W, H, dpr };
}

function drawClockGuidesOnCtx(ctx, geom) {
    const { cx, cy, innerR, outerR, topN, maxStep } = geom;
    ctx.save();
    ctx.font = '500 10px Inter, system-ui, sans-serif';
    ctx.textBaseline = 'middle';

    // Radial step spokes & rim labels
    const stepTicks = rcStepTicks(maxStep);
    for (let i = 0; i < stepTicks.length; i++) {
        const s = stepTicks[i];
        const a = rcAngleOfStep(s, maxStep);
        const cosA = Math.cos(a);
        const sinA = Math.sin(a);
        const isStart = s === 1;
        const isNow = maxStep > 1 && s === maxStep;

        ctx.beginPath();
        if (isNow) {
            ctx.strokeStyle = 'rgba(52, 211, 153, 0.55)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 2]);
        } else if (isStart) {
            ctx.strokeStyle = 'rgba(108, 140, 255, 0.35)';
            ctx.lineWidth = 1.2;
            ctx.setLineDash([]);
        } else {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
            ctx.lineWidth = 1.0;
            ctx.setLineDash([]);
        }
        ctx.moveTo(cx + innerR * cosA, cy + innerR * sinA);
        ctx.lineTo(cx + (outerR + 5) * cosA, cy + (outerR + 5) * sinA);
        ctx.stroke();
        ctx.setLineDash([]);

        const labelR = outerR + 18;
        ctx.fillStyle = isNow ? '#34d399' : (isStart ? '#6c8cff' : '#8b8fa5');
        ctx.textAlign = Math.abs(cosA) < 0.2 ? 'center' : (cosA > 0 ? 'left' : 'right');
        ctx.fillText(`t=${s}`, cx + labelR * cosA, cy + labelR * sinA);
    }

    if (maxStep === 0) {
        ctx.beginPath();
        ctx.strokeStyle = 'rgba(108, 140, 255, 0.35)';
        ctx.lineWidth = 1.2;
        ctx.moveTo(cx + innerR * Math.cos(RC_START_ANGLE), cy + innerR * Math.sin(RC_START_ANGLE));
        ctx.lineTo(cx + outerR * Math.cos(RC_START_ANGLE), cy + outerR * Math.sin(RC_START_ANGLE));
        ctx.stroke();
    }

    // Concentric rank rings & 12 o'clock radial rank labels
    const rankTicks = rcRankTicks(topN);
    ctx.font = '600 9.5px Inter, system-ui, sans-serif';
    ctx.textAlign = 'center';
    for (let i = 0; i < rankTicks.length; i++) {
        const rnk = rankTicks[i];
        const r = rcRadiusOfRank(rnk, topN, innerR, outerR);
        ctx.beginPath();
        if (rnk === 1) {
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(108, 140, 255, 0.05)';
            ctx.fill();
            ctx.strokeStyle = 'rgba(108, 140, 255, 0.38)';
            ctx.lineWidth = 1.4;
            ctx.setLineDash([]);
            ctx.stroke();
        } else {
            ctx.arc(cx, cy, r, RC_START_ANGLE, RC_END_ANGLE, false);
            ctx.strokeStyle = rnk === topN ? 'rgba(255, 255, 255, 0.16)' : 'rgba(255, 255, 255, 0.08)';
            ctx.lineWidth = rnk === topN ? 1.2 : 1.0;
            ctx.setLineDash(rnk === topN ? [] : [3, 3]);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        ctx.fillStyle = '#8b8fa5';
        ctx.fillText(`#${rnk}`, cx, cy - r);
    }

    // Center bullseye label
    ctx.font = '700 10px Inter, system-ui, sans-serif';
    ctx.fillStyle = '#6c8cff';
    ctx.fillText('#1', cx, cy);
    ctx.restore();
}

function drawFirmTrajectoryOnCtx(ctx, f, geom, isFocused) {
    const pts = f.points;
    if (!pts || pts.length === 0) return;

    const { cx, cy, innerR, outerR, topN, maxStep } = geom;
    const color = firmColor(f.id);

    ctx.save();
    if (isFocused) {
        ctx.globalAlpha = 1.0;
        ctx.lineWidth = 3.4;
        ctx.shadowColor = color;
        ctx.shadowBlur = 9;
    } else {
        ctx.globalAlpha = f.in_top_n_now ? 0.90 : 0.42;
        ctx.lineWidth = f.in_top_n_now ? 2.0 : 1.3;
    }
    ctx.strokeStyle = color;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Walk contiguous step runs; collapse constant-rank runs into single native ctx.arc calls
    const markers = [];
    let runStart = 0;
    while (runStart < pts.length) {
        let runEnd = runStart;
        while (runEnd + 1 < pts.length && pts[runEnd + 1][0] === pts[runEnd][0] + 1) {
            runEnd++;
        }

        const first = pts[runStart];
        const last = pts[runEnd];
        markers.push([first, last]);

        ctx.beginPath();
        const aStart = rcAngleOfStep(first[0], maxStep);
        const rStart = rcRadiusOfRank(first[1], topN, innerR, outerR);
        ctx.moveTo(cx + rStart * Math.cos(aStart), cy + rStart * Math.sin(aStart));

        if (runStart === runEnd) {
            ctx.lineTo(cx + rStart * Math.cos(aStart) + 0.01, cy + rStart * Math.sin(aStart));
        } else {
            let i = runStart;
            while (i < runEnd) {
                if (pts[i + 1][1] === pts[i][1]) {
                    // Collapse entire constant-rank stretch into a single circular arc!
                    let k = i + 1;
                    while (k + 1 <= runEnd && pts[k + 1][1] === pts[i][1]) {
                        k++;
                    }
                    const rArc = rcRadiusOfRank(pts[i][1], topN, innerR, outerR);
                    ctx.arc(cx, cy, rArc, rcAngleOfStep(pts[i][0], maxStep), rcAngleOfStep(pts[k][0], maxStep), false);
                    i = k;
                } else {
                    const a0 = rcAngleOfStep(pts[i][0], maxStep);
                    const r0 = rcRadiusOfRank(pts[i][1], topN, innerR, outerR);
                    const a1 = rcAngleOfStep(pts[i + 1][0], maxStep);
                    const r1 = rcRadiusOfRank(pts[i + 1][1], topN, innerR, outerR);
                    const subSteps = Math.max(1, Math.ceil(Math.abs(a1 - a0) / 0.05));
                    for (let j = 1; j <= subSteps; j++) {
                        const t = j / subSteps;
                        const a = a0 + (a1 - a0) * t;
                        const r = r0 + (r1 - r0) * t;
                        ctx.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a));
                    }
                    i++;
                }
            }
        }
        ctx.stroke();
        runStart = runEnd + 1;
    }

    // Draw entry, exit, and active head markers
    ctx.shadowBlur = isFocused ? 6 : 0;
    for (let m = 0; m < markers.length; m++) {
        const [first, last] = markers[m];
        if (first[0] > 1 || maxStep === 1) {
            const a = rcAngleOfStep(first[0], maxStep);
            const r = rcRadiusOfRank(first[1], topN, innerR, outerR);
            ctx.beginPath();
            ctx.arc(cx + r * Math.cos(a), cy + r * Math.sin(a), maxStep === 1 ? 4.0 : 2.3, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
        }
        if (last[0] < maxStep) {
            const a = rcAngleOfStep(last[0], maxStep);
            const r = rcRadiusOfRank(last[1], topN, innerR, outerR);
            ctx.beginPath();
            ctx.arc(cx + r * Math.cos(a), cy + r * Math.sin(a), 2.5, 0, Math.PI * 2);
            ctx.fillStyle = '#0f1117';
            ctx.fill();
            ctx.lineWidth = 1.4;
            ctx.strokeStyle = color;
            ctx.stroke();
        } else if (maxStep > 1) {
            const a = rcAngleOfStep(last[0], maxStep);
            const r = rcRadiusOfRank(last[1], topN, innerR, outerR);
            ctx.beginPath();
            ctx.arc(cx + r * Math.cos(a), cy + r * Math.sin(a), isFocused ? 4.8 : 3.8, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
            ctx.lineWidth = 1.1;
            ctx.strokeStyle = '#ffffff';
            ctx.stroke();
        }
    }
    ctx.restore();
}

function drawRankClock(data) {
    const dims = ensureRankClockCanvas();
    if (!dims) return;

    const { W, H, dpr } = dims;
    const cx = W / 2;
    const cy = H / 2;
    const outerR = Math.max(90, Math.min(W, H) / 2 - 44);
    const innerR = Math.max(22, outerR * 0.12);
    const topN = (data && data.top_n) || rankClockTopN;
    const maxStep = (data && data.step) || 0;
    const firms = (data && data.firms) || [];

    rcGeom = { W, H, dpr, cx, cy, innerR, outerR, topN, maxStep };

    // Render full base layer onto offscreen canvas once per step/resize
    const bctx = rcBaseCanvas.getContext('2d');
    bctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    bctx.clearRect(0, 0, W, H);

    drawClockGuidesOnCtx(bctx, rcGeom);

    if (maxStep === 0 || firms.length === 0) {
        bctx.save();
        bctx.font = '500 12px Inter, system-ui, sans-serif';
        bctx.fillStyle = '#8b8fa5';
        bctx.textAlign = 'center';
        bctx.fillText('Click Step or ▶ Run to watch firm rank trajectories', cx, cy + innerR + (outerR - innerR) * 0.52);
        bctx.restore();
    } else {
        // Draw historical firms first, active Top-N firms on top
        for (let i = firms.length - 1; i >= 0; i--) {
            drawFirmTrajectoryOnCtx(bctx, firms[i], rcGeom, false);
        }
    }

    paintRankClockDisplay();
}

function paintRankClockDisplay() {
    if (!rcDisplayCanvas || !rcBaseCanvas || !rcGeom) return;
    const { W, H, dpr } = rcGeom;
    const ctx = rcDisplayCanvas.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, rcDisplayCanvas.width, rcDisplayCanvas.height);

    const focusId = getActiveFocusFirmId();
    const focusedFirm = focusId != null ? rcFirmMap.get(focusId) : null;

    if (!focusedFirm) {
        ctx.drawImage(rcBaseCanvas, 0, 0);
        return;
    }

    // Dim cached trajectories in O(1), redraw sharp clock guides, and highlight focused firm
    ctx.save();
    ctx.globalAlpha = 0.12;
    ctx.drawImage(rcBaseCanvas, 0, 0);
    ctx.restore();

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawClockGuidesOnCtx(ctx, rcGeom);
    drawFirmTrajectoryOnCtx(ctx, focusedFirm, rcGeom, true);
}

function rcFindStepIdxLE(pts, targetStep) {
    let lo = 0, hi = pts.length - 1, ans = -1;
    while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (pts[mid][0] <= targetStep) {
            ans = mid;
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return ans;
}

function rcHitTest(mx, my) {
    if (!rcGeom || !rankClockData || !rankClockData.firms || rankClockData.step <= 0) return null;
    const { cx, cy, innerR, outerR, topN, maxStep } = rcGeom;
    const dx = mx - cx;
    const dy = my - cy;
    const rCursor = Math.hypot(dx, dy);
    if (rCursor < innerR - 12 || rCursor > outerR + 12) return null;

    let rawAngle = Math.atan2(dy, dx);
    if (rawAngle < -Math.PI / 2) rawAngle += 2 * Math.PI;
    if (rawAngle < RC_START_ANGLE - 0.08 || rawAngle > RC_END_ANGLE + 0.08) return null;

    const clamped = Math.max(RC_START_ANGLE, Math.min(RC_END_ANGLE, rawAngle));
    const exactStep = maxStep <= 1
        ? 1
        : 1 + ((clamped - RC_START_ANGLE) / RC_SWEEP_ANGLE) * (maxStep - 1);

    const firms = rankClockData.firms;
    let bestFirm = null;
    let bestPoint = null;
    let bestDist = 9.5; // px hit tolerance

    for (let i = 0; i < firms.length; i++) {
        const f = firms[i];
        const pts = f.points;
        if (!pts || pts.length === 0) continue;
        if (exactStep < f.first_step - 1 || exactStep > f.last_step + 1) continue;

        const idx = rcFindStepIdxLE(pts, exactStep);

        // Case 1: cursor angle falls inside a contiguous spiral segment [pts[idx], pts[idx+1]]
        if (idx >= 0 && idx + 1 < pts.length && pts[idx + 1][0] === pts[idx][0] + 1) {
            const frac = exactStep - pts[idx][0];
            const interpRank = pts[idx][1] + frac * (pts[idx + 1][1] - pts[idx][1]);
            const rFirm = rcRadiusOfRank(interpRank, topN, innerR, outerR);
            const d = Math.abs(rCursor - rFirm);
            if (d < bestDist) {
                bestDist = d;
                bestFirm = f;
                bestPoint = frac < 0.5 ? pts[idx] : pts[idx + 1];
            }
        }

        // Case 2: endpoint proximity (handles maxStep === 1 and isolated single-step appearances)
        const candidates = [];
        if (idx >= 0) candidates.push(pts[idx]);
        if (idx + 1 < pts.length) candidates.push(pts[idx + 1]);
        for (let c = 0; c < candidates.length; c++) {
            const pt = candidates[c];
            const a = rcAngleOfStep(pt[0], maxStep);
            const r = rcRadiusOfRank(pt[1], topN, innerR, outerR);
            const d = Math.hypot(mx - (cx + r * Math.cos(a)), my - (cy + r * Math.sin(a)));
            if (d < bestDist) {
                bestDist = d;
                bestFirm = f;
                bestPoint = pt;
            }
        }
    }

    return bestFirm ? { firm: bestFirm, point: bestPoint } : null;
}

function bindRankClockCanvasEvents(canvas) {
    canvas.addEventListener('mousemove', (ev) => {
        const rect = canvas.getBoundingClientRect();
        const mx = ev.clientX - rect.left;
        const my = ev.clientY - rect.top;
        const hit = rcHitTest(mx, my);

        if (hit) {
            const { firm: f, point: nearest } = hit;
            canvas.style.cursor = 'pointer';
            if (hoveredFirmId !== f.id) {
                hoveredFirmId = f.id;
                applyRankClockFocus();
            }
            const topN = (rankClockData && rankClockData.top_n) || rankClockTopN;
            const [pStep, pRank, pSize, pOut] = nearest;
            const statusStr = f.current_rank != null
                ? `Active (#${f.current_rank})`
                : (f.alive ? `Active (>${topN})` : 'Dissolved');

            tooltip.style.display = 'block';
            tooltip.innerHTML =
                `<strong style="color:${firmColor(f.id)}">Firm ${f.id}</strong> · Step ${pStep}<br>` +
                `Rank: <strong>#${pRank}</strong> of Top ${topN}<br>` +
                `Size: ${pSize} wkrs · Output: ${pOut.toFixed(2)}<br>` +
                `<span style="color:#8b8fa5">Peak #${f.peak_rank} · ${statusStr}</span>`;
            tooltip.style.left = (ev.pageX + 12) + 'px';
            tooltip.style.top = (ev.pageY - 34) + 'px';
        } else {
            canvas.style.cursor = 'default';
            tooltip.style.display = 'none';
            if (hoveredFirmId !== null) {
                hoveredFirmId = null;
                applyRankClockFocus();
            }
        }
    });

    canvas.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
        if (hoveredFirmId !== null) {
            hoveredFirmId = null;
            applyRankClockFocus();
        }
    });

    canvas.addEventListener('click', (ev) => {
        const rect = canvas.getBoundingClientRect();
        const hit = rcHitTest(ev.clientX - rect.left, ev.clientY - rect.top);
        if (hit) {
            const fid = hit.firm.id;
            pinnedFirmId = (pinnedFirmId === fid) ? null : fid;
        } else if (pinnedFirmId !== null) {
            pinnedFirmId = null;
        } else {
            return;
        }
        rcFirmFilter.value = pinnedFirmId != null ? String(pinnedFirmId) : '';
        rcClearFocus.style.display = pinnedFirmId != null ? 'inline-block' : 'none';
        applyRankClockFocus();
    });
}

function applyRankClockFocus() {
    renderRankClockStats(rankClockData);
    paintRankClockDisplay();

    const focusId = getActiveFocusFirmId();
    const hasFocus = focusId != null;
    if (rcLeaderboard) {
        const rows = rcLeaderboard.querySelectorAll('.rc-lb-row');
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const fid = parseInt(row.dataset.firmId, 10);
            row.classList.toggle('active', hasFocus && fid === focusId);
            row.classList.toggle('dimmed', hasFocus && fid !== focusId);
        }
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

        // Load detail view data on tab switch if not already synced to currentStep
        if (btn.dataset.tab === 'firm') {
            if (
                !rankClockData ||
                rankClockData.step !== currentStep ||
                rankClockData.metric !== rankClockMetric ||
                rankClockData.top_n !== rankClockTopN
            ) {
                loadRankClock();
            } else {
                syncRankClockAuxDom(true);
                drawRankClock(rankClockData);
            }
        }
        if (btn.dataset.tab === 'agent' && selectedAgentId != null) {
            if (loadedAgentViewId !== selectedAgentId || loadedAgentViewStep !== currentStep) {
                loadAgentView(selectedAgentId);
            }
        }
    });
});

// Event delegation on Rank Clock leaderboard (zero per-row listener churn)
rcLeaderboard.addEventListener('mouseover', (ev) => {
    const row = ev.target.closest('.rc-lb-row');
    const fid = row ? parseInt(row.dataset.firmId, 10) : null;
    if (hoveredFirmId !== fid) {
        hoveredFirmId = fid;
        applyRankClockFocus();
    }
});

rcLeaderboard.addEventListener('mouseleave', () => {
    if (hoveredFirmId !== null) {
        hoveredFirmId = null;
        applyRankClockFocus();
    }
});

rcLeaderboard.addEventListener('click', (ev) => {
    const row = ev.target.closest('.rc-lb-row');
    if (!row) return;
    const fid = parseInt(row.dataset.firmId, 10);
    pinnedFirmId = (pinnedFirmId === fid) ? null : fid;
    rcFirmFilter.value = pinnedFirmId != null ? String(pinnedFirmId) : '';
    rcClearFocus.style.display = pinnedFirmId != null ? 'inline-block' : 'none';
    applyRankClockFocus();
});

// Rank Clock metric toggle (Size vs Output)
rcMetricToggle.querySelectorAll('.seg-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const m = btn.dataset.metric;
        if (!m || m === rankClockMetric) return;
        rankClockMetric = m;
        rcMetricToggle.querySelectorAll('.seg-btn').forEach(b => b.classList.toggle('active', b === btn));
        loadRankClock();
    });
});

// Rank Clock Top-N cutoff selector
rcTopN.addEventListener('change', () => {
    const val = parseInt(rcTopN.value, 10);
    if (!isNaN(val)) {
        rankClockTopN = val;
        loadRankClock();
    }
});

// Rank Clock Focus dropdown & Clear button
rcFirmFilter.addEventListener('change', () => {
    const val = rcFirmFilter.value;
    pinnedFirmId = val ? parseInt(val, 10) : null;
    rcClearFocus.style.display = pinnedFirmId != null ? 'inline-block' : 'none';
    applyRankClockFocus();
});

rcClearFocus.addEventListener('click', () => {
    pinnedFirmId = null;
    rcFirmFilter.value = '';
    rcClearFocus.style.display = 'none';
    applyRankClockFocus();
});

// Redraw Rank Clock on window resize when Firm View is active
window.addEventListener('resize', () => {
    if (getActiveTab() === 'firm' && rankClockData) {
        drawRankClock(rankClockData);
    }
});

// Agent select
agentSelect.addEventListener('change', () => {
    const id = parseInt(agentSelect.value, 10);
    if (!isNaN(id)) loadAgentView(id);
});

// Full snapshot handler (used on Init & Reset)
async function handleInitSnapshot(snap) {
    currentStep = snap.step;
    stepDisplay.textContent = `Step: ${currentStep}`;
    updateModelCharts(snap.timeseries);

    // Populate Agent dropdown once using a DocumentFragment
    if (agentSelect.options.length <= 1 || agentSelect.options[0].value === '') {
        agentSelect.innerHTML = '';
        const workerIds = snap.worker_ids || [];
        const frag = document.createDocumentFragment();
        for (let idx = 0; idx < workerIds.length; idx++) {
            const opt = document.createElement('option');
            opt.value = workerIds[idx];
            opt.textContent = `Worker ${idx + 1}  (id ${workerIds[idx]})`;
            frag.appendChild(opt);
        }
        agentSelect.appendChild(frag);
        if (workerIds.length > 0) {
            selectedAgentId = workerIds[0];
            agentSelect.value = selectedAgentId;
        }
    }

    const activeTab = getActiveTab();
    if (activeTab === 'firm') await loadRankClock();
    if (activeTab === 'agent' && selectedAgentId != null) await loadAgentView(selectedAgentId);
}

// Incremental single-roundtrip step handler
async function performStep(n, forceAuxDom = false) {
    const activeTab = getActiveTab();
    const resp = await api('/api/step', {
        steps: n,
        since_step: currentStep,
        active_tab: activeTab,
        rc_metric: rankClockMetric,
        rc_top_n: rankClockTopN,
        agent_id: selectedAgentId,
    });
    if (resp.error) return resp;

    currentStep = resp.step;
    stepDisplay.textContent = `Step: ${currentStep}`;
    appendModelChartsDelta(resp.ts_delta, resp.since_step);

    if (activeTab === 'firm' && resp.rc_delta) {
        await applyRankClockDelta(resp.rc_delta, forceAuxDom);
    } else if (activeTab === 'agent' && resp.agent_delta) {
        await applyAgentViewDelta(resp.agent_delta);
    }
    return resp;
}


// Toggle Max Friends Cap input when Make Friends on Join changes
$('#p-makefriends').addEventListener('change', (ev) => {
    const enabled = ev.target.checked;
    $('#p-maxfriends').disabled = !enabled;
    $('#maxFriendsRow').style.opacity = enabled ? '1' : '0.5';
});

async function endSimulationAndShowResults(autoEnded = false) {
    running = false;
    btnRun.textContent = '\u25b6 Run';
    btnRun.classList.remove('running');
    if (getActiveTab() === 'firm') syncRankClockAuxDom(true);

    btnEnd.disabled = true;
    status(autoEnded ? `Reached ${MAX_STEP} steps – loading final results...` : 'Loading results...');

    try {
        const results = await api('/api/results');
        if (results.error) { status('Error: ' + results.error); return; }
        showResultsPage(results);
        status(autoEnded ? `Completed ${results.step} steps – viewing final results` : `Simulation results at step ${results.step}`);
    } catch (e) {
        status('Error fetching results: ' + e.message);
    } finally {
        btnEnd.disabled = false;
    }
}

// Init
btnInit.addEventListener('click', async () => {
    running = false;
    btnRun.textContent = '\u25b6 Run';
    btnRun.classList.remove('running');
    resultsPage.style.display = 'none';
    status('Initializing model...');
    btnInit.disabled = true;
    pinnedFirmId = null;
    hoveredFirmId = null;
    rankClockData = null;
    rcFirmMap = new Map();
    rcPrevRank1Id = null;
    loadedAgentViewStep = -1;
    loadedAgentViewId = null;
    agentListPopulated = false;
    agentSelect.innerHTML = '<option value="">loading...</option>';
    try {
        const snap = await api('/api/init', getParams());
        if (snap.error) { status('Error: ' + snap.error); return; }
        await handleInitSnapshot(snap);
        status(`Model initialized – ${snap.num_firms ?? snap.firms.length} firms`);
    } finally { btnInit.disabled = false; }
});

// Step
btnStep.addEventListener('click', async () => {
    const remaining = MAX_STEP - currentStep;
    if (remaining <= 0) {
        await endSimulationAndShowResults(true);
        return;
    }
    const n = Math.min(getStepsPerTick(), remaining);
    status(`Stepping ${n}...`);
    btnStep.disabled = true;
    try {
        const resp = await performStep(n, true);
        if (resp.error) { status('Error: ' + resp.error); return; }
        if (currentStep >= MAX_STEP) {
            await endSimulationAndShowResults(true);
        } else {
            status(`Step ${resp.step} – ${resp.num_firms} firms`);
        }
    } finally { btnStep.disabled = false; }
});

// Reset
btnReset.addEventListener('click', async () => {
    running = false;
    btnRun.textContent = '\u25b6 Run';
    btnRun.classList.remove('running');
    resultsPage.style.display = 'none';
    status('Resetting...');
    pinnedFirmId = null;
    hoveredFirmId = null;
    rankClockData = null;
    rcFirmMap = new Map();
    rcPrevRank1Id = null;
    loadedAgentViewStep = -1;
    loadedAgentViewId = null;
    const snap = await api('/api/reset', {});
    if (snap.error) { status('Error: ' + snap.error); return; }
    agentListPopulated = false;
    agentSelect.innerHTML = '<option value="">loading...</option>';
    await handleInitSnapshot(snap);
    status('Model reset');
});

// Run / Stop toggle
btnRun.addEventListener('click', () => {
    if (running) {
        running = false;
        btnRun.textContent = '\u25b6 Run';
        btnRun.classList.remove('running');
        if (getActiveTab() === 'firm') syncRankClockAuxDom(true);
        status(`Stopped at step ${currentStep}`);
    } else if (currentStep >= MAX_STEP) {
        endSimulationAndShowResults(true);
    } else {
        running = true;
        btnRun.textContent = '\u25a0 Stop';
        btnRun.classList.add('running');
        runLoop();
    }
});

async function runLoop() {
    let reachedMax = false;
    while (running) {
        if (currentStep >= MAX_STEP) {
            running = false;
            reachedMax = true;
            break;
        }
        const n = Math.min(getStepsPerTick(), MAX_STEP - currentStep);
        try {
            const resp = await performStep(n, false);
            if (resp.error) { running = false; status('Error: ' + resp.error); break; }
            status(`Running – step ${resp.step} – ${resp.num_firms} firms`);
            if (currentStep >= MAX_STEP) {
                running = false;
                reachedMax = true;
                break;
            }
        } catch (e) {
            running = false;
            status('Error: ' + e.message);
            break;
        }
        // Yield one animation frame so the browser paints smoothly without artificial delay
        await new Promise(r => requestAnimationFrame(r));
    }
    if (getActiveTab() === 'firm') syncRankClockAuxDom(true);
    btnRun.textContent = '\u25b6 Run';
    btnRun.classList.remove('running');
    if (reachedMax) {
        await endSimulationAndShowResults(true);
    }
}


// --- End Simulation click: stop immediately and show results ---
btnEnd.addEventListener('click', async () => {
    await endSimulationAndShowResults(false);
});

// --- Back button ---
btnBackToSim.addEventListener('click', () => {
    resultsPage.style.display = 'none';
});

// --- Show the results page ---
let resultsChartSize = null;
let resultsChartOutput = null;
let resultsChartProductivity = null;

function showResultsPage(data) {
    resultsPage.style.display = 'flex';
    document.getElementById('resultsTitle').textContent = `Simulation Results — Step ${data.step}`;
    document.getElementById('resultsSummary').textContent =
        `${data.total_workers} workers · ${data.living_firms} living firms · ${data.collapsed_firms} collapsed`;

    renderLogLogPlots(data.firms);
}

// ============================================================
//  OLS Power-Law Fit  (log-log linear regression)
//  Fits log(y) = m·log(x) + b  →  y = e^b · x^m
//  Returns { slope, intercept, r2, fitPoints }
// ============================================================

function fitPowerLaw(points) {
    // Filter to positive values only (log requires > 0)
    const valid = points.filter(p => p.x > 0 && p.y > 0);
    const n = valid.length;
    if (n < 2) return null;

    const lx = valid.map(p => Math.log(p.x));
    const ly = valid.map(p => Math.log(p.y));

    const sumX = lx.reduce((a, b) => a + b, 0);
    const sumY = ly.reduce((a, b) => a + b, 0);
    const sumXY = lx.reduce((a, v, i) => a + v * ly[i], 0);
    const sumX2 = lx.reduce((a, v) => a + v * v, 0);

    const denom = n * sumX2 - sumX * sumX;
    if (Math.abs(denom) < 1e-12) return null;

    const slope = (n * sumXY - sumX * sumY) / denom;
    const intercept = (sumY - slope * sumX) / n;

    // R² (coefficient of determination)
    const meanY = sumY / n;
    const ssTot = ly.reduce((a, v) => a + (v - meanY) ** 2, 0);
    const ssRes = ly.reduce((a, v, i) => a + (v - (slope * lx[i] + intercept)) ** 2, 0);
    const r2 = ssTot > 0 ? 1 - ssRes / ssTot : 0;

    // Generate fit line points spanning the data range
    const xMin = Math.min(...valid.map(p => p.x));
    const xMax = Math.max(...valid.map(p => p.x));
    const fitPoints = [];
    const steps = 50;
    for (let i = 0; i <= steps; i++) {
        const logX = Math.log(xMin) + (Math.log(xMax) - Math.log(xMin)) * (i / steps);
        const x = Math.exp(logX);
        const y = Math.exp(intercept) * Math.pow(x, slope);
        fitPoints.push({ x, y });
    }

    return { slope, intercept, r2, fitPoints };
}

// ============================================================
//  Log-Log Scatter Plots with Fit Line (Chart.js)
// ============================================================

function logLogChartOpts(xLabel, yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
            x: {
                type: 'logarithmic',
                title: { display: true, text: xLabel, color: '#8b8fa5' },
                ticks: { color: '#8b8fa5' },
                grid: { color: 'rgba(255,255,255,0.04)' },
            },
            y: {
                type: 'logarithmic',
                title: { display: true, text: yLabel, color: '#8b8fa5' },
                ticks: { color: '#8b8fa5' },
                grid: { color: 'rgba(255,255,255,0.04)' },
            },
        },
        plugins: {
            legend: { labels: { color: '#e4e6ed', boxWidth: 12 } },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        if (ctx.datasetIndex === 1) return ''; // suppress fit line tooltips
                        const raw = ctx.raw;
                        if (raw && raw.count != null) {
                            return `Size ${ctx.parsed.x}: avg output ${ctx.parsed.y.toFixed(2)} (${raw.count} firm${raw.count === 1 ? '' : 's'})`;
                        }
                        return `(${ctx.parsed.x.toFixed(1)}, ${ctx.parsed.y.toFixed(2)})`;
                    },
                },
            },
        },
    };
}

function makeLogLogChart(canvasId, xLabel, yLabel, dotColor, fitColor) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Data',
                    data: [],
                    backgroundColor: dotColor,
                    borderColor: dotColor,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Fit',
                    data: [],
                    borderColor: fitColor,
                    borderWidth: 2,
                    borderDash: [6, 3],
                    pointRadius: 0,
                    showLine: true,
                    fill: false,
                    tension: 0,
                },
            ],
        },
        options: logLogChartOpts(xLabel, yLabel),
    });
}

function applyFit(chart, dataPoints, dotLabel, fitLabel) {
    chart.data.datasets[0].data = dataPoints;
    chart.data.datasets[0].label = dotLabel;

    const fit = fitPowerLaw(dataPoints);
    if (fit) {
        chart.data.datasets[1].data = fit.fitPoints;
        chart.data.datasets[1].label = `${fitLabel} (slope=${fit.slope.toFixed(2)}, R²=${fit.r2.toFixed(3)})`;
    }
    chart.update();
}

function renderLogLogPlots(firms) {
    // Destroy previous chart instances if they exist
    if (resultsChartSize) resultsChartSize.destroy();
    if (resultsChartOutput) resultsChartOutput.destroy();
    if (resultsChartProductivity) resultsChartProductivity.destroy();

    // Rank-Size plot
    const sizeData = firms.map((f, i) => ({ x: i + 1, y: f.size })).filter(d => d.y > 0);
    resultsChartSize = makeLogLogChart('chartLogSize', 'Rank', 'Firm Size', '#6c8cff', 'rgba(108,140,255,0.5)');
    applyFit(resultsChartSize, sizeData, 'Firm Size', 'Power-law fit');

    // Rank-Output plot
    const outputSorted = [...firms].sort((a, b) => b.output - a.output);
    const outputData = outputSorted.map((f, i) => ({ x: i + 1, y: f.output })).filter(d => d.y > 0);
    resultsChartOutput = makeLogLogChart('chartLogOutput', 'Rank', 'Firm Output', '#34d399', 'rgba(52,211,153,0.5)');
    applyFit(resultsChartOutput, outputData, 'Firm Output', 'Power-law fit');

    // Size-Output scaling plot: average firm output at each distinct firm size
    const bySize = new Map();
    for (let i = 0; i < firms.length; i++) {
        const f = firms[i];
        if (f.size <= 0) continue;
        const bucket = bySize.get(f.size);
        if (bucket) {
            bucket.sum += f.output;
            bucket.count += 1;
        } else {
            bySize.set(f.size, { sum: f.output, count: 1 });
        }
    }
    const sizeOutputData = Array.from(bySize.entries())
        .sort((a, b) => a[0] - b[0])
        .map(([size, b]) => ({ x: size, y: b.sum / b.count, count: b.count }))
        .filter(d => d.y > 0);
    resultsChartProductivity = makeLogLogChart('chartLogProductivity', 'Firm Size', 'Avg Firm Output', '#fb923c', 'rgba(251,146,60,0.5)');
    applyFit(resultsChartProductivity, sizeOutputData, 'Avg Firm Output', 'Power-law fit');
}

