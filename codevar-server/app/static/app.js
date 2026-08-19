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

let codevarActiveDateFilter = null;

function codevarFilterEventsByDate(dateStr, hitRect) {
    if (codevarActiveDateFilter === dateStr) {
        codevarClearEventFilter();
        return;
    }
    codevarActiveDateFilter = dateStr;
    codevarApplyEventFilter();

    document.querySelectorAll(".chart-bar-hit").forEach((el) => {
        el.classList.remove("chart-bar-hit-selected");
    });
    if (hitRect) hitRect.classList.add("chart-bar-hit-selected");
}

function codevarClearEventFilter() {
    codevarActiveDateFilter = null;
    codevarApplyEventFilter();
    document.querySelectorAll(".chart-bar-hit").forEach((el) => {
        el.classList.remove("chart-bar-hit-selected");
    });
}

function codevarApplyEventFilter() {
    const events = document.querySelectorAll("#events-list .event");
    let visibleCount = 0;

    events.forEach((el) => {
        const matches = !codevarActiveDateFilter || el.dataset.date === codevarActiveDateFilter;
        el.style.display = matches ? "" : "none";
        if (matches) visibleCount++;
    });

    const statusEl = document.getElementById("events-filter-status");
    if (statusEl) {
        statusEl.style.display = codevarActiveDateFilter ? "" : "none";
        const dateLabel = statusEl.querySelector(".filter-date");
        if (dateLabel) dateLabel.textContent = codevarActiveDateFilter || "";
    }

    const emptyFilteredEl = document.getElementById("events-empty-filtered");
    if (emptyFilteredEl) {
        emptyFilteredEl.style.display = codevarActiveDateFilter && visibleCount === 0 ? "" : "none";
    }
}

function codevarHandleBarKeydown(evt, dateStr, hitRect) {
    if (evt.key === "Enter" || evt.key === " ") {
        evt.preventDefault();
        codevarFilterEventsByDate(dateStr, hitRect);
    }
}
