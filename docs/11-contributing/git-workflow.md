# Git workflow

Established convention: small logical `type: summary` commits (docs/fix/feat/test/chore/refactor). Suggested branches: docs/topic, fix/topic, feat/topic; no enforced naming policy is claimed.

Preserve existing modifications. Do not reset/clean, amend/rewrite history or alter author configuration. Push only on explicit request. This task forbids automatic commits/pushes and leaves reviewable changes in the working tree.

Before a later authorized commit:

```sh
git status --short
git diff --stat
git diff --check
```

Stage only intended files and exclude secrets/databases/generated credentials. Existing curriculum artifacts are not implicitly part of a documentation commit.

[Section index](README.md) · [Documentation home](../README.md)
