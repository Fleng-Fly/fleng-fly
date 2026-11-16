# Styling

app.css owns shared CSS/custom-property tokens. Page styles are dashboard.css, courses.css, lesson.css, settings.css and leaderboard.css. ai-assistant.css styles chat; star4life.css is an existing additional style asset. There is no Tailwind, compiler or UI framework.

Reuse existing tokens/classes and scope new selectors. Lesson theory supports blank-line blocks, ## headings and - lists; rendering is safe DOM construction, not unrestricted HTML/Markdown.

Check long text, focus, reduced motion and responsive overlap in a browser. DOM tests cannot prove visual fidelity or exact Figma matching. See [responsive design](responsive-design.md).

[Section index](README.md) · [Documentation home](../README.md)

The compact assistant uses ai-assistant.css with a bounded flex layout, a fixed
composer area, internal message/code scrolling and visualViewport positioning.
Assistant Markdown is built with fixed DOM tags and validated http/https/mailto
or root-relative/fragment URLs; raw HTML, images and custom attributes cannot be
created by the renderer. No external renderer or UI dependency is introduced.
