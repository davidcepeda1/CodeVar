function codevarCopyStackTrace(button) {
    const pre = button.nextElementSibling;
    navigator.clipboard.writeText(pre.textContent).then(() => {
        const original = button.textContent;
        button.textContent = "Copiado";
        setTimeout(() => {
            button.textContent = original;
        }, 1500);
    });
}
