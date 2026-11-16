# Fleng website 2026.11.16-web.3

The owner's Untitled (1).zip contains 2x PNG exports from the linked Figma board.
These exports, inspected individually, are the visual reference for this release.
The Figma live canvas could not be inspected in this environment (WebGL unavailable).
No editable-layer or exact-pixel comparison is claimed.

## Design changes

The shared final stylesheet `frontend/css/figma-reference.css` uses the exported
256px sidebar / 76px topbar / 32px content gutter at the original 1280px CSS scale.
It aligns Dashboard, course/lesson views, Settings, login/signup, Leaderboard,
My Words, Course Words, cards, recall questions and result panels. The previous
invented Team copy and orbit-card hero were removed. The seven names and roles
now come from ApplicationLayout.png, in four / three rows with a large background
orb. David uses a neutral avatar instead of the embedded photograph; other
avatars are CSS representations. Illustrative XP, counts, profile details and
completion claims in the exports are replaced with actual server/run data.

The words library retains course and level filtering, selection and saved words;
its session builder is an expandable panel opened by Practice Flashcards.
Multiple choice now selects first, then grades through Check Answer. Failed
personal review saves remain retryable without counting or advancing the answer.
Flashcards offer Flip, previous/next and bounded Auto Play; backgrounding or
leaving stops playback. Letter tiles support click, drag, typing, Backspace and
Clear Placed Letters. Reduced-motion behavior is retained.

Login/signup keep existing authentication. Password visibility is a local display
control. Social sign-in buttons are visibly disabled because no social provider
is implemented. Language selection and account edits keep their existing behavior;
passwords are never displayed as saved data. The lesson still has its three real
tabs, avoiding a duplicate Test action. Custom template creation remains disabled.

## Separate course-progress change

A separate worktree on feat/course-progress-batch implements the owner's scoped
optimization. GET /api/v1/courses/{slug}/progress returns a compact own-user snapshot
with courseId, lessonsTotal, lessonsStarted, lessonsCompleted and lessons
(lessonId, slug, status). Status is not_started, in_progress or completed.
Published-only filters apply; missing/draft courses return the same 404 and
unauthenticated requests return 401. It uses two catalog reads regardless of
lesson count, in addition to existing authentication reads. No writes, migrations,
XP, grading, auth/refresh, AI, Dashboard, Words or CSS changes are part of that
optimization. GET /lessons/{slug}/progress remains unchanged.

Course detail now renders catalog content before requesting the snapshot.
Unavailable progress is shown as unknown with a retry action, and all lesson
links remain available. Expired sessions still redirect through existing behavior.

No commit, push or deployment was performed after the owner's latest instruction.
The package records a prepared tree rather than claiming an existing release commit.
The guarded Windows updater creates a commit/push only when the owner runs it.

## Validation and limits

- 88 targeted backend scenarios passed, including eight new batch scenarios.
- 49 frontend scenarios passed, including explicit choice confirmation and
  one-request course statuses / progress-failure recovery.
- Ruff checks passed; mypy checked all 82 application source files.
- Legacy worker / installation retirement checks passed.
- Desktop browser fixture verified Team, Dashboard, Settings, login, course-word
  selection and cards → choice test → 50% summary → mistakes-only retry.
- 390px iframe checks for Course Words, Team and Settings had no horizontal overflow.
- Browser fixtures are isolated, synthetic and omitted from the package. No real
  browser login, Windows execution, live deployment or PostgreSQL run was tested.

Self-review checked ownership in the join, unchanged grading/auth/AI modules,
read-only SQL count, missing progress as unknown, retry behavior, reduced-motion
support, scoped legacy-worker cleanup and archive exclusion of private files.
