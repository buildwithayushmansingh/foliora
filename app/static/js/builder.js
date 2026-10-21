// Powers the AI & Tech builder form:
//  - adding/removing repeatable rows (skills, projects, certificates, education, experience)
//  - "Fill sample data" buttons for quick template testing
(function () {
    const form = document.getElementById("builderForm");
    if (!form) return;
    if (form.dataset.builderReady) return;   // safety: never attach twice
    form.dataset.builderReady = "1";

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
        if (!container || !tpl) return null;
        const index = nextIndex(container);
        const html = tpl.innerHTML.replaceAll("___I__", "_" + String(index));
        const wrapper = document.createElement("div");
        wrapper.innerHTML = html.trim();
        const row = wrapper.firstElementChild;
        container.appendChild(row);
        return row;
    }

    document.getElementById("addSkillRow")?.addEventListener("click", () => addRow("skillsRows", "tplSkillRow"));
    document.getElementById("addProjectRow")?.addEventListener("click", () => addRow("projectsRows", "tplProjectRow"));
    document.getElementById("addCertRow")?.addEventListener("click", () => addRow("certsRows", "tplCertRow"));
    document.getElementById("addEduRow")?.addEventListener("click", () => addRow("eduRows", "tplEduRow"));
    document.getElementById("addExpRow")?.addEventListener("click", () => addRow("expRows", "tplExpRow"));

    // Event delegation: works for rows present on load AND rows added later.
    form.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-remove-row]");
        if (!btn) return;
        const row = btn.closest("[data-row]");
        if (row) row.remove();
    });

    // ------------------------------------------------------------------
    // Sample data (for quickly testing how the template looks)
    // Edit this object freely to change what the button fills in.
    // ------------------------------------------------------------------
    const CERT_IMG = "img/demo/ayushman/certificates/";
    const SAMPLE = {
        fields: {
            name: "Aarav Mehta",
            title: "AI & Full Stack Developer",
            tagline: "Building smart, fast and useful web products.",
            location: "Noida, India",
            status: "Open to internships",
            about: "I'm a computer science student who loves turning ideas into working products. " +
                "I build web apps with Python and Flask, experiment with machine learning, " +
                "and enjoy learning in public by shipping small projects every month.",
            achievements: "Won 1st place at the College Hackathon 2026\n" +
                "Top 10 finalist at Smart India Hackathon\n" +
                "Solved 300+ problems on LeetCode\n" +
                "Built and deployed 5+ live projects",
            email: "aarav.mehta@example.com",
            github_username: "octocat",
            social_github: "https://github.com/octocat",
            social_linkedin: "https://www.linkedin.com/in/aarav-mehta",
            social_twitter: "https://x.com/aaravmehta",
            social_instagram: "https://instagram.com/aaravmehta",
            social_website: "https://aarav.dev",
        },
        skills: [
            ["Frontend development", "HTML, CSS, JavaScript, Tailwind CSS, React"],
            ["Backend development", "Python, Flask, REST APIs, Node.js"],
            ["Databases", "MySQL, SQLite, MongoDB"],
            ["AI & Data", "Pandas, NumPy, Scikit-learn, Generative AI"],
            ["Tools & Deployment", "Git, GitHub, Render, Postman, VS Code"],
        ],
        projects: [
            {
                name: "Foliora", icon: "🚀", desc: "A platform where anyone can pick a portfolio template, add their details and go live without writing code.",
                tech: "Python, Flask, SQLite, Jinja", github: "https://github.com/octocat/foliora", live: "https://example.com/foliora"
            },
            {
                name: "AI Study Buddy", icon: "🤖", desc: "A chatbot that turns lecture notes into quizzes and summaries using a large language model.",
                tech: "Python, Flask, Gemini API", github: "https://github.com/octocat/study-buddy", live: ""
            },
            {
                name: "Expense Tracker", icon: "💸", desc: "Track daily spending with charts, monthly budgets and CSV export.",
                tech: "JavaScript, Chart.js, MySQL", github: "https://github.com/octocat/expense-tracker", live: "https://example.com/expenses"
            },
            {
                name: "Weather Dashboard", icon: "🌦️", desc: "Live weather and 5-day forecast for any city using a public API.",
                tech: "HTML, CSS, JavaScript, REST API", github: "https://github.com/octocat/weather", live: ""
            },
        ],
        // Images come from the demo images already inside app/static/img/demo/...
        certificates: [
            { name: "Full Stack Web Development", issuer: "Coursera", tags: "Web, Python", detail: "Completed a 6-month hands-on course covering frontend, backend and deployment.", image: CERT_IMG + "course-completion-certificate.png" },
            { name: "Google Cloud Fundamentals", issuer: "Google", tags: "Cloud, Google", detail: "Core cloud concepts and services.", image: CERT_IMG + "google-certificate.png" },
            { name: "Hackathon Winner", issuer: "College Tech Fest", tags: "Hackathon, Team", detail: "First place among 60+ teams.", image: CERT_IMG + "gold-certificate.png" },
        ],
        education: [
            { degree: "B.Tech Computer Science (AI & ML)", institution: "Sample Institute of Technology", year: "2024–2028", desc: "Currently in 2nd year, CGPA 8.5." },
            { degree: "Class XII (Science)", institution: "Sample Public School", year: "2022–2024", desc: "Scored 92%." },
        ],
        experience: [
            { role: "Frontend Intern", company: "Sample Tech Pvt. Ltd.", duration: "Jun–Aug 2026", desc: "Built responsive dashboard pages and improved page load time by 30%." },
            { role: "Freelance Web Developer", company: "Self-employed", duration: "2025–Present", desc: "Designed and shipped websites for 4 local businesses." },
        ],
        profileImage: "img/demo/ayushman/profile.jpg",
    };

    function setVal(name, value) {
        const el = form.elements[name];
        if (el) el.value = value;
    }

    function clearRows(containerId) {
        const c = document.getElementById(containerId);
        if (c) c.innerHTML = "";
    }

    function fill(row, map) {
        // map: { "name-prefix": value } — finds the input whose name starts with the prefix
        Object.entries(map).forEach(([prefix, value]) => {
            const el = row.querySelector('[name^="' + prefix + '_"]');
            if (el) el.value = value;
        });
    }

    async function setProfilePhoto(path) {
        // Put the demo photo into the file input, as if the user picked it.
        try {
            const input = form.elements["profile_image"];
            if (!input || typeof DataTransfer === "undefined") return;
            const url = "/static/" + path;
            const res = await fetch(url);
            if (!res.ok) return;
            const blob = await res.blob();
            const file = new File([blob], "sample-profile.jpg", { type: blob.type || "image/jpeg" });
            const dt = new DataTransfer();
            dt.items.add(file);
            input.files = dt.files;
            const rm = form.elements["remove_profile_image"];
            if (rm) rm.checked = false;
        } catch (err) {
            // Photo is optional — ignore if it can't be attached.
        }
    }

    async function fillSampleData() {
        Object.entries(SAMPLE.fields).forEach(([k, v]) => setVal(k, v));

        clearRows("skillsRows");
        SAMPLE.skills.forEach(([category, items]) => {
            fill(addRow("skillsRows", "tplSkillRow"), { skill_category: category, skill_items: items });
        });

        clearRows("projectsRows");
        SAMPLE.projects.forEach((p) => {
            fill(addRow("projectsRows", "tplProjectRow"), {
                project_name: p.name, project_icon: p.icon, project_desc: p.desc,
                project_tech: p.tech, project_github: p.github, project_live: p.live,
            });
        });

        clearRows("certsRows");
        SAMPLE.certificates.forEach((c) => {
            const row = addRow("certsRows", "tplCertRow");
            fill(row, { cert_name: c.name, cert_issuer: c.issuer, cert_tags: c.tags, cert_detail: c.detail });
            // The server keeps an existing image path when no new file is uploaded.
            const idx = row.querySelector('[name^="cert_name_"]').name.match(/_(\d+)$/)[1];
            const hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = "cert_existing_" + idx;
            hidden.value = c.image;
            row.appendChild(hidden);
            const hint = row.querySelector(".build-hint");
            if (hint) hint.textContent = "Sample certificate image attached (choose a file to replace it).";
        });

        clearRows("eduRows");
        SAMPLE.education.forEach((e) => {
            fill(addRow("eduRows", "tplEduRow"), {
                edu_degree: e.degree, edu_institution: e.institution, edu_year: e.year, edu_desc: e.desc,
            });
        });

        clearRows("expRows");
        SAMPLE.experience.forEach((x) => {
            fill(addRow("expRows", "tplExpRow"), {
                exp_role: x.role, exp_company: x.company, exp_duration: x.duration, exp_desc: x.desc,
            });
        });

        await setProfilePhoto(SAMPLE.profileImage);
    }

    document.getElementById("fillSampleBtn")?.addEventListener("click", async (e) => {
        const btn = e.currentTarget;
        const old = btn.textContent;
        btn.disabled = true;
        await fillSampleData();
        btn.disabled = false;
        btn.textContent = "Filled ✓";
        setTimeout(() => { btn.textContent = old; }, 1500);
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    document.getElementById("fillSampleSaveBtn")?.addEventListener("click", async (e) => {
        e.currentTarget.disabled = true;
        await fillSampleData();
        form.requestSubmit();   // same as clicking "Save and preview"
    });
})();