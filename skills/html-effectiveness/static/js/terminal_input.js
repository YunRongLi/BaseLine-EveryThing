/**
 * terminal_input.js
 *
 * Enhances terminal and agent input elements with modern dynamic resizing and interaction styling.
 */
document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('#terminalInput, #agentInput, #terminal-input');
    
    inputs.forEach(input => {
        // Enforce smooth auto-resizing
        const autoResize = () => {
            input.style.height = 'auto';
            input.style.height = input.scrollHeight + 'px';
        };

        input.addEventListener('input', autoResize);
        
        // Initial setup and resize
        autoResize();
        
        // Focus state styling helper
        input.addEventListener('focus', () => {
            input.classList.add('terminal-focused');
        });
        
        input.addEventListener('blur', () => {
            input.classList.remove('terminal-focused');
        });
    });
});
