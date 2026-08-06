function codevarCopyText(button, text) {
    navigator.clipboard.writeText(text).then(() => {
        const label = button.querySelector(".copy-label") || button;
        const original = label.textContent;
        label.textContent = "Copiado";
        setTimeout(() => {
            label.textContent = original;
        }, 1500);
    });
}

function codevarCopyById(button, elementId) {
    codevarCopyText(button, document.getElementById(elementId).textContent);
}

function codevarCopyStackTrace(button) {
    const pre = button.nextElementSibling;
    codevarCopyText(button, pre.textContent);
}
