/**
 * keyboard_shortcuts.js
 *
 * Handles global keyboard shortcuts for the html-effectiveness web interface.
 * Implements Alt+Enter to submit message from active terminal or agent input box.
 */
document.addEventListener('keydown', (event) => {
    if (event.altKey && event.key === 'Enter') {
        const active = document.activeElement;
        if (active && (active.id === 'terminalInput' || active.id === 'agentInput' || active.id === 'terminal-input')) {
            event.preventDefault();
            sendMessageToAgent(active);
        }
    }
});

function sendMessageToAgent(inputEl) {
    if (!inputEl) return;
    const value = inputEl.value.trim();
    if (value === '') return;

    // Trigger the appropriate send function depending on page context
    if (typeof window.sendTerminalMessage === 'function') {
        window.sendTerminalMessage();
    } else if (typeof window.sendAgentMessage === 'function') {
        window.sendAgentMessage();
    } else {
        // Fallback for generic/test context
        console.log('Generic sendMessageToAgent triggered with value:', value);
        inputEl.value = '';
    }
}
