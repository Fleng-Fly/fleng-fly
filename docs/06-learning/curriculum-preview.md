# Curriculum preview

Local reviewer mode is not publishing/admin access. It needs POSIX UID/private modes/fcntl locking. From root:

```sh
backend/.venv/bin/python scripts/preview_curriculum.py prepare --directory /tmp/fleng-doc-review --port 3011
backend/.venv/bin/python scripts/preview_curriculum.py start --directory /tmp/fleng-doc-review --port 3011
```

Choose a new dedicated directory; prepare refuses existing paths. Open http://127.0.0.1:3011/login.html and use credentials printed privately by the tool. Never copy generated passwords/marker into docs/reports/Git. Navigate to courses.html.

Preparation creates private 0700 directory/0600 DB+marker, migrates/seeds/imports unpublished drafts and creates one reviewer, without copying learner data. Startup validates owned marker, snapshot SHA, isolated database/JWT/cookie, development mode and disabled AI/SMTP. Loopback host/client guards, reviewer UUID authorization and a file lock restrict use. Do not tunnel/reverse-proxy/deploy it.

Stop with Ctrl+C before cleanup. Inspect the exact disposable directory, ensure its server stopped, then remove only that directory with your normal filesystem tool. No cleanup CLI action exists. Never delete backend/data. /tmp is not durable. [Visual review](../curriculum-visual-review.md) retains historical browser evidence without reproducing private credentials here.

[Section index](README.md) · [Documentation home](../README.md)
