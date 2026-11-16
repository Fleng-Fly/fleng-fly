# State management

Page variables/DOM hold filters, selected tabs, loading, lesson state and assistant visibility. Persisted identity/progress comes from APIs. No global state framework, router store or offline synchronization exists.

Access tokens live in the api.js closure. localStorage holds logout events and per-user assistant conversation IDs, not passwords/JWTs. IDs are convenience pointers and history endpoints still check ownership. A same-tab shared promise prevents simultaneous refresh rotation there; separate tabs are not globally serialized.

A local animation/answer selection is not persisted completion. Wait for successful server responses before treating XP or completion as authoritative. Preserve context and expose retry where page implementations support it.

[Section index](README.md) · [Documentation home](../README.md)
