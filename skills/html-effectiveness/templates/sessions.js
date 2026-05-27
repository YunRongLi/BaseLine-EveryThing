document.addEventListener('keydown', function(e) {
    if (e.altKey && e.key === 'Enter') {
        const agentInput = document.getElementById('agentInput');
        if (document.activeElement === agentInput && agentInput) {
            e.preventDefault();
            if (typeof window.sendAgentMessage === 'function') {
                window.sendAgentMessage();
            }
        }
    }
});

document.addEventListener('DOMContentLoaded', () => {

    // 1. Find navbar container
    const navRight = document.querySelector('.nav-right') || document.querySelector('.navbar-controls') || document.querySelector('.navbar');
    if (!navRight) return;

    // 2. Create New Session button
    const btnNew = document.createElement('button');
    btnNew.id = 'btn-new-session';
    btnNew.className = 'btn btn-secondary';
    btnNew.textContent = 'New Session';
    btnNew.style.whiteSpace = 'nowrap';
    btnNew.style.marginRight = '0.5rem';
    btnNew.style.padding = '0.4rem 1rem';
    btnNew.style.fontSize = '0.8125rem';
    btnNew.style.borderRadius = '999px';
    btnNew.style.cursor = 'pointer';
    btnNew.style.height = 'auto';
    btnNew.style.display = 'inline-flex';
    btnNew.style.alignItems = 'center';
    btnNew.style.justifyContent = 'center';
    btnNew.style.border = '1.5px solid var(--gray-200, #e6e6e3)';
    btnNew.style.backgroundColor = 'transparent';
    btnNew.style.fontWeight = '600';
    btnNew.onclick = handleNewSession;

    // 3. Create Sessions Switcher button
    const btnList = document.createElement('button');
    btnList.id = 'btn-sessions';
    btnList.className = 'btn btn-secondary';
    btnList.textContent = 'Sessions';
    btnList.style.whiteSpace = 'nowrap';
    btnList.style.marginRight = '0.5rem';
    btnList.style.padding = '0.4rem 1rem';
    btnList.style.fontSize = '0.8125rem';
    btnList.style.borderRadius = '999px';
    btnList.style.cursor = 'pointer';
    btnList.style.height = 'auto';
    btnList.style.display = 'inline-flex';
    btnList.style.alignItems = 'center';
    btnList.style.justifyContent = 'center';
    btnList.style.border = '1.5px solid var(--gray-200, #e6e6e3)';
    btnList.style.backgroundColor = 'transparent';
    btnList.style.fontWeight = '600';
    btnList.onclick = openSessionsModal;

    // 4. Inject buttons cleanly
    if (navRight.classList.contains('navbar')) {
        // If it's the raw navbar, wrap buttons in a container or append
        const container = document.createElement('div');
        container.style.display = 'flex';
        container.style.alignItems = 'center';
        container.appendChild(btnNew);
        container.appendChild(btnList);
        navRight.appendChild(container);
    } else {
        navRight.insertBefore(btnList, navRight.firstChild);
        navRight.insertBefore(btnNew, navRight.firstChild);
    }

    // 5. Inject Sessions Switcher popup/modal HTML
    const modalHtml = `
    <div id="sessionsModal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.35); align-items:center; justify-content:center; z-index:2000; font-family: system-ui, -apple-system, sans-serif;">
        <div style="background-color: var(--paper, #fdfdfc); border: 1.5px solid var(--gray-200, #e6e6e3); border-radius: 12px; padding: 2rem; width: 600px; max-width: 95%; box-shadow: 0 4px 20px rgba(0,0,0,0.15); display: flex; flex-direction: column; max-height: 80vh;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1.5px solid var(--gray-200, #e6e6e3); padding-bottom: 1rem; margin-bottom: 1rem;">
                <h3 style="margin:0; font-family: var(--serif, Georgia); font-weight: 500; font-size: 1.25rem; color: var(--slate, #1c1c1a);">Manage Sessions</h3>
                <button onclick="closeSessionsModal()" style="background:none; border:none; font-size:1.5rem; cursor:pointer; color: var(--gray-500, #8f8f8b);">&times;</button>
            </div>
            <div id="sessions-list-container" style="flex-grow:1; overflow-y:auto; margin-bottom: 1rem; display:flex; flex-direction:column; gap: 0.75rem; padding-right: 0.5rem;">
                <!-- Populated dynamically -->
            </div>
            <div style="display:flex; justify-content:flex-end; gap:0.5rem; border-top: 1.5px solid var(--gray-200, #e6e6e3); padding-top: 1rem;">
                <button class="btn btn-secondary" onclick="closeSessionsModal()" style="padding: 0.5rem 1rem; font-size: 0.8125rem; border-radius:999px;">Close</button>
            </div>
        </div>
    </div>
    `;
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = modalHtml;
    document.body.appendChild(tempDiv.firstElementChild);

    // 6. Inject Premium Glassmorphism Permission Gate Modal HTML
    const permModalHtml = `
    <div id="permissionModal" style="display:none; position:fixed; inset:0; background:rgba(15, 23, 42, 0.4); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); align-items:center; justify-content:center; z-index:3000; font-family: system-ui, -apple-system, sans-serif; transition: all 0.3s ease;">
        <div style="background: rgba(255, 255, 255, 0.85); border: 1.5px solid rgba(255, 255, 255, 0.5); border-radius: 16px; padding: 2rem; width: 480px; max-width: 90%; box-shadow: 0 8px 32px rgba(15, 23, 42, 0.15); display: flex; flex-direction: column; text-align: center; gap: 1.5rem; transform: scale(0.95); transition: transform 0.3s ease;">
            <div style="display: flex; justify-content: center;">
                <div style="background: rgba(239, 68, 68, 0.1); border: 1.5px solid rgba(239, 68, 68, 0.3); border-radius: 50%; width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; color: #ef4444; font-size: 1.5rem; font-weight: bold;">
                    !
                </div>
            </div>
            <div>
                <h3 id="perm-title" style="margin: 0 0 0.5rem 0; font-weight: 600; font-size: 1.25rem; color: #0f172a;">Permission Required</h3>
                <p id="perm-desc" style="margin: 0; font-size: 0.9375rem; color: #475569; line-height: 1.5;"></p>
            </div>
            <div style="background: rgba(15, 23, 42, 0.04); border: 1px solid rgba(15, 23, 42, 0.08); border-radius: 8px; padding: 0.75rem 1rem; font-family: monospace; font-size: 0.8125rem; color: #1e293b; text-align: left; max-height: 120px; overflow-y: auto; word-break: break-all;">
                <span id="perm-target" style="font-weight: 600;"></span>
            </div>
            <div style="display: flex; gap: 0.75rem; width: 100%;">
                <button onclick="respondPermission(false)" style="flex: 1; padding: 0.625rem; border-radius: 8px; border: 1.5px solid #e2e8f0; background: #fff; color: #475569; font-weight: 600; font-size: 0.875rem; cursor: pointer; transition: all 0.15s ease;" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background='#fff'">Deny</button>
                <button onclick="respondPermission(true)" style="flex: 1; padding: 0.625rem; border-radius: 8px; border: none; background: #ef4444; color: #fff; font-weight: 600; font-size: 0.875rem; cursor: pointer; transition: all 0.15s ease;" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">Allow</button>
            </div>
        </div>
    </div>
    `;
    const tempDivPerm = document.createElement('div');
    tempDivPerm.innerHTML = permModalHtml;
    document.body.appendChild(tempDivPerm.firstElementChild);
});

window.openSessionsModal = function() {
    const modal = document.getElementById('sessionsModal');
    if (modal) {
        modal.style.display = 'flex';
        fetchSessions();
    }
};

window.closeSessionsModal = function() {
    const modal = document.getElementById('sessionsModal');
    if (modal) {
        modal.style.display = 'none';
    }
};

async function fetchSessions() {
    try {
        const res = await fetch('/api/sessions');
        const data = await res.json();
        if (data.status === 'success') {
            renderSessionsList(data.sessions, data.active_session_id);
        }
    } catch (err) {
        console.error('Failed to fetch sessions:', err);
    }
}

function renderSessionsList(sessions, activeId) {
    const container = document.getElementById('sessions-list-container');
    if (!container) return;
    container.innerHTML = '';
    
    if (sessions.length === 0) {
        container.innerHTML = '<div style="color: var(--gray-500); text-align: center; padding: 2rem;">No past sessions found.</div>';
        return;
    }
    
    sessions.forEach(sess => {
        const isActive = sess.session_id === activeId;
        const card = document.createElement('div');
        card.style.border = isActive ? '1.5px solid var(--clay, #d97757)' : '1px solid var(--gray-200, #e6e6e3)';
        card.style.backgroundColor = isActive ? 'rgba(217, 119, 87, 0.03)' : 'var(--paper, #fdfdfc)';
        card.style.borderRadius = '8px';
        card.style.padding = '0.75rem 1rem';
        card.style.display = 'flex';
        card.style.justifyContent = 'space-between';
        card.style.alignItems = 'center';
        card.style.gap = '1rem';
        card.style.transition = 'all 0.15s ease';
        
        const info = document.createElement('div');
        info.style.flexGrow = '1';
        info.style.cursor = 'pointer';
        info.onclick = () => selectSession(sess.session_id);
        
        const title = document.createElement('div');
        title.style.fontWeight = isActive ? '600' : '500';
        title.style.fontSize = '0.9375rem';
        title.style.color = 'var(--slate, #1c1c1a)';
        title.textContent = sess.title || 'Untitled Session';
        
        const meta = document.createElement('div');
        meta.style.fontSize = '0.75rem';
        meta.style.color = 'var(--gray-500, #8f8f8b)';
        meta.style.marginTop = '0.25rem';
        meta.textContent = `Updated: ${sess.updated_at ? sess.updated_at.slice(0, 16).replace('T', ' ') : 'N/A'}`;
        
        info.appendChild(title);
        info.appendChild(meta);
        
        const actions = document.createElement('div');
        actions.style.display = 'flex';
        actions.style.gap = '0.5rem';
        actions.style.alignItems = 'center';
        
        if (!isActive) {
            const btnSel = document.createElement('button');
            btnSel.className = 'btn btn-secondary';
            btnSel.textContent = 'Switch';
            btnSel.style.padding = '0.3rem 0.75rem';
            btnSel.style.fontSize = '0.75rem';
            btnSel.style.borderRadius = '4px';
            btnSel.style.cursor = 'pointer';
            btnSel.onclick = () => selectSession(sess.session_id);
            
            const btnDel = document.createElement('button');
            btnDel.className = 'btn btn-secondary';
            btnDel.textContent = 'Delete';
            btnDel.style.padding = '0.3rem 0.75rem';
            btnDel.style.fontSize = '0.75rem';
            btnDel.style.borderRadius = '4px';
            btnDel.style.borderColor = 'rgba(176, 74, 63, 0.2)';
            btnDel.style.color = 'var(--rust, #b04a3f)';
            btnDel.style.cursor = 'pointer';
            btnDel.onclick = (e) => {
                e.stopPropagation();
                if (confirm('Are you sure you want to permanently delete this session?')) {
                    deleteSession(sess.session_id);
                }
            };
            
            actions.appendChild(btnSel);
            actions.appendChild(btnDel);
        } else {
            const activeBadge = document.createElement('span');
            activeBadge.style.fontSize = '0.75rem';
            activeBadge.style.fontWeight = '600';
            activeBadge.style.color = 'var(--clay, #d97757)';
            activeBadge.style.backgroundColor = 'rgba(217, 119, 87, 0.1)';
            activeBadge.style.padding = '0.25rem 0.5rem';
            activeBadge.style.borderRadius = '4px';
            activeBadge.textContent = 'Active';
            actions.appendChild(activeBadge);
        }
        
        card.appendChild(info);
        card.appendChild(actions);
        container.appendChild(card);
    });
}

async function selectSession(sessionId) {
    try {
        const res = await fetch('/api/sessions/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.location.reload();
        }
    } catch (err) {
        console.error('Failed to select session:', err);
    }
}

async function deleteSession(sessionId) {
    try {
        const res = await fetch('/api/sessions/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        const data = await res.json();
        if (data.status === 'success') {
            fetchSessions();
        }
    } catch (err) {
        console.error('Failed to delete session:', err);
    }
}

async function handleNewSession() {
    try {
        const res = await fetch('/api/sessions/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const data = await res.json();
        if (data.status === 'success') {
            window.location.href = '/explore';
        }
    } catch (err) {
        console.error('Failed to start new session:', err);
    }
}

let isPermissionModalOpen = false;

async function checkPendingPermission() {
    try {
        const res = await fetch('/api/state');
        const data = await res.json();
        if (data.status === 'success' && data.state) {
            const pending = data.state.pending_permission;
            const modal = document.getElementById('permissionModal');
            if (pending) {
                // Populate text
                const titleEl = document.getElementById('perm-title');
                const descEl = document.getElementById('perm-desc');
                const targetEl = document.getElementById('perm-target');
                
                const isZh = (localStorage.getItem('app_lang') || 'en') === 'zh';
                titleEl.textContent = isZh ? "權限授權請求" : "Permission Gate Authorization";
                descEl.textContent = pending.message || (isZh ? "系統即將執行高風險操作，需要您的核准。" : "The AI Agent requested a high-risk operation.");
                targetEl.textContent = pending.target || "";
                
                if (modal && modal.style.display !== 'flex') {
                    modal.style.display = 'flex';
                    // Trigger reflow for transition
                    setTimeout(() => {
                        modal.firstElementChild.style.transform = 'scale(1)';
                    }, 10);
                    isPermissionModalOpen = true;
                }
            } else {
                if (modal && modal.style.display === 'flex') {
                    modal.firstElementChild.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        modal.style.display = 'none';
                    }, 150);
                    isPermissionModalOpen = false;
                }
            }
        }
    } catch (e) {
        console.error("Error checking pending permission:", e);
    }
}

window.respondPermission = async function(approved) {
    try {
        const res = await fetch('/api/agent/permission/respond', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ approved: approved })
        });
        const data = await res.json();
        if (data.status === 'success') {
            const modal = document.getElementById('permissionModal');
            if (modal) {
                modal.firstElementChild.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 150);
            }
            isPermissionModalOpen = false;
            
            // Refresh parent view logs if fetchDebugLogs is present
            if (typeof fetchDebugLogs === 'function') {
                await fetchDebugLogs();
            }
        }
    } catch (e) {
        console.error("Error sending permission response:", e);
    }
};

// Start checking intervals
setInterval(checkPendingPermission, 3000);
