// ==========================================================================
// DOGFOOD 2026 // MISSION CONTROL CYBERNETIC ENGINE
// Real-time Acceptance Audits, Persona Switcher, Gate #05 Firewall & Web Audio
// ==========================================================================

let audioEnabled = localStorage.getItem('cyber_audio_enabled') !== 'false';
let audioCtx = null;
let cachedAudits = [];

// Synthesized Web Audio API Sound Effects (Zero External Dependencies)
function getAudioContext() {
    if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            audioCtx = new AudioContext();
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

function playCyberSound(type) {
    if (!audioEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        const now = ctx.currentTime;

        if (type === 'click') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(800, now);
            osc.frequency.exponentialRampToValueAtTime(300, now + 0.04);
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.04);
            osc.start(now);
            osc.stop(now + 0.04);
        } else if (type === 'pass') {
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(523.25, now); // C5
            osc.frequency.setValueAtTime(659.25, now + 0.07); // E5
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.16);
            osc.start(now);
            osc.stop(now + 0.16);
        } else if (type === 'fail' || type === 'shield_block') {
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(180, now);
            osc.frequency.linearRampToValueAtTime(110, now + 0.18);
            gain.gain.setValueAtTime(0.18, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.18);
            osc.start(now);
            osc.stop(now + 0.18);
        } else if (type === 'audit_start') {
            osc.type = 'sine';
            osc.frequency.setValueAtTime(260, now);
            osc.frequency.exponentialRampToValueAtTime(900, now + 0.22);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.22);
            osc.start(now);
            osc.stop(now + 0.22);
        }
    } catch (e) {
        // Audio error silent fallback
    }
}

function updateAudioButtonUI() {
    const btn = document.getElementById('cyber-audio-toggle');
    if (!btn) return;
    const textEl = btn.querySelector('.audio-text');
    const iconEl = btn.querySelector('.audio-icon');
    if (textEl) textEl.textContent = audioEnabled ? 'Audio: ON' : 'Audio: OFF';
    if (iconEl) iconEl.textContent = audioEnabled ? '🔊' : '🔈';
    btn.classList.toggle('muted', !audioEnabled);
}

function toggleCyberAudio() {
    audioEnabled = !audioEnabled;
    localStorage.setItem('cyber_audio_enabled', audioEnabled);
    updateAudioButtonUI();
    if (audioEnabled) {
        playCyberSound('click');
        showToast('Cyber Synthesizer Audio enabled', 'info');
    } else {
        showToast('Cyber Audio muted', 'info');
    }
}

// Dom Ready Handlers
document.addEventListener('DOMContentLoaded', () => {
    // Sync audio toggle button
    updateAudioButtonUI();

    // Initialize all judge forms with real-time score calculation
    document.querySelectorAll('.hud-score-form').forEach(form => {
        updateWeightedPreview(form);
    });

    // Logout button handler
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            playCyberSound('click');
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
                showToast('Session cleared', 'info');
                setTimeout(() => window.location.href = '/', 400);
            } catch (err) {
                window.location.href = '/';
            }
        });
    }

    // Auto-update real-time clocks
    const clockEl = document.getElementById('live-telemetry-clock');
    setInterval(() => {
        const now = new Date();
        const utcStr = 'UTC: ' + now.toISOString().replace('T', ' ').substring(0, 19);
        if (clockEl) clockEl.textContent = utcStr;
    }, 1000);

    // Initial audit history cache load
    syncAuditHistory(true);
});

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('hud-toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `hud-toast ${type}`;
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `<span class="toast-icon">${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// 1. Trigger Full Live Acceptance Audit (7 Checks)
async function triggerLiveAudit() {
    playCyberSound('audit_start');
    const btn = document.getElementById('btn-run-all-checks');
    const logOutput = document.getElementById('audit-log-output');
    const progressWrap = document.getElementById('suite-progress-wrap');
    const progressBar = document.getElementById('suite-progress-bar');
    const progressText = document.getElementById('suite-progress-text');
    const progressPct = document.getElementById('suite-progress-pct');
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="btn-icon spinning">⏳</span> EXECUTING LIVE AUDIT...`;
    }

    if (progressWrap) {
        progressWrap.style.display = 'block';
        if (progressBar) progressBar.style.width = '20%';
        if (progressText) progressText.textContent = 'DISPATCHING 7-CHECK ACCEPTANCE SUITE...';
        if (progressPct) progressPct.textContent = '20%';
    }

    // Reset all cards to scanning
    document.querySelectorAll('.check-card').forEach(card => {
        card.classList.add('scanning');
    });

    if (logOutput) {
        logOutput.textContent = `[AUDIT-START] Initializing 7-point acceptance check sequence...\n` +
                                `[AUDIT-TARGET] Connecting to http://localhost:8088\n` +
                                `[AUDIT-ENGINE] Testing T1 (Core Gallery + Submissions) & T2 (Judging + Role Isolation)...\n`;
    }

    try {
        const response = await fetch('/api/checks/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            playCyberSound('fail');
            showToast('Audit failed: ' + (data.error || 'Server error'), 'error');
            if (progressBar) progressBar.style.background = 'var(--accent-red)';
            if (progressText) progressText.textContent = 'SUITE FAILED TO EXECUTE';
            return;
        }

        playCyberSound('pass');
        const audit = data.audit;
        const results = audit.results;

        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.style.background = audit.passedChecks === audit.totalChecks ? 'linear-gradient(90deg, #00f0a8, #00c4ff)' : 'linear-gradient(90deg, #f59e0b, #ef4444)';
        }
        if (progressText) progressText.textContent = `VERIFICATION COMPLETE: ${audit.passedChecks} / ${audit.totalChecks} PASSED (${audit.durationMs} ms)`;
        if (progressPct) progressPct.textContent = '100%';

        // Update Matrix Cards
        results.forEach(c => {
            const card = document.getElementById(`check-card-${c.id}`);
            const latEl = document.getElementById(`lat-${c.id}`);
            if (card) {
                card.classList.remove('scanning');
                card.className = `check-card ${c.passed ? 'pass' : 'fail'}`;
                const badge = card.querySelector('.check-badge');
                if (badge) {
                    badge.className = `check-badge ${c.passed ? 'pass' : 'fail'}`;
                    badge.textContent = c.passed ? 'PASS' : 'FAIL';
                }
            }
            if (latEl) {
                latEl.textContent = `${c.latencyMs} ms`;
            }
        });

        // Update Terminal Log
        let terminalText = `==================================================\n` +
                           `      DOGFOOD 2026 ACCEPTANCE CHECKER REPORT     \n` +
                           `==================================================\n` +
                           `Execution Time (UTC):   ${audit.timestampUtc}\n` +
                           `Execution Time (Local): ${audit.timestampLocal || audit.timestampUtc}\n` +
                           `Total Suite Latency:    ${audit.durationMs} ms\n` +
                           `Operator:               ${audit.operator} (${audit.operatorRole})\n\n` +
                           `[TIER 1 CHECKS]\n`;

        results.filter(r => r.tier.startsWith('Tier 1')).forEach(r => {
            terminalText += `  [${r.passed ? 'PASS' : 'FAIL'}] ${r.id}: ${r.name} -> Expected: ${r.expected} | Actual: ${r.actual} (${r.latencyMs} ms)\n`;
        });

        terminalText += `\n[TIER 2 CHECKS]\n`;
        results.filter(r => r.tier.startsWith('Tier 2')).forEach(r => {
            terminalText += `  [${r.passed ? 'PASS' : 'FAIL'}] ${r.id}: ${r.name} -> Expected: ${r.expected} | Actual: ${r.actual} (${r.latencyMs} ms)\n`;
        });

        terminalText += `\n==================================================\n` +
                        `SUMMARY: ${audit.passedChecks}/${audit.totalChecks} PASSED\n` +
                        `Tier 1:  ${audit.t1Verified ? 'VERIFIED' : 'FAILED'}\n` +
                        `Tier 2:  ${audit.t2Verified ? 'VERIFIED' : 'FAILED'}\n` +
                        `MongoDB Collection: checkAudits (Doc ID: ${audit._id})\n` +
                        `==================================================`;

        if (logOutput) {
            logOutput.textContent = terminalText;
        }

        // Prepend new row to MongoDB Audit Stream Table
        prependAuditTableRow(audit);

        showToast(`Audit Complete: ${audit.passedChecks}/${audit.totalChecks} Passed. Stored in MongoDB!`, 'success');

    } catch (err) {
        playCyberSound('fail');
        showToast('Network error during audit execution', 'error');
        if (logOutput) {
            logOutput.textContent += `\n[AUDIT-ERROR] ${err.message}\n`;
        }
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span class="btn-icon">▶</span> RUN ALL 7 CHECKS`;
        }
        document.querySelectorAll('.check-card').forEach(card => card.classList.remove('scanning'));
    }
}

// Live Calculation of Weighted Total in Judge Evaluation Forms
function updateWeightedPreview(form) {
    if (!form) return;
    const inputs = form.querySelectorAll('input[type="range"][data-weight]');
    let total = 0;
    inputs.forEach(inp => {
        const val = parseFloat(inp.value) || 0;
        const weight = parseFloat(inp.getAttribute('data-weight')) || 0;
        total += val * weight;
    });
    const display = form.querySelector('.calc-value-display');
    if (display) {
        display.textContent = total.toFixed(2);
    }
}

// Filter Stored Audit History Logs in Real-time
function filterAuditLogs() {
    const q = (document.getElementById('audit-filter-input')?.value || '').toLowerCase().trim();
    const rows = document.querySelectorAll('#audit-history-tbody tr');
    rows.forEach(tr => {
        if (tr.id === 'empty-audits-row') return;
        const text = tr.textContent.toLowerCase();
        if (!q || text.includes(q)) {
            tr.style.display = '';
        } else {
            tr.style.display = 'none';
        }
    });
}

// 2. Trigger Single Acceptance Check on Demand
async function triggerSingleCheck(checkId) {
    playCyberSound('click');
    const card = document.getElementById(`check-card-${checkId}`);
    const latEl = document.getElementById(`lat-${checkId}`);
    const logOutput = document.getElementById('audit-log-output');

    if (card) {
        card.classList.add('scanning');
    }
    if (latEl) {
        latEl.textContent = 'Testing...';
    }

    try {
        const resp = await fetch('/api/checks/run-single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ checkId: checkId })
        });
        const data = await resp.json();

        if (!resp.ok || !data.success) {
            playCyberSound('fail');
            showToast(`Check ${checkId} failed: ` + (data.error || 'Server error'), 'error');
            return;
        }

        const res = data.result;
        const audit = data.audit;

        if (res.passed) {
            playCyberSound('pass');
        } else {
            playCyberSound('fail');
        }

        if (card) {
            card.className = `check-card ${res.passed ? 'pass' : 'fail'}`;
            const badge = card.querySelector('.check-badge');
            if (badge) {
                badge.className = `check-badge ${res.passed ? 'pass' : 'fail'}`;
                badge.textContent = res.passed ? 'PASS' : 'FAIL';
            }
        }
        if (latEl) {
            latEl.textContent = `${res.latencyMs} ms`;
        }

        if (logOutput) {
            const logLine = `[SINGLE-CHECK] ${res.id} (${res.name}): ${res.passed ? 'PASS' : 'FAIL'} -> Status: ${res.statusCode} | Latency: ${res.latencyMs} ms | Stored in MongoDB ID: ${audit._id}\n`;
            logOutput.textContent = logLine + logOutput.textContent;
        }

        // Add to audit table
        prependAuditTableRow(audit);

        showToast(`Check ${checkId} Verified: ${res.passed ? 'PASS' : 'FAIL'} (${res.latencyMs} ms)`, res.passed ? 'success' : 'error');

    } catch (err) {
        playCyberSound('fail');
        showToast(`Network error testing ${checkId}`, 'error');
    } finally {
        if (card) card.classList.remove('scanning');
    }
}

// 3. Interactive Gate #05 Firewall Prober
async function runFirewallProbe() {
    playCyberSound('click');
    const sourceRole = document.getElementById('probe-source-role').value;
    const targetJudge = document.getElementById('probe-target-judge').value;
    const visualizer = document.getElementById('firewall-visualizer');
    const icon = document.getElementById('shield-indicator-icon');
    const headline = document.getElementById('shield-status-headline');
    const bodyText = document.getElementById('shield-status-body');
    const badgeBar = document.getElementById('shield-telemetry-badge');
    const codePill = document.getElementById('shield-code-pill');
    const latPill = document.getElementById('shield-lat-pill');
    const gatePill = document.getElementById('shield-gate-pill');

    headline.textContent = 'PROBING SECURITY SHIELD...';
    bodyText.textContent = `Dispatching test request as ${sourceRole.toUpperCase()} -> target: ${targetJudge}...`;
    icon.className = 'shield-indicator pulse';

    try {
        const resp = await fetch('/api/checks/probe-firewall', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sourceRole: sourceRole, targetJudge: targetJudge })
        });
        const data = await resp.json();

        badgeBar.style.display = 'flex';
        codePill.textContent = `HTTP ${data.statusCode}`;
        latPill.textContent = `${data.latencyMs} ms`;

        if (data.isBlocked) {
            playCyberSound('shield_block');
            visualizer.className = 'firewall-visualizer-box blocked';
            icon.textContent = '🛡️';
            icon.className = 'shield-indicator blocked';
            headline.textContent = `ACCESS BLOCKED: ${data.statusCode} FORBIDDEN`;
            bodyText.textContent = `GATE #05 COMPLIANCE ENFORCED: Backend verified session credentials for '${sourceRole}' and strictly denied unauthorized access to ${targetJudge}'s private scores.`;
            gatePill.className = 'shield-pill badge-success';
            gatePill.textContent = 'GATE #05 PASS (PROTECTED)';
        } else {
            playCyberSound('pass');
            visualizer.className = 'firewall-visualizer-box permitted';
            icon.textContent = '🔓';
            icon.className = 'shield-indicator permitted';
            headline.textContent = `ACCESS GRANTED: ${data.statusCode} OK`;
            bodyText.textContent = `Legitimate evaluation access granted to ${sourceRole.toUpperCase()} for ${targetJudge}.`;
            gatePill.className = 'shield-pill badge-info';
            gatePill.textContent = 'LEGITIMATE PERMITTED';
        }

    } catch (err) {
        playCyberSound('fail');
        headline.textContent = 'PROBE ERROR';
        bodyText.textContent = err.message;
    }
}

// 4. Toggle Inspector Drawer on Check Card
function toggleInspector(checkId) {
    playCyberSound('click');
    const drawer = document.getElementById(`inspect-${checkId}`);
    if (drawer) {
        drawer.style.display = drawer.style.display === 'none' ? 'block' : 'none';
    }
}

// 5. Filter Check Cards (All, Tier 1, Tier 2)
function filterChecks(tier) {
    playCyberSound('click');
    document.querySelectorAll('.filter-pill').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-filter') === tier);
    });

    document.querySelectorAll('.check-card').forEach(card => {
        const cardTier = card.getAttribute('data-tier');
        if (tier === 'all' || cardTier === tier) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// 6. Prepend Row to Audit History Table
function prependAuditTableRow(audit) {
    cachedAudits.unshift(audit);
    const tbody = document.getElementById('audit-history-tbody');
    const emptyRow = document.getElementById('empty-audits-row');
    if (emptyRow) emptyRow.remove();

    if (tbody) {
        const tr = document.createElement('tr');
        tr.setAttribute('data-audit-id', audit._id);
        tr.className = 'new-row-highlight';
        tr.innerHTML = `
            <td>
                <div class="time-primary"><code>${audit.timestampUtc || audit.timestampFormatted}</code></div>
                ${audit.timestampLocal ? `<div class="time-sub">Local: ${audit.timestampLocal}</div>` : ''}
            </td>
            <td>
                <span class="run-type-pill ${(audit.runType || '').includes('FULL') ? 'full' : 'single'}">
                    ${audit.runType || 'FULL_SUITE'}
                </span>
            </td>
            <td><strong>${audit.operator}</strong></td>
            <td><span class="role-pill role-${audit.operatorRole}">${audit.operatorRole}</span></td>
            <td>${audit.durationMs} ms</td>
            <td>
                ${audit.passedChecks === audit.totalChecks ? 
                    `<span class="badge-success">${audit.passedChecks} / ${audit.totalChecks} Passed</span>` : 
                    `<span class="badge-warning">${audit.passedChecks} / ${audit.totalChecks} Passed</span>`}
            </td>
            <td>
                <button class="btn-mini-inspect" onclick="viewAuditJson('${audit._id}')">
                    👁️ View JSON
                </button>
            </td>
        `;
        tbody.insertBefore(tr, tbody.firstChild);

        // Update counter badges
        const countBadge = document.getElementById('audit-count-badge');
        const heroBadge = document.getElementById('hero-audit-counter');
        if (countBadge) countBadge.textContent = parseInt(countBadge.textContent || '0') + 1;
        if (heroBadge) heroBadge.textContent = `${countBadge ? countBadge.textContent : '1'} LOGGED`;
    }
}

// 7. Sync Audit History from MongoDB
async function syncAuditHistory(silent = false) {
    if (!silent) playCyberSound('click');
    try {
        const resp = await fetch('/api/checks/history?limit=25');
        const audits = await resp.json();
        if (Array.isArray(audits)) {
            cachedAudits = audits;
            const tbody = document.getElementById('audit-history-tbody');
            if (tbody && !silent) {
                tbody.innerHTML = '';
                if (audits.length === 0) {
                    tbody.innerHTML = `<tr id="empty-audits-row"><td colspan="7" class="text-center text-muted">No stored audits found in MongoDB.</td></tr>`;
                } else {
                    audits.forEach(a => {
                        const tr = document.createElement('tr');
                        tr.setAttribute('data-audit-id', a._id);
                        tr.innerHTML = `
                            <td>
                                <div class="time-primary"><code>${a.timestampUtc || a.timestampFormatted || a.timestamp}</code></div>
                                ${a.timestampLocal ? `<div class="time-sub">Local: ${a.timestampLocal}</div>` : ''}
                            </td>
                            <td>
                                <span class="run-type-pill ${(a.runType || '').includes('FULL') ? 'full' : 'single'}">
                                    ${a.runType || 'FULL_SUITE'}
                                </span>
                            </td>
                            <td><strong>${a.operator}</strong></td>
                            <td><span class="role-pill role-${a.operatorRole}">${a.operatorRole}</span></td>
                            <td>${a.durationMs} ms</td>
                            <td>
                                ${a.passedChecks === a.totalChecks ? 
                                    `<span class="badge-success">${a.passedChecks} / ${a.totalChecks} Passed</span>` : 
                                    `<span class="badge-warning">${a.passedChecks} / ${a.totalChecks} Passed</span>`}
                            </td>
                            <td>
                                <button class="btn-mini-inspect" onclick="viewAuditJson('${a._id}')">
                                    👁️ View JSON
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
                const countBadge = document.getElementById('audit-count-badge');
                if (countBadge) countBadge.textContent = audits.length;
                const heroBadge = document.getElementById('hero-audit-counter');
                if (heroBadge) heroBadge.textContent = `${audits.length} LOGGED`;
                showToast(`Synced ${audits.length} audits from MongoDB`, 'info');
            }
        }
    } catch (e) {
        if (!silent) showToast('Failed to sync audit history', 'error');
    }
}

// 8. Clear Audit History from MongoDB
async function clearAuditHistory() {
    playCyberSound('click');
    if (!confirm('Are you sure you want to clear all stored check audit logs in MongoDB?')) return;

    try {
        const resp = await fetch('/api/checks/history', { method: 'DELETE' });
        const data = await resp.json();
        if (resp.ok && data.success) {
            playCyberSound('pass');
            cachedAudits = [];
            const tbody = document.getElementById('audit-history-tbody');
            if (tbody) {
                tbody.innerHTML = `<tr id="empty-audits-row"><td colspan="7" class="text-center text-muted">All audit logs cleared. Run tests above to record new entries.</td></tr>`;
            }
            const countBadge = document.getElementById('audit-count-badge');
            if (countBadge) countBadge.textContent = '0';
            const heroBadge = document.getElementById('hero-audit-counter');
            if (heroBadge) heroBadge.textContent = '0 LOGGED';
            showToast('Cleared audit logs from MongoDB', 'success');
        }
    } catch (e) {
        showToast('Failed to clear audit history', 'error');
    }
}

// 9. Export Audits to JSON File
function exportAuditsJson() {
    playCyberSound('click');
    if (!cachedAudits.length) {
        showToast('No audits to export', 'info');
        return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(cachedAudits, null, 2));
    const dlAnchor = document.createElement('a');
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `dogfood_acceptance_audits_${new Date().toISOString().substring(0, 10)}.json`);
    document.body.appendChild(dlAnchor);
    dlAnchor.click();
    dlAnchor.remove();
    showToast('Exported audit history to JSON', 'success');
}

// 10. View Raw Mongo JSON in Modal
function viewAuditJson(auditId) {
    playCyberSound('click');
    const modal = document.getElementById('mongo-modal');
    const pre = document.getElementById('modal-json-content');
    const idEl = document.getElementById('modal-audit-id');
    const timeEl = document.getElementById('modal-audit-time');

    const audit = cachedAudits.find(a => a._id === auditId);
    if (!audit) {
        showToast('Audit document not found in local cache', 'error');
        return;
    }

    if (idEl) idEl.textContent = `MongoDB _id: ${audit._id}`;
    if (timeEl) timeEl.textContent = `Recorded: ${audit.timestampUtc || audit.timestampFormatted || audit.timestamp}`;
    if (pre) pre.textContent = JSON.stringify(audit, null, 2);

    if (modal) modal.style.display = 'flex';
}

function closeMongoModal() {
    playCyberSound('click');
    const modal = document.getElementById('mongo-modal');
    if (modal) modal.style.display = 'none';
}

function closeModalOnBackdrop(event) {
    if (event.target.id === 'mongo-modal') {
        closeMongoModal();
    }
}

function copyModalJson() {
    const pre = document.getElementById('modal-json-content');
    if (pre) {
        navigator.clipboard.writeText(pre.textContent);
        showToast('Copied raw MongoDB JSON to clipboard!', 'success');
    }
}

// 11. Persona Switcher
async function switchPersona(roleSlug) {
    playCyberSound('click');
    try {
        const resp = await fetch('/api/auth/switch-role', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona: roleSlug })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            showToast(`Switched active persona to: ${roleSlug.toUpperCase()}`, 'success');
            setTimeout(() => window.location.reload(), 300);
        } else {
            showToast(data.error || 'Failed to switch persona', 'error');
        }
    } catch (err) {
        showToast('Network error while switching persona', 'error');
    }
}

// 12. Trigger Z-Score Normalization
async function triggerNormalization() {
    playCyberSound('click');
    try {
        const resp = await fetch('/api/judge/normalize', { method: 'POST' });
        const data = await resp.json();
        if (resp.ok) {
            playCyberSound('pass');
            showToast(data.message || 'Scores successfully normalized with sigma=0 guard!', 'success');
            loadLiveCsvPreview();
        } else {
            playCyberSound('fail');
            showToast(data.error || 'Normalization failed', 'error');
        }
    } catch (err) {
        showToast('Network error during normalization', 'error');
    }
}

// 13. Publish Official Results
async function publishOfficialResults() {
    playCyberSound('click');
    try {
        const resp = await fetch('/api/judge/publish', { method: 'POST' });
        const data = await resp.json();
        if (resp.ok) {
            playCyberSound('pass');
            showToast(data.message || 'Results published to public gallery!', 'success');
        } else {
            showToast(data.error || 'Failed to publish results', 'error');
        }
    } catch (err) {
        showToast('Network error while publishing results', 'error');
    }
}

// 14. Batch Assign Judges
async function batchAssignJudges() {
    playCyberSound('click');
    try {
        const resp = await fetch('/api/judge/assignments', { method: 'POST' });
        const data = await resp.json();
        if (resp.ok) {
            playCyberSound('pass');
            showToast(data.message || 'Batch round-robin assignments created!', 'success');
        } else {
            showToast(data.error || 'Failed to assign judges', 'error');
        }
    } catch (err) {
        showToast('Network error during judge assignment', 'error');
    }
}

// 15. Live CSV Table Preview
async function loadLiveCsvPreview() {
    playCyberSound('click');
    try {
        const resp = await fetch('/api/export/preview');
        const results = await resp.json();
        const tbody = document.getElementById('live-standings-tbody');
        if (!tbody || !Array.isArray(results)) return;

        tbody.innerHTML = '';
        results.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>#${r.rank} ${r.title}</strong></td>
                <td><span class="track-pill">${r.track}</span></td>
                <td><code>${r.rawAvg}</code></td>
                <td><code class="z-score-val">${r.normalizedAvg}</code></td>
                <td>${r.judgeCount} review(s)</td>
                <td><span class="badge-success">Rank #${r.rank}</span></td>
            `;
            tbody.appendChild(tr);
        });
        showToast('Loaded real-time ranking preview', 'info');
    } catch (err) {
        console.error('Failed to load standings preview', err);
    }
}

// 16. Judge Score Submission from Dashboard
async function submitJudgeScore(subId, btn) {
    playCyberSound('click');
    const card = document.getElementById(`card-sub-${subId}`);
    if (!card) return;

    const form = card.querySelector('.hud-score-form');
    const commentEl = form.querySelector('textarea[name="comment"]');
    const comment = commentEl ? commentEl.value : '';

    const criteriaScores = [];
    const ranges = form.querySelectorAll('input[type="range"]');
    ranges.forEach(r => {
        const name = r.name.replace('score_', '');
        criteriaScores.push({ criterionName: name, score: parseFloat(r.value) });
    });

    btn.disabled = true;
    btn.textContent = 'Submitting...';

    try {
        const resp = await fetch('/api/judge/scores', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                submissionId: subId,
                criteriaScores: criteriaScores,
                comment: comment
            })
        });

        const data = await resp.json();
        if (resp.ok) {
            playCyberSound('pass');
            showToast('Evaluation submitted successfully!', 'success');
            card.style.opacity = '0.5';
            btn.textContent = 'Submitted';
            setTimeout(() => window.location.reload(), 600);
        } else {
            playCyberSound('fail');
            showToast(data.error || 'Failed to submit evaluation', 'error');
            btn.disabled = false;
            btn.textContent = 'Submit Evaluation';
        }
    } catch (err) {
        showToast('Network error while submitting evaluation', 'error');
        btn.disabled = false;
        btn.textContent = 'Submit Evaluation';
    }
}

// 17. Terminal HUD Controls
function copyTerminalLog() {
    playCyberSound('click');
    const el = document.getElementById('audit-log-output');
    if (el) {
        navigator.clipboard.writeText(el.textContent);
        showToast('Terminal output copied to clipboard!', 'success');
    }
}

function clearTerminalLog() {
    playCyberSound('click');
    const el = document.getElementById('audit-log-output');
    if (el) {
        el.textContent = `[DOGFOOD-SYSTEM] Terminal cleared. Ready for next audit run.\n`;
        showToast('Terminal cleared', 'info');
    }
}

function downloadAuditReport() {
    playCyberSound('click');
    const el = document.getElementById('audit-log-output');
    if (!el) return;
    const blob = new Blob([el.textContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `acceptance-report-${new Date().toISOString().substring(0, 19).replace(/:/g, '-')}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    showToast('Downloaded audit report file', 'success');
}

// Feature 2: Leaderboard Toggle
async function toggleLeaderboardPreview() {
    try {
        const resp = await fetch('/api/judge/leaderboard-toggle', {method: 'POST', credentials: 'include'});
        const data = await resp.json();
        if (resp.ok) {
            alert(data.message || 'Leaderboard toggled');
            location.reload();
        } else {
            alert('Error: ' + (data.error || 'Failed to toggle'));
        }
    } catch (e) {
        alert('Error toggling leaderboard: ' + e.message);
    }
}

// Feature 3: Save Draft Score
async function saveDraftScore(submissionId, btnEl) {
    const form = btnEl.closest('form') || btnEl.closest('.hud-score-form');
    if (!form) { alert('Form not found'); return; }
    const scores = {};
    form.querySelectorAll('input[type=range]').forEach(input => {
        const name = input.name.replace('score_', '');
        scores[name] = parseInt(input.value);
    });
    const comment = form.querySelector('textarea[name=comment]');
    try {
        btnEl.disabled = true;
        btnEl.textContent = 'Saving...';
        const resp = await fetch('/api/judge/scores', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({
                submissionId: submissionId,
                criteriaScores: scores,
                comment: comment ? comment.value : '',
                draft: true
            })
        });
        const data = await resp.json();
        if (resp.ok) {
            btnEl.textContent = '✅ Draft Saved';
            setTimeout(() => { btnEl.textContent = '💾 Save Draft'; btnEl.disabled = false; }, 2000);
        } else {
            alert('Error: ' + (data.error || 'Failed to save draft'));
            btnEl.textContent = '💾 Save Draft';
            btnEl.disabled = false;
        }
    } catch (e) {
        alert('Error saving draft: ' + e.message);
        btnEl.textContent = '💾 Save Draft';
        btnEl.disabled = false;
    }
}

// Feature 4: COI Conflicts Viewer
async function loadConflicts() {
    try {
        const resp = await fetch('/api/judge/conflicts', {credentials: 'include'});
        if (!resp.ok) { alert('Error loading conflicts'); return; }
        const data = await resp.json();
        const tbody = document.getElementById('conflicts-tbody');
        if (!tbody) return;
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No conflicts detected. All assignments are conflict-free.</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(c => `
            <tr>
                <td><strong>${c.judgeName || c.judgeId}</strong></td>
                <td>${c.submissionTitle || c.submissionId}</td>
                <td><code>${c.reason}</code></td>
                <td><span class="badge-warning">SKIPPED</span></td>
            </tr>
        `).join('');
    } catch (e) {
        alert('Error: ' + e.message);
    }
}
