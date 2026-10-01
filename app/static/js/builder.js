// Powers the AI & Tech builder form: adding/removing repeatable rows
// (skills, projects, certificates) without a page reload.
(function () {
    const form = document.getElementById("builderForm");
    if (!form) return;

    function nextIndex(container) {
        // Highest existing row index + 1, found from any input's name suffix.
        let max = -1;
        container.querySelectorAll("[data-row] input, [data-row] textarea").forEach((el) => {
            const m = el.name.match(/_(\d+)$/);
            if (m) max = Math.max(max, parseInt(m[1], 10));
        });
        return max + 1;
    }

    function addRow(containerId, templateId) {
        const container = document.getElementById(containerId);
        const tpl = document.getElementById(templateId);
        if (!container || !tpl) return;
        const index = nextIndex(container);
        const html = tpl.innerHTML.replaceAll("___I__", "_" + String(index));
        const wrapper = document.createElement("div");
        wrapper.innerHTML = html.trim();
        container.appendChild(wrapper.firstElementChild);
    }

    document.getElementById("addSkillRow")?.addEventListener("click", () => addRow("skillsRows", "tplSkillRow"));
    document.getElementById("addProjectRow")?.addEventListener("click", () => addRow("projectsRows", "tplProjectRow"));
    document.getElementById("addCertRow")?.addEventListener("click", () => addRow("certsRows", "tplCertRow"));

    // Event delegation: works for rows present on load AND rows added later.
    form.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-remove-row]");
        if (!btn) return;
        const row = btn.closest("[data-row]");
        if (row) row.remove();
    });
})();