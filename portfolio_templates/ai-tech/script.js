// Count-up stats, triggered once when the hero stats come into view
const counters = document.querySelectorAll('[data-count]');
let counted = false;

function runCounters() {
    if (counted) return;
    counted = true;
    counters.forEach(el => {
        const target = parseInt(el.getAttribute('data-count'), 10);
        const duration = 900;
        const start = performance.now();
        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target);
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });
}

const statsSection = document.querySelector('.hero-stats');
if (statsSection) {
    const obs = new IntersectionObserver(
        entries => entries.forEach(e => { if (e.isIntersecting) runCounters(); }),
        { threshold: 0.4 }
    );
    obs.observe(statsSection);
}

// ---------- Certificate showcase: click a thumbnail to feature it ----------
(function () {
    const thumbs = document.querySelectorAll('.cert-thumb');
    if (!thumbs.length) return;

    const featuredImg = document.getElementById('certFeaturedImg');
    const featuredTitle = document.getElementById('certFeaturedTitle');
    const featuredIssuer = document.getElementById('certFeaturedIssuer');
    const featuredDesc = document.getElementById('certFeaturedDesc');
    const featuredTags = document.getElementById('certFeaturedTags');
    const featuredLink = document.getElementById('certFeaturedLink');

    thumbs.forEach(thumb => {
        thumb.addEventListener('click', () => {
            // swap the featured panel's content to match the clicked thumbnail
            featuredImg.src = thumb.dataset.image;
            featuredImg.alt = thumb.dataset.title;
            featuredTitle.textContent = thumb.dataset.title;
            featuredIssuer.textContent = thumb.dataset.issuer;
            featuredDesc.textContent = thumb.dataset.desc;
            featuredLink.href = thumb.dataset.image;

            featuredTags.innerHTML = '';
            thumb.dataset.tags.split(',').forEach(tag => {
                const span = document.createElement('span');
                span.className = 'tag';
                span.textContent = tag;
                featuredTags.appendChild(span);
            });

            thumbs.forEach(t => t.classList.remove('active'));
            thumb.classList.add('active');
        });
    });
})();

// ---------- Hero background: mouse + scroll parallax ----------
// Skipped entirely if the person has requested reduced motion.
(function () {
    const hero = document.getElementById('top');
    const bgLayer = document.getElementById('heroBgLayer');
    const heroOrbit = document.querySelector('.hero-orbit');
    if (!hero || !bgLayer) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) return;

    const isTouchDevice = window.matchMedia('(pointer: coarse)').matches;

    let mouseX = 0, mouseY = 0;   // -1..1, normalized to hero center
    let smoothX = 0, smoothY = 0; // eased toward mouseX/Y each frame

    if (!isTouchDevice) {
        hero.addEventListener('mousemove', e => {
            const rect = hero.getBoundingClientRect();
            mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
            mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;
        });
    }

    function tick() {
        smoothX += (mouseX - smoothX) * 0.04;
        smoothY += (mouseY - smoothY) * 0.04;

        // background drifts upward as the person scrolls past the hero
        const scrollShift = Math.min(window.scrollY, hero.offsetHeight) * 0.06;

        bgLayer.style.transform = `translate(${smoothX * 10}px, ${smoothY * 10 - scrollShift}px)`;
        if (heroOrbit) {
            // rings move less than the background text — creates a depth feel
            heroOrbit.style.transform = `translate(${smoothX * 4}px, ${smoothY * 4}px)`;
        }
        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
})();

// ---------- Custom cursor: scanner reticle + trailing dust ----------
// Skipped entirely on touch devices (no mouse to track)
const isTouch = window.matchMedia('(pointer: coarse)').matches;

if (!isTouch) {
    const cursor = document.getElementById('cursor');
    const cursorLabel = document.getElementById('cursorLabel');

    // crosshair follows the pointer instantly (feels precise, no lag)
    window.addEventListener('mousemove', e => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });

    // hide reticle when it leaves the window
    document.addEventListener('mouseleave', () => { cursor.style.opacity = '0'; });
    document.addEventListener('mouseenter', () => { cursor.style.opacity = '1'; });

    // brackets snap in + optional label on anything clickable
    const hoverTargets = 'a, button, .circuit-card, .orbit-card';
    document.querySelectorAll(hoverTargets).forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.classList.add('active');
            const text = el.dataset.cursorText;
            if (text) {
                cursorLabel.textContent = text;
                cursorLabel.classList.add('visible');
            }
        });
        el.addEventListener('mouseleave', () => {
            cursor.classList.remove('active');
            cursorLabel.classList.remove('visible');
        });
    });

    // comet-style trailing dust: a small pool of squares that chase the pointer
    // with staggered easing, each one lagging slightly more than the last
    const TRAIL_LENGTH = 6;
    const trailDots = [];
    for (let i = 0; i < TRAIL_LENGTH; i++) {
        const dot = document.createElement('div');
        dot.className = 'cursor-trail';
        dot.style.opacity = String(0.5 - i * 0.07);
        dot.style.transform = `translate(-50%,-50%) rotate(45deg) scale(${1 - i * 0.12})`;
        document.body.appendChild(dot);
        trailDots.push({ el: dot, x: 0, y: 0 });
    }

    let pointerX = 0, pointerY = 0;
    window.addEventListener('mousemove', e => {
        pointerX = e.clientX;
        pointerY = e.clientY;
    });

    function animateTrail() {
        let targetX = pointerX;
        let targetY = pointerY;
        trailDots.forEach(dot => {
            dot.x += (targetX - dot.x) * 0.35;
            dot.y += (targetY - dot.y) * 0.35;
            dot.el.style.left = dot.x + 'px';
            dot.el.style.top = dot.y + 'px';
            targetX = dot.x;
            targetY = dot.y;
        });
        requestAnimationFrame(animateTrail);
    }
    animateTrail();
}

// ---------- Interface sound ----------
// Small synthesized tunes via Web Audio — no audio files needed.
// Off by default; the person turns it on with the speaker button.
(function () {
    const toggle = document.getElementById('soundToggle');
    if (!toggle) return;

    let audioCtx = null;
    let soundOn = localStorage.getItem('soundOn') === 'true';
    toggle.setAttribute('aria-pressed', String(soundOn));

    function getCtx() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') audioCtx.resume();
        return audioCtx;
    }

    // plays a short sequence of notes — lets hover/click/confirm each have
    // their own distinct little tune instead of one flat beep
    function playTune(frequencies, noteDuration, volume, waveType) {
        if (!soundOn) return;
        const ctx = getCtx();
        const vol = volume * (window.siteVolume ?? 0.85);
        frequencies.forEach((freq, i) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = waveType;
            osc.frequency.value = freq;
            const startTime = ctx.currentTime + i * noteDuration * 0.85;
            gain.gain.setValueAtTime(vol, startTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, startTime + noteDuration);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(startTime);
            osc.stop(startTime + noteDuration);
        });
    }

    function hoverTune() { playTune([660, 880], 0.07, 0.10, 'triangle'); }
    function clickTune() { playTune([740, 494], 0.09, 0.16, 'sine'); }
    function onTune() { playTune([523, 659, 784], 0.1, 0.18, 'sine'); } // confirmation when turning sound ON

    toggle.addEventListener('click', () => {
        soundOn = !soundOn;
        localStorage.setItem('soundOn', String(soundOn));
        toggle.setAttribute('aria-pressed', String(soundOn));
        if (soundOn) onTune();
    });

    // distinct hover chime + a louder, different click chime on interactive elements
    document.querySelectorAll('a, button').forEach(el => {
        el.addEventListener('mouseenter', hoverTune);
        el.addEventListener('click', clickTune);
    });
})();
// ---------- Profile menu: theme switch + sound + volume ----------
(function () {
    const profileMenu = document.getElementById('profileMenu');
    const avatarBtn = document.getElementById('profileAvatarBtn');
    const themeButtons = document.querySelectorAll('.theme-swatch');
    const volumeSlider = document.getElementById('volumeSlider');
    if (!profileMenu || !avatarBtn) return;

    // open/close dropdown — profile menu now lives in the always-visible top bar,
    // so it no longer needs to force the bottom nav open
    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = profileMenu.classList.toggle('open');
        avatarBtn.setAttribute('aria-expanded', String(isOpen));
    });
    document.addEventListener('click', (e) => {
        if (!profileMenu.contains(e.target)) {
            profileMenu.classList.remove('open');
            avatarBtn.setAttribute('aria-expanded', 'false');
        }
    });

    // theme switching — 'cinematic' is the default, so it needs no data-theme attribute
    const themeSelect = document.getElementById('themeSelect');
    const themeLabel = document.getElementById('currentThemeLabel');
    const THEME_NAMES = { cinematic: 'Dark', light: 'Light', terminal: 'Terminal' };

    function applyTheme(theme) {
        if (theme === 'cinematic') {
            document.documentElement.removeAttribute('data-theme');
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        themeButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
        if (themeLabel) themeLabel.textContent = THEME_NAMES[theme] || 'Dark';
        localStorage.setItem('siteTheme', theme);
    }

    const savedTheme = localStorage.getItem('siteTheme') || 'cinematic';
    applyTheme(savedTheme);

    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            applyTheme(btn.dataset.theme);
            if (themeSelect) themeSelect.removeAttribute('open'); // collapse back to one line
        });
    });

    // volume — read by playTune() in the sound-toggle script above
    const savedVolume = localStorage.getItem('soundVolume');
    window.siteVolume = savedVolume !== null ? parseInt(savedVolume, 10) / 100 : 0.85;

    if (volumeSlider) {
        volumeSlider.value = Math.round(window.siteVolume * 100);
        volumeSlider.addEventListener('input', () => {
            window.siteVolume = volumeSlider.value / 100;
            localStorage.setItem('soundVolume', volumeSlider.value);
        });
    }
})();

// ---------- Scroll-reveal for section content ----------
(function () {
    const revealEls = document.querySelectorAll('.reveal-on-scroll');
    if (!revealEls.length) return;

    const obs = new IntersectionObserver(
        entries => entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                obs.unobserve(entry.target);
            }
        }),
        { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
    );
    revealEls.forEach(el => obs.observe(el));
})();

// ---------- Sections menu: icon in the top bar opens a page list ----------
(function () {
    const trigger = document.getElementById('sectionsTrigger');
    const overlay = document.getElementById('sectionsOverlay');
    const closeBtn = document.getElementById('sectionsClose');
    if (!trigger || !overlay) return;

    function open() {
        overlay.hidden = false;
        trigger.setAttribute('aria-expanded', 'true');
    }
    function close() {
        overlay.hidden = true;
        trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', () => {
        overlay.hidden ? open() : close();
    });
    if (closeBtn) closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && !overlay.hidden) close();
    });
})();

// ---------- Terminal overlay: opens with Ctrl+K / Cmd+K, runs real commands ----------
// Reads window.PORTFOLIO (set from the template's data — never hardcoded here),
// so the same commands work for any portfolio built from this template.
(function () {
    const overlay = document.getElementById('termOverlay');
    const termBody = document.getElementById('termBody');
    const termInput = document.getElementById('termInput');
    const trigger = document.getElementById('cmdkTrigger');
    const escLabel = document.querySelector('.term-esc');
    if (!overlay || !termBody || !termInput) return;

    const P = window.PORTFOLIO || {};
    const username = (P.username || 'dev').toLowerCase();

    function updateThemeLabel(theme) {
        const label = document.getElementById('currentThemeLabel');
        if (!label) return;
        const names = { cinematic: 'Dark', light: 'Light', terminal: 'Terminal' };
        label.textContent = names[theme] || 'Dark';
    }

    function setTheme(theme) {
        if (theme === 'dark' || theme === 'cinematic') {
            document.documentElement.removeAttribute('data-theme');
            theme = 'cinematic';
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
        localStorage.setItem('siteTheme', theme);
        document.querySelectorAll('.theme-swatch').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === theme);
        });
        updateThemeLabel(theme);
    }

    // sections actually present on this page (from data-driven conditional rendering)
    function availableSections() {
        return Array.from(document.querySelectorAll('main [id], body > section[id]'))
            .map(el => el.id)
            .filter((v, i, a) => a.indexOf(v) === i);
    }

    const commands = {
        help() {
            return 'Available commands: help, whoami, about, skills, projects, certificates, contact, resume, github, linkedin, theme <dark|light|terminal>, open <section>, clear';
        },
        whoami() { return username + '@developer'; },
        about() {
            return P.about || P.tagline || 'No about information provided.';
        },
        skills() {
            const flat = (P.skills || []).flatMap(g => g.items || []);
            return flat.length ? flat.join(', ') : 'No skills listed.';
        },
        projects() {
            const list = P.projects || [];
            if (!list.length) return 'No projects listed.';
            return list.map(p => `${p.name} — ${p.description || ''}`).join('\n');
        },
        certificates() {
            const list = P.certificates || [];
            if (!list.length) return 'No certificates listed.';
            return list.map(c => `${c.name} (${c.issuer || 'Issuer not specified'})`).join('\n');
        },
        contact() {
            const s = P.social_links || {};
            const lines = [];
            if (P.email) lines.push('email: ' + P.email);
            if (s.github) lines.push('github: ' + s.github.replace('https://', ''));
            if (s.linkedin) lines.push('linkedin: ' + s.linkedin.replace('https://', ''));
            return lines.length ? lines.join('\n') : 'No contact details provided.';
        },
        resume() {
            if (P.resume_url) { window.open(P.resume_url, '_blank', 'noopener'); return 'Opening resume...'; }
            return 'No resume uploaded yet.';
        },
        github() {
            const url = (P.social_links || {}).github;
            if (url) { window.open(url, '_blank', 'noopener'); return 'Opening GitHub...'; }
            return 'No GitHub link provided.';
        },
        linkedin() {
            const url = (P.social_links || {}).linkedin;
            if (url) { window.open(url, '_blank', 'noopener'); return 'Opening LinkedIn...'; }
            return 'No LinkedIn link provided.';
        },
        clear() {
            termBody.innerHTML = '';
            return null;
        }
    };

    function printLine(text, cls) {
        const div = document.createElement('div');
        div.className = 'term-line' + (cls ? ' ' + cls : '');
        div.textContent = text;
        termBody.appendChild(div);
        termBody.scrollTop = termBody.scrollHeight;
    }

    function runCommand(raw) {
        const trimmed = raw.trim();
        if (!trimmed) return;
        printLine(trimmed, 'term-cmd');

        const parts = trimmed.split(/\s+/);
        const cmd = parts[0].toLowerCase();

        if (cmd === 'open' && parts[1]) {
            const target = parts[1].toLowerCase();
            const sections = availableSections();
            const match = target === 'home' ? 'top' : target;
            if (sections.includes(match)) {
                printLine('Opening ' + target + '...');
                const el = document.getElementById(match);
                if (el) setTimeout(() => el.scrollIntoView({ behavior: 'smooth' }), 150);
            } else {
                printLine("No section named '" + target + "' — try " + sections.join(', '), 'term-error');
            }
            return;
        }

        if (cmd === 'theme' && parts[1]) {
            const target = parts[1].toLowerCase();
            if (['dark', 'cinematic', 'light', 'terminal'].includes(target)) {
                setTheme(target);
                printLine('Theme set to ' + target + '.');
            } else {
                printLine("Unknown theme '" + target + "' — try dark, light or terminal", 'term-error');
            }
            return;
        }

        if (commands[cmd]) {
            const out = commands[cmd]();
            if (out) printLine(out);
            return;
        }

        printLine("command not found: " + cmd + " — type 'help' for available commands", 'term-error');
    }

    function open() {
        overlay.hidden = false;
        setTimeout(() => termInput.focus(), 10);
    }
    function close() {
        overlay.hidden = true;
    }

    termInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            runCommand(termInput.value);
            termInput.value = '';
        } else if (e.key === 'Escape') {
            close();
        }
    });

    const termWindow = document.querySelector('.term-window');
    if (termWindow) {
        termWindow.addEventListener('click', () => termInput.focus());
    }

    overlay.addEventListener('click', e => { if (e.target === overlay) close(); });
    if (escLabel) escLabel.addEventListener('click', close);

    document.addEventListener('keydown', e => {
        if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            overlay.hidden ? open() : close();
        }
        if (e.key === 'Escape' && !overlay.hidden) close();
    });

    if (trigger) trigger.addEventListener('click', open);
})();
// ---------- GitHub Activity: live data from GitHub's public API ----------
// Username comes from the portfolio data (set as a data attribute on #github),
// never hardcoded — this is what makes the section reusable per user.
(function () {
    const section = document.getElementById('github');
    const heatmap = document.getElementById('ghHeatmap');
    const monthsRow = document.getElementById('ghMonths');
    const reposEl = document.getElementById('ghRepos');
    const langsEl = document.getElementById('ghLangs');
    if (!section || !heatmap) return;

    const USERNAME = section.dataset.ghUsername;
    if (!USERNAME) return;

    // repo count + distinct languages, for the stats row — GitHub's public REST API
    fetch(`https://api.github.com/users/${USERNAME}/repos?per_page=100`)
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(repos => {
            if (reposEl) reposEl.textContent = repos.length;
            const langs = new Set(repos.map(r => r.language).filter(Boolean));
            if (langsEl) langsEl.textContent = langs.size;
        })
        .catch(() => {
            if (reposEl) reposEl.textContent = '—';
            if (langsEl) langsEl.textContent = '—';
        });

    // contribution calendar — GitHub doesn't expose this without login,
    // so this uses a well-known public community API instead
    const tooltip = document.getElementById('ghTooltip');
    const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    function showTooltip(e, text) {
        if (!tooltip) return;
        tooltip.textContent = text;
        tooltip.hidden = false;
        tooltip.style.left = e.clientX + 'px';
        tooltip.style.top = e.clientY + 'px';
    }
    function hideTooltip() {
        if (tooltip) tooltip.hidden = true;
    }

    fetch(`https://github-contributions-api.jogruber.de/v4/${USERNAME}?y=last`)
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(data => {
            const all = data.contributions || [];
            const recent = all.slice(-182);
            if (!recent.length) return Promise.reject();

            // pad the front so day-of-week rows line up correctly (row 0 = Sunday)
            const firstDow = new Date(recent[0].date + 'T00:00:00').getDay();
            const padded = Array(firstDow).fill(null).concat(recent);
            const weekCount = Math.ceil(padded.length / 7);

            heatmap.innerHTML = '';
            heatmap.style.gridTemplateColumns = `repeat(${weekCount}, 14px)`;

            padded.forEach(day => {
                const cell = document.createElement('div');
                cell.className = 'gh-cell';
                if (!day) {
                    cell.classList.add('pad');
                } else {
                    const c = day.count;
                    if (c === 0) cell.classList.add('l0');
                    else if (c <= 2) cell.classList.add('l1');
                    else if (c <= 5) cell.classList.add('l2');
                    else if (c <= 9) cell.classList.add('l3');
                    else cell.classList.add('l4');
                    const niceDate = new Date(day.date + 'T00:00:00')
                        .toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                    const text = `${day.count} contribution${day.count === 1 ? '' : 's'} on ${niceDate}`;
                    cell.addEventListener('mouseenter', e => showTooltip(e, text));
                    cell.addEventListener('mousemove', e => showTooltip(e, text));
                    cell.addEventListener('mouseleave', hideTooltip);
                }
                heatmap.appendChild(cell);
            });

            // month labels — one per week-column, aligned via the same column count
            if (monthsRow) {
                monthsRow.innerHTML = '';
                monthsRow.style.gridTemplateColumns = `repeat(${weekCount}, 14px)`;
                let lastMonth = -1;
                for (let w = 0; w < weekCount; w++) {
                    let label = '';
                    for (let r = 0; r < 7; r++) {
                        const entry = padded[w * 7 + r];
                        if (entry) {
                            const m = new Date(entry.date + 'T00:00:00').getMonth();
                            if (m !== lastMonth) { label = MONTH_NAMES[m]; lastMonth = m; }
                            break;
                        }
                    }
                    const span = document.createElement('span');
                    span.textContent = label;
                    monthsRow.appendChild(span);
                }
            }

            const total = all.reduce((sum, d) => sum + d.count, 0);
            const heading = document.getElementById('ghContribHeading');
            if (heading) heading.textContent = `${total} contributions in the last year`;
        })
        .catch(() => {
            heatmap.classList.add('gh-heatmap--empty');
            heatmap.innerHTML = '<div class="gh-error">Live activity data is unavailable right now — <a href="https://github.com/' + USERNAME + '" target="_blank" rel="noopener">view the profile directly</a>.</div>';
        });
})();
// ---------- Boot screen: code initialization intro ----------
(function () {
    const screen = document.getElementById('bootScreen');
    if (!screen || screen.classList.contains('boot-skip-instant')) return;

    const linesEl = document.getElementById('bootLines');
    const fillEl = document.getElementById('bootProgressFill');
    const pctEl = document.getElementById('bootProgressPct');
    const skipBtn = document.getElementById('bootSkip');

    // reflects this actual portfolio's real features — nothing invented
    const BOOT_LINES = [
        'Initializing developer environment...',
        'Loading theme engine...',
        'Mounting developer identity...',
        'Connecting to GitHub...',
        'Loading projects...',
        'Indexing certificates...',
        'Starting command terminal...',
        'Preparing interface audio...',
        'Compiling contact channel...',
        'Verifying configuration...'
    ];

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function finish() {
        screen.classList.add('boot-hide');
        setTimeout(() => { screen.style.display = 'none'; }, 650);
    }

    if (reduceMotion) {
        finish(); // respect reduced motion — skip straight to Home, no flashing sequence
        return;
    }

    let lineIndex = 0;
    const totalSteps = BOOT_LINES.length + 2; // + verify + success steps

    function updateProgress(step) {
        const pct = Math.min(Math.round((step / totalSteps) * 100), 100);
        fillEl.style.width = pct + '%';
        pctEl.textContent = pct + '%';
    }

    function typeLine(text, num, onDone) {
        const row = document.createElement('div');
        row.className = 'boot-line';
        const numSpan = document.createElement('span');
        numSpan.className = 'boot-line-num';
        numSpan.textContent = String(num).padStart(2, '0');
        const textSpan = document.createElement('span');
        row.appendChild(numSpan);
        row.appendChild(textSpan);
        linesEl.appendChild(row);
        requestAnimationFrame(() => row.classList.add('boot-line-in'));

        let i = 0;
        const speed = 9; // ms per character — fast, fits the ~5s total budget
        const interval = setInterval(() => {
            textSpan.textContent = text.slice(0, i + 1);
            i++;
            if (i >= text.length) {
                clearInterval(interval);
                onDone();
            }
        }, speed);
    }

    function runNext() {
        if (lineIndex >= BOOT_LINES.length) {
            showVerification();
            return;
        }
        updateProgress(lineIndex);
        typeLine(BOOT_LINES[lineIndex], lineIndex + 1, () => {
            lineIndex++;
            setTimeout(runNext, 40);
        });
    }

    function showVerification() {
        updateProgress(BOOT_LINES.length);
        const row = document.createElement('div');
        row.className = 'boot-line boot-verify';
        row.textContent = 'Verifying portfolio...';
        linesEl.appendChild(row);
        requestAnimationFrame(() => row.classList.add('boot-line-in'));
        setTimeout(showSuccess, 350);
    }

    function showSuccess() {
        updateProgress(BOOT_LINES.length + 1);
        const row = document.createElement('div');
        row.className = 'boot-line boot-success';
        row.innerHTML = '<span class="boot-check">✓</span>Access granted — initialization complete';
        linesEl.appendChild(row);
        requestAnimationFrame(() => row.classList.add('boot-line-in'));
        setTimeout(finish, 500);
    }

    skipBtn.addEventListener('click', finish);
    skipBtn.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); finish(); }
    });

    runNext();
})();
// ---------- Fast typewriter effect for main headings ----------
(function () {
    const targets = document.querySelectorAll('.type-target');
    if (!targets.length) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    targets.forEach(el => {
        const text = el.innerText; // preserves <br> as a line break
        if (reduceMotion) {
            el.classList.remove('color-hidden');
            el.style.color = '';
            return;
        }

        const lines = text.split('\n');
        el.textContent = '';
        el.style.color = ''; // reveal as characters are typed in

        let li = 0, ci = 0;
        const speed = 35; // ms per character — fast, ~2-3s for these headings

        function step() {
            if (li >= lines.length) return;
            const line = lines[li];
            if (ci < line.length) {
                el.append(line[ci]);
                ci++;
                setTimeout(step, speed);
            } else {
                li++;
                ci = 0;
                if (li < lines.length) {
                    el.append(document.createElement('br'));
                    setTimeout(step, speed);
                }
            }
        }
        step();
    });
})();