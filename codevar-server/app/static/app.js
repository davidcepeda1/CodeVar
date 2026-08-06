function codevarCopyStackTrace(button) {
    const pre = button.nextElementSibling;
    const label = button.querySelector(".copy-label") || button;
    navigator.clipboard.writeText(pre.textContent).then(() => {
        const original = label.textContent;
        label.textContent = "Copiado";
        setTimeout(() => {
            label.textContent = original;
        }, 1500);
    });
}
