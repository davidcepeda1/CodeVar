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

function codevarShowChartTooltip(evt, dateStr, count) {
    const tooltip = document.getElementById("chart-tooltip");
    if (!tooltip) return;

    const label = count === 1 ? "1 evento" : count + " eventos";
    tooltip.textContent = dateStr + " — " + label;

    const barRect = evt.target.getBoundingClientRect();
    const containerRect = tooltip.parentElement.getBoundingClientRect();

    tooltip.style.left = barRect.left - containerRect.left + barRect.width / 2 + "px";
    tooltip.style.top = barRect.top - containerRect.top + "px";
    tooltip.classList.add("chart-tooltip-visible");
}

function codevarHideChartTooltip() {
    const tooltip = document.getElementById("chart-tooltip");
    if (tooltip) tooltip.classList.remove("chart-tooltip-visible");
}
