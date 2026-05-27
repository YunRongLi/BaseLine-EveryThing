/**
 * sessions.js
 *
 * Session management UI injected into all task templates.
 * Uses the native OpenCode session API via /api/opencode/session/*.
 * Stores the active session ID in localStorage under 'opencode_session_id'.
 */

// ---------------------------------------------------------------------------
// Redundant Alt+Enter shortcut has been moved to keyboard_shortcuts.js
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Inject session controls into navbar
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    const navRight = document.querySelector('.nav-right') ||
                     document.querySelector('.navbar-controls') ||
                     document.querySelector('.navbar');
    if (!navRight) return;

    const btnNew = _makeNavBtn('btn-new-session', 'New Session', handleNewSession);
    const btnList = _makeNavBtn('btn-sessions', 'Sessions', openSessionsModal);

    if (navRight.classList.contains('navbar')) {
        const wrapper = document.createElement('div');
        wrapper.style.cssText = 'display:flex; align-items:center;';
        wrapper.appendChild(btnNew);
        wrapper.appendChild(btnList);
        navRight.appendChild(wrapper);
    } else {
        navRight.insertBefore(btnList, navRight.firstChild);
        navRight.insertBefore(btnNew, navRight.firstChild);
    }

    // Sessions modal
    document.body.insertAdjacentHTML('beforeend', `
    <div id="sessionsModal" style="display:none; position:fixed; inset:0;
         background:rgba(0,0,0,0.35); align-items:center; justify-content:center;
         z-index:2000; font-family:system-ui,-apple-system,sans-serif;">
      <div style="background:var(--paper,#fdfdfc); border:1.5px solid var(--gray-200,#e6e6e3);
           border-radius:12px; padding:2rem; width:600px; max-width:95%;
           box-shadow:0 4px 20px rgba(0,0,0,0.15); display:flex; flex-direction:column;
           max-height:80vh;">
        <div style="display:flex; justify-content:space-between; align-items:center;
             border-bottom:1.5px solid var(--gray-200,#e6e6e3); padding-bottom:1rem; margin-bottom:1rem;">
          <h3 style="margin:0; font-weight:500; font-size:1.25rem; color:var(--slate,#1c1c1a);">
            Manage Sessions
          </h3>
          <button onclick="closeSessionsModal()"
                  style="background:none; border:none; font-size:1.5rem; cursor:pointer;
                         color:var(--gray-500,#8f8f8b);">&times;</button>
        </div>
        <div id="sessions-list-container"
             style="flex-grow:1; overflow-y:auto; margin-bottom:1rem;
                    display:flex; flex-direction:column; gap:0.75rem; padding-right:0.5rem;">
        </div>
        <div style="display:flex; justify-content:flex-end; gap:0.5rem;
             border-top:1.5px solid var(--gray-200,#e6e6e3); padding-top:1rem;">
          <button class="btn btn-secondary" onclick="closeSessionsModal()"
                  style="padding:0.5rem 1rem; font-size:0.8125rem; border-radius:999px;">
            Close
          </button>
        </div>
      </div>
    </div>`);
});

function _makeNavBtn(id, label, handler) {
    const btn = document.createElement('button');
    btn.id = id;
    btn.className = 'btn btn-secondary';
    btn.textContent = label;
    Object.assign(btn.style, {
        whiteSpace: 'nowrap',
        marginRight: '0.5rem',
        padding: '0.4rem 1rem',
        fontSize: '0.8125rem',
        borderRadius: '999px',
        cursor: 'pointer',
        height: 'auto',
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '1.5px solid var(--gray-200, #e6e6e3)',
        backgroundColor: 'transparent',
        fontWeight: '600',
    });
    btn.onclick = handler;
    return btn;
}

// ---------------------------------------------------------------------------
// Modal open / close
// ---------------------------------------------------------------------------

window.openSessionsModal = function() {
    const modal = document.getElementById('sessionsModal');
    if (modal) { modal.style.display = 'flex'; fetchAndRenderSessions(); }
};

window.closeSessionsModal = function() {
    const modal = document.getElementById('sessionsModal');
    if (modal) modal.style.display = 'none';
};

// ---------------------------------------------------------------------------
// Session list fetch + render
// ---------------------------------------------------------------------------

async function fetchAndRenderSessions() {
    const container = document.getElementById('sessions-list-container');
    if (!container) return;
    container.innerHTML = '<div style="color:var(--gray-500); font-size:0.8125rem;">Loading...</div>';

    let sessions = [];
    try {
        const data = await ocListSessions();
        // OpenCode returns an array directly or {sessions: [...]}
        sessions = Array.isArray(data) ? data : (data.sessions || []);
    } catch (err) {
        container.innerHTML = `<div style="color:var(--rust,#B04A3F);">Failed to load sessions: ${err.message}</div>`;
        return;
    }

    const activeId = localStorage.getItem('opencode_session_id');
    renderSessionsList(sessions, activeId);
}

function renderSessionsList(sessions, activeId) {
    const container = document.getElementById('sessions-list-container');
    if (!container) return;
    container.innerHTML = '';

    if (sessions.length === 0) {
        container.innerHTML = '<div style="color:var(--gray-500); text-align:center; padding:2rem;">No sessions found.</div>';
        return;
    }

    sessions.forEach(sess => {
        const id = sess.id || sess.session_id;
        const isActive = id === activeId;
        const card = document.createElement('div');
        card.style.cssText = `border:${isActive ? '1.5px solid var(--clay,#d97757)' : '1px solid var(--gray-200,#e6e6e3)'};
            background-color:${isActive ? 'rgba(217,119,87,0.03)' : 'var(--paper,#fdfdfc)'};
            border-radius:8px; padding:0.75rem 1rem; display:flex;
            justify-content:space-between; align-items:center; gap:1rem; transition:all 0.15s ease;`;

        const info = document.createElement('div');
        info.style.cssText = 'flex-grow:1; cursor:pointer;';
        info.onclick = () => selectSession(id);

        const title = document.createElement('div');
        title.style.cssText = `font-weight:${isActive ? '600' : '500'}; font-size:0.9375rem; color:var(--slate,#1c1c1a);`;
        title.textContent = sess.title || sess.id || 'Untitled Session';

        const meta = document.createElement('div');
        meta.style.cssText = 'font-size:0.75rem; color:var(--gray-500,#8f8f8b); margin-top:0.25rem;';
        let updatedStr = '';
        if (sess.time && sess.time.updated) {
            updatedStr = new Date(sess.time.updated).toISOString();
        } else {
            updatedStr = sess.updated || sess.updated_at || sess.createdAt || '';
        }
        meta.textContent = updatedStr ? `Updated: ${updatedStr.slice(0, 16).replace('T', ' ')}` : id;

        info.appendChild(title);
        info.appendChild(meta);

        const actions = document.createElement('div');
        actions.style.cssText = 'display:flex; gap:0.5rem; align-items:center;';

        if (isActive) {
            const badge = document.createElement('span');
            badge.style.cssText = 'font-size:0.75rem; font-weight:600; color:var(--clay,#d97757); background:rgba(217,119,87,0.1); padding:0.25rem 0.5rem; border-radius:4px;';
            badge.textContent = 'Active';
            actions.appendChild(badge);
        } else {
            const btnSel = _makeSmallBtn('Switch', () => selectSession(id));
            const btnDel = _makeSmallBtn('Delete', (e) => {
                e.stopPropagation();
                if (confirm('Delete this session permanently?')) deleteSession(id);
            }, true);
            actions.appendChild(btnSel);
            actions.appendChild(btnDel);
        }

        card.appendChild(info);
        card.appendChild(actions);
        container.appendChild(card);
    });
}

function _makeSmallBtn(label, handler, isDanger = false) {
    const btn = document.createElement('button');
    btn.className = 'btn btn-secondary';
    btn.textContent = label;
    btn.style.cssText = `padding:0.3rem 0.75rem; font-size:0.75rem; border-radius:4px; cursor:pointer;
        ${isDanger ? 'border-color:rgba(176,74,63,0.2); color:var(--rust,#b04a3f);' : ''}`;
    btn.onclick = handler;
    return btn;
}

// ---------------------------------------------------------------------------
// Session actions
// ---------------------------------------------------------------------------

async function selectSession(sessionId) {
    localStorage.setItem('opencode_session_id', sessionId);
    window.location.reload();
}

async function deleteSession(sessionId) {
    try {
        await ocDeleteSession(sessionId);
        if (localStorage.getItem('opencode_session_id') === sessionId) {
            localStorage.removeItem('opencode_session_id');
        }
        await fetchAndRenderSessions();
    } catch (err) {
        console.error('Failed to delete session:', err);
    }
}

async function handleNewSession() {
    try {
        const sess = await ocCreateSession('Task Workflow');
        const id = sess.id || sess.session_id;
        localStorage.setItem('opencode_session_id', id);
        window.location.href = '/explore';
    } catch (err) {
        console.error('Failed to create session:', err);
    }
}
