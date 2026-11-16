# Words navigation and Fleng AI mini chat

Implemented 2026-11-16 on the existing static HTML/CSS/JavaScript frontend.
No backend AI changes, API/model changes, migration, new dependencies, commit,
push or paid API requests were made for this stage. Earlier uncommitted security
work was preserved. The three referenced screenshots were not attached to the
received task, so exact reference matching is not claimed.

## Words

The shared sidebar has one native Words disclosure containing My Words and
Course Words. Active children use aria-current; the disclosure opens on either
word section, including existing personal practice URLs. Mobile focus trapping
excludes links hidden by a collapsed disclosure.

Personal vocabulary retains all existing filters, editing/add flows, reviews,
flashcards, multiple choice, writing, letter tiles and summaries. Course Words
uses the existing published course catalog and paginated course-words API. It
shows counts from loaded API rows, course/search filters, loading/empty/error
states, and saves through the existing personal vocabulary API. Save & practise
opens the same personal practice engine with the saved word first. No independent
learning-state or practice system is introduced; already-saved words are handled
through WORD_EXISTS without replacing the learner's translation.

## Compact assistant and Markdown

The assistant keeps owned history, authorization, context IDs, streaming,
request IDs, minimize/close lifecycle and existing provider limits. History
refresh is in the options disclosure and appears as recovery when required.
The panel has a bottom composer, icon send button, maximum 500-character input
(or the smaller server bound), counter, typing indicator and Latest control.
Manual scrolling disables automatic following until Latest is selected.

Assistant messages use markdown.js; user messages remain literal text. The
renderer supports emphasis, paragraphs/breaks, lists (including nested lists),
inline/fenced code and links. Sanitization is by construction: only fixed DOM
tags and attributes, text nodes for content and explicit URL validation. It never
parses HTML or creates images, script elements, event handlers or custom HTML.
Links allow HTTP/HTTPS/mailto, root-relative paths and fragments, reject control
characters/backslashes/protocol-relative URLs/credentials, and use noopener and
noreferrer. Unsupported Markdown stays text. Streaming uses bounded whole-message
parsing coalesced to animation frames; the final saved reply replaces provisional
content. Parsing is limited to 64,000 characters and bounded inline nesting.

## Verification

- All seven files in npm run frontend:test pass. The new Markdown/Words suite
  has eight checks: Markdown tags, raw HTML/XSS/unsafe URLs, unfinished streaming
  formatting, four active-navigation cases and paginated course/save/practice.
- Eleven widget checks pass, including existing history/account isolation,
  interrupted streams/no automatic paid retry, 500-character cap, Markdown versus
  user text and preserving manual scroll. Both legacy PWA cleanup scripts pass.
- Firefox 159.0.1: actual temporary SQLite catalog reads (500 words, filtered A0
  100 words), search and personal-word save. AI status/SSE were mocked in browser;
  no provider requests were sent.
- Browser widths 1440, 768, 390 and 360: document width stays within viewport,
  chat panel stays within horizontal bounds, long code scrolls internally,
  composer stays visible. A discovered 4px mobile scrollbar sizing error was fixed.
- Simulated visualViewport keyboard contraction and actual 360x360 reduced-height
  viewport keep the composer visible. Physical Android/iOS keyboards were not used.
- Native Words disclosure click and summary focusability verified. Native key
  activation remains unverified because headless Firefox reports no system focus;
  production uses standard summary/Enter/Space behavior, not custom key handling.
- git diff --check passes. Existing documentation contracts/link checks are run
  separately. No claim of exact screenshot fidelity or accessibility certification.

Temporary QA screenshots and measurements are under /tmp/fleng-words-ai-review/;
they contain only a disposable QA account and mocked AI replies. They are not
repository artifacts.
