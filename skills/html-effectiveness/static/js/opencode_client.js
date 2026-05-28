/**
 * opencode_client.js
 *
 * Shared client for all html-effectiveness templates.
 * Provides:
 *   - Session lifecycle:  createSession, listSessions, deleteSession
 *   - Prompt execution:   sendPrompt (with structured schema per command type)
 *   - Message polling:    pollForCompletion (returns extracted JSON payload)
 *   - State persistence:  loadState, saveState (via /api/state)
 *   - UI helpers:         appendAgentOutput, setLoading, parseMarkdown
 *
 * All OpenCode REST calls go through /api/opencode/* (proxied by serve_html.py
 * to http://127.0.0.1:4096).
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const OC_BASE = '/api/opencode';

// How often (ms) to poll the message timeline while waiting for agent response
const POLL_INTERVAL_MS = 1500;

// Maximum time (ms) to wait for an agent response before giving up
const POLL_TIMEOUT_MS = 300_000;

// ---------------------------------------------------------------------------
// Session management
// ---------------------------------------------------------------------------

async function ocListSessions() {
    const res = await fetch(`${OC_BASE}/session`);
    if (!res.ok) throw new Error(`listSessions: HTTP ${res.status}`);
    return res.json();
}

async function ocCreateSession(title = 'Task Workflow') {
    const res = await fetch(`${OC_BASE}/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error(`createSession: HTTP ${res.status}`);
    return res.json();
}

async function ocDeleteSession(sessionId) {
    const res = await fetch(`${OC_BASE}/session/${sessionId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`deleteSession: HTTP ${res.status}`);
    return res.json();
}

/** Get or create a session ID, persisting to localStorage. */
async function ocGetOrCreateSessionId() {
    const stored = localStorage.getItem('opencode_session_id');
    if (stored) return stored;

    const created = await ocCreateSession('Task Workflow');
    const id = created.id;
    localStorage.setItem('opencode_session_id', id);
    return id;
}

// ---------------------------------------------------------------------------
// Prompt sending
// ---------------------------------------------------------------------------

/**
 * Send a plain prompt to a session.
 * @param {string} sessionId
 * @param {string} promptText - Full prompt text (including schema instructions)
 * @returns {Promise<object>} - Raw API response
 */
async function ocSendPrompt(sessionId, promptText) {
    const res = await fetch(`${OC_BASE}/session/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            parts: [
                {
                    type: 'text',
                    text: promptText
                }
            ]
        }),
    });
    if (!res.ok) throw new Error(`sendPrompt: HTTP ${res.status}`);
    return res.json();
}

// ---------------------------------------------------------------------------
// Message timeline polling & JSON extraction
// ---------------------------------------------------------------------------

/**
 * Fetch the full message timeline for a session.
 */
async function ocGetMessages(sessionId) {
    const res = await fetch(`${OC_BASE}/session/${sessionId}/message`);
    if (!res.ok) throw new Error(`getMessages: HTTP ${res.status}`);
    return res.json();
}

/**
 * Extract the last JSON block from a message text.
 * Handles ```json ... ``` and bare { ... } patterns using a robust brace-balancing parser.
 */
function ocExtractJson(text) {
    if (!text) return null;

    // Try ```json ... ``` block first
    const fenced = text.match(/```json\s*([\s\S]*?)\s*```/i);
    if (fenced) {
        try { return JSON.parse(fenced[1]); } catch (_) {}
    }

    // Try bare ```...``` block
    const bare = text.match(/```\s*([\s\S]*?)\s*```/);
    if (bare) {
        try { return JSON.parse(bare[1]); } catch (_) {}
    }

    // Balance-tracking brace matching to safely locate the valid JSON block
    let braceCount = 0;
    let startIdx = -1;

    for (let i = 0; i < text.length; i++) {
        if (text[i] === '{') {
            if (braceCount === 0) {
                startIdx = i;
            }
            braceCount++;
        } else if (text[i] === '}') {
            if (braceCount > 0) {
                braceCount--;
                if (braceCount === 0 && startIdx !== -1) {
                    const candidate = text.slice(startIdx, i + 1);
                    try {
                        return JSON.parse(candidate);
                    } catch (_) {
                        // Continue searching if this wasn't a valid JSON block
                    }
                }
            }
        }
    }

    return null;
}

/**
 * Poll the message timeline until the last assistant message is complete
 * and contains a JSON block matching expectedEventType.
 *
 * @param {string} sessionId
 * @param {string} expectedEventType   - e.g. 'task_create', 'task_spec_finalize'
 * @param {function} [onChunk]         - Called with the full assistant text on each poll tick
 * @returns {Promise<object>}          - The extracted JSON payload
 */
async function ocPollForCompletion(sessionId, expectedEventType, onChunk) {
    const deadline = Date.now() + POLL_TIMEOUT_MS;

    while (Date.now() < deadline) {
        await _sleep(POLL_INTERVAL_MS);

        let messages;
        try {
            messages = await ocGetMessages(sessionId);
        } catch (_) {
            continue;
        }

        // Find the latest assistant message
        // V1 messages have an 'info' object with the 'role' field
        const assistantMsgs = (messages || []).filter(m => m.info && m.info.role === 'assistant');
        if (assistantMsgs.length === 0) continue;

        const last = assistantMsgs[assistantMsgs.length - 1];

        // Collect all text parts
        const fullText = _extractMessageText(last);

        if (onChunk && fullText) onChunk(fullText);

        // Check if message has finished generating (info.time.completed or info.finish exists)
        const isCompleted = last.info && last.info.time && (last.info.time.completed || last.info.finish);
        if (!isCompleted) continue;

        const parsed = ocExtractJson(fullText);
        if (parsed && (parsed.event_type === expectedEventType || !expectedEventType)) {
            return parsed;
        }
    }

    throw new Error(`Timeout waiting for ${expectedEventType} response`);
}

function _extractMessageText(message) {
    if (!message) return '';
    if (typeof message.content === 'string') return message.content;
    if (Array.isArray(message.parts)) {
        return message.parts
            .filter(p => p.type === 'text')
            .map(p => p.text || '')
            .join('');
    }
    if (Array.isArray(message.content)) {
        return message.content
            .filter(p => p.type === 'text')
            .map(p => p.text || '')
            .join('');
    }
    return '';
}

function _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Structured prompt builders (one per command type)
// Mirrors the prompt templates in skills/html-effectiveness/prompts/
// ---------------------------------------------------------------------------

function ocBuildExplorePrompt(context, references, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    const refSection = _buildRefSection(references);
    return `${langLine} Do NOT use emojis or icons.

${refSection}Analyze the user's context and generate an exploration strategy.
Context: ${context}

You MUST respond ONLY with a JSON block matching this exact schema:
\`\`\`json
{
  "explore": {
    "insights": [
      "[Component Overview] Description of the component/file and its design intent.",
      "[Key Capabilities] Concrete features, APIs, or system flows identified.",
      "[Suggested Next Steps] Recommended files or directories to examine next."
    ]
  },
  "event_type": "task_explore"
}
\`\`\``;
}

function ocBuildCreatePrompt(title, category, goal, context, references, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    const refSection = _buildRefSection(references);
    return `${langLine} Do NOT use emojis or icons.

${refSection}Analyze this task and generate the specifications.
Task Title: ${title}
Category: ${category}
Goal: ${goal}
Context: ${context}

You MUST respond ONLY with a JSON block matching this exact schema:
\`\`\`json
{
  "spec": {
    "sections": [
      {
        "title": "Functional Requirements",
        "items": ["Requirement 1", "Requirement 2"]
      },
      {
        "title": "Technical Constraints",
        "items": ["Constraint 1"]
      }
    ],
    "open_questions": {
      "Most important architectural question (max 3 total)": ""
    }
  },
  "event_type": "task_create"
}
\`\`\`
Provide at least 3-4 sections. Limit open_questions to at most 3. Group related items into cohesive paragraphs. Use light markdown (bold, bullet points) inside item strings if helpful.`;
}

function ocBuildSpecUpdatePrompt(sections, scopingInput, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    const sectionsStr = JSON.stringify(sections, null, 2);
    return `${langLine} Do NOT use emojis or icons.

The user wants to UPDATE the task specifications based on their feedback.
Current Specification Sections:
${sectionsStr}

User's Feedback/Instructions:
${scopingInput}

Analyze the feedback and output the updated specification.
Limit open_questions to at most 3. Group related items into cohesive paragraph strings.
You MUST respond ONLY with a JSON block:
\`\`\`json
{
  "spec": {
    "sections": [
      {"title": "Section Title", "items": ["Item 1", "Item 2"]}
    ],
    "open_questions": {
      "Question 1": ""
    }
  },
  "event_type": "task_spec_update"
}
\`\`\``;
}

function ocBuildSpecFinalizePrompt(sections, scopingInput, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    const sectionsStr = JSON.stringify(sections, null, 2);
    return `${langLine} Do NOT use emojis or icons.

The user has finalized the task specifications and wants to generate the develop architecture.
Final Specification Sections:
${sectionsStr}

User's Scoping Feedback/Instructions:
${scopingInput}

Analyze these specifications and design the Develop architecture, workflow steps, file tree, and core logic snippets.
Limit open_questions to at most 3.
You MUST respond ONLY with a JSON block:
\`\`\`json
{
  "develop": {
    "workflow_steps": ["Step 1: description", "Step 2: description"],
    "file_tree": [
      {"path": "src/main.py", "status": "new"}
    ],
    "code_snippets": [
      {"filename": "src/main.py", "language": "python", "code": "def core_logic():\\n    pass"}
    ],
    "open_questions": {
      "Question 1": ""
    }
  },
  "event_type": "task_spec_finalize"
}
\`\`\``;
}

function ocBuildDevelopUpdatePrompt(workflowSteps, fileTree, codeSnippets, feedbackInput, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    return `${langLine} Do NOT use emojis or icons.

The user wants to UPDATE the develop design and code based on their feedback.
Current Workflow Steps: ${JSON.stringify(workflowSteps, null, 2)}
Current File Tree: ${JSON.stringify(fileTree, null, 2)}
Current Code Snippets (filenames only for brevity): ${JSON.stringify(codeSnippets.map(s => s.filename), null, 2)}

User's Feedback/Instructions:
${feedbackInput}

Analyze the feedback and output the updated develop.
Limit open_questions to at most 3. Group related details into cohesive paragraphs.
You MUST respond ONLY with a JSON block:
\`\`\`json
{
  "develop": {
    "workflow_steps": ["Step 1...", "Step 2..."],
    "file_tree": [{"path": "...", "status": "..."}],
    "code_snippets": [{"filename": "...", "language": "...", "code": "..."}],
    "open_questions": {
      "Question 1...": ""
    }
  },
  "event_type": "task_develop_update"
}
\`\`\``;
}

function ocBuildDevelopFinalizePrompt(workflowSteps, fileTree, codeSnippets, feedbackInput, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    return `${langLine} Do NOT use emojis or icons.

The user has approved the prototype and submitted final implementation instructions.
Please implement the following in the workspace using your file editing tools.

Final Workflow Steps: ${JSON.stringify(workflowSteps, null, 2)}
Final File Tree: ${JSON.stringify(fileTree, null, 2)}
Final Code Snippets: ${JSON.stringify(codeSnippets, null, 2)}
Final Feedback/Instructions: ${feedbackInput}

After implementing the files, provide a completion summary.
You MUST respond ONLY with a JSON block:
\`\`\`json
{
  "completed": {
    "summary_items": ["Summary detail 1", "Summary detail 2"],
    "created_files": ["src/main.py", "tests/test_main.py"],
    "verification_results": ["Test 1: Pass", "Test 2: Pass"]
  },
  "event_type": "task_develop_finalize"
}
\`\`\``;
}

function ocBuildTestingPrompt(feedbackInput, testLogs, codeSnippets, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    return `${langLine} Do NOT use emojis or icons.

The user wants to resolve testing failures (regression/verification).
User Feedback/Instructions: ${feedbackInput}
Failing Test Logs:
${testLogs}
Code Snippets: ${JSON.stringify(codeSnippets, null, 2)}

Analyze the failure and provide remediation steps, then edit the files to fix the issue.
You MUST respond ONLY with a JSON block:
\`\`\`json
{
  "testing": {
    "remediation_plan": ["Step 1", "Step 2"],
    "fixed_files": ["src/main.py"]
  },
  "event_type": "task_testing_remediation"
}
\`\`\``;
}

function ocBuildChatPrompt(userMsg, lang) {
    const langLine = lang === 'zh'
        ? 'CRITICAL: Write all content in Traditional Chinese (zh-TW).'
        : 'Write all content in English.';
    return `${langLine} Do NOT use emojis or icons.

The user says: "${userMsg}"

Please respond naturally and helpfully. You MUST respond ONLY with a JSON block:
\`\`\`json
{
  "chat": "Your textual response here",
  "event_type": "chat"
}
\`\`\``;
}

function _buildRefSection(references) {
    if (!references || references.length === 0) return '';
    const lines = references.map(r => {
        if (r.type === 'local') return `- [LOCAL FILE/DIR] ${r.value}`;
        return `- [URL] ${r.value}`;
    });
    return `REFERENCE MATERIALS (use these as architectural context):\n${lines.join('\n')}\n\n`;
}

// ---------------------------------------------------------------------------
// Workflow state (proxied through serve_html.py to workflow_state.json)
// ---------------------------------------------------------------------------

async function ocLoadState() {
    const res = await fetch('/api/state');
    if (!res.ok) return {};
    const data = await res.json();
    return (data.status === 'success') ? data.state : {};
}

async function ocSaveState(partialState) {
    await fetch('/api/state', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: partialState }),
    });
}

// ---------------------------------------------------------------------------
// UI helpers (shared across templates)
// ---------------------------------------------------------------------------

/**
 * Append a message to the agent console output panel.
 * Accepts plain text with light markdown (bold, bullet points, code blocks).
 */
function ocAppendAgentOutput(containerId, text) {
    const out = document.getElementById(containerId);
    if (!out) return;

    out.style.fontFamily = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
    out.style.fontSize = '0.875rem';
    out.style.lineHeight = '1.5';

    const div = document.createElement('div');
    div.style.marginBottom = '1.5rem';
    div.style.borderBottom = '1px solid var(--gray-200, #e6e6e3)';
    div.style.paddingBottom = '1rem';
    div.innerHTML = ocParseMarkdown(text);

    _styleOutputBlock(div);
    out.appendChild(div);
    out.scrollTop = out.scrollHeight;
}

function _styleOutputBlock(div) {
    div.querySelectorAll('p').forEach(p => {
        p.style.marginBottom = '0.75rem';
        p.style.lineHeight = '1.6';
    });
    div.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach(h => {
        h.style.marginTop = '1rem';
        h.style.marginBottom = '0.5rem';
        h.style.color = 'var(--slate, #141413)';
        h.style.fontWeight = '600';
    });
    div.querySelectorAll('ul,ol').forEach(l => {
        l.style.marginLeft = '1.25rem';
        l.style.marginBottom = '0.75rem';
    });
    div.querySelectorAll('code').forEach(c => {
        if (c.parentElement.tagName !== 'PRE') {
            c.style.fontFamily = 'ui-monospace, Menlo, Consolas, monospace';
            c.style.background = 'var(--gray-200, #e6e6e3)';
            c.style.padding = '0.1rem 0.3rem';
            c.style.borderRadius = '4px';
            c.style.fontSize = '0.8125rem';
        }
    });
    div.querySelectorAll('pre').forEach(pb => {
        pb.style.background = 'var(--slate, #141413)';
        pb.style.color = 'var(--ivory, #FAF9F5)';
        pb.style.padding = '0.75rem';
        pb.style.borderRadius = '6px';
        pb.style.overflowX = 'auto';
        pb.style.marginBottom = '0.75rem';
        pb.querySelectorAll('code').forEach(pc => {
            pc.style.background = 'transparent';
            pc.style.padding = '0';
        });
    });
}

function ocSetLoading(isLoading, btnIds = []) {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) indicator.style.display = isLoading ? 'flex' : 'none';
    btnIds.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = isLoading;
    });
}

function ocLogDebug(message) {
    const pre = document.getElementById('globalDebug');
    if (!pre) return;
    const ts = new Date().toLocaleTimeString();
    pre.textContent = `[${ts}] ${message}\n\n` + pre.textContent;
}

/**
 * Minimal markdown renderer (bold, italic, lists, code blocks, headings).
 */
function ocParseMarkdown(text) {
    if (!text) return '';
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    const codeBlocks = [];
    html = html.replace(/```(?:[a-zA-Z0-9+#-]+)?\n([\s\S]*?)\n```/g, (_, code) => {
        codeBlocks.push(code);
        return `__CODE_${codeBlocks.length - 1}__`;
    });

    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/^#### (.*?)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
    html = html.replace(/^---$/gm, '<hr>');

    const lines = html.split('\n');
    let inList = false;
    let listType = null;
    const out = [];
    for (const line of lines) {
        const t = line.trim();
        if (t.startsWith('- ') || t.startsWith('* ')) {
            if (!inList || listType !== 'ul') {
                if (inList) out.push(`</${listType}>`);
                out.push('<ul>'); inList = true; listType = 'ul';
            }
            out.push(`<li>${t.substring(2)}</li>`);
        } else if (/^\d+\.\s/.test(t)) {
            const m = t.match(/^(\d+)\.\s(.*)/);
            if (!inList || listType !== 'ol') {
                if (inList) out.push(`</${listType}>`);
                out.push('<ol>'); inList = true; listType = 'ol';
            }
            out.push(`<li>${m[2]}</li>`);
        } else {
            if (inList) { out.push(`</${listType}>`); inList = false; listType = null; }
            if (t) {
                if (t.startsWith('<h') || t.startsWith('<hr') || t.startsWith('__CODE_')) {
                    out.push(line);
                } else {
                    out.push(`<p>${line}</p>`);
                }
            } else {
                out.push('');
            }
        }
    }
    if (inList) out.push(`</${listType}>`);

    html = out.join('\n');
    for (let i = 0; i < codeBlocks.length; i++) {
        html = html.replace(`__CODE_${i}__`, `<pre><code>${codeBlocks[i]}</code></pre>`);
    }
    return html;
}
