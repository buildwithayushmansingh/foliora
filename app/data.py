"""Static content for Phase 1. Later phases replace this with database models."""

HOW_IT_WORKS = [
    ("Choose a design", "Browse portfolio designs made for developers, students and creatives."),
    ("Add your details", "Fill in your bio, skills, projects and certificates. No code involved."),
    ("Generate", "Your details flow into the design you picked. Sections you skip disappear."),
    ("Launch", "Get a portfolio link you can put on your resume and share anywhere."),
]

PROBLEMS = [
    ("No coding background", "Most people who need a portfolio never learned HTML, CSS or JavaScript."),
    ("No time", "Job hunts and deadlines leave little room to build a site from scratch."),
    ("No design eye", "A portfolio that looks unfinished can cost you the interview."),
    ("No deployment know-how", "Hosting, domains and Git are a wall for first-time builders."),
]

FEATURED_PORTFOLIO = {
    "owner": "Ayushman Singh",
    "type": "Developer Portfolio",
    "role": "Full Stack Web Developer",
    "description": "An interactive developer portfolio with a boot-screen intro, three color themes, "
                   "a live GitHub activity feed and a built-in AI assistant.",
    "tech": ["HTML", "CSS", "JavaScript", "Python", "Flask", "SQLite"],
    "stats": [("6", "Pages"), ("4", "Projects"), ("4", "Certificates")],
    "sections": [
        ("About", "Bio, education and current status"),
        ("Skills", "Six skill groups from frontend to AI and data"),
        ("Projects", "Project cards with tech stack and GitHub links"),
        ("Certificates", "Certificate images with issuer details"),
        ("GitHub activity", "Live feed of recent commits and repositories"),
        ("Contact", "Email and social links"),
        ("Developer ID", "A shareable ID card with level and XP"),
    ],
    "features": [
        "Boot-screen intro and animated background",
        "Three switchable color themes",
        "Command palette and built-in terminal",
        "AI assistant that answers from portfolio data",
        "Developer ID card with XP and levels",
        "Responsive on desktop, tablet and mobile",
    ],
}

UPCOMING_DESIGNS = [
    ("Student", "Clean and resume-first, built for internships and campus hiring."),
    ("Creative", "Bold layouts for designers and visual storytellers."),
    ("AI and Tech", "Project-heavy pages for data and AI builders."),
]
