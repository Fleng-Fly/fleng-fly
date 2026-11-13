# Conversations

AIConversation belongs to user; AIMessage belongs to conversation with role/content/model/usage/time. Listing/history/deletion checks ownership regardless of known UUID. Conversation lists are newest first; messages chronological, both bounded limit/offset.

save_turn persists completed turns. Displayed deltas before done are provisional: cancellation/failure can leave no saved reply. Reload history after uncertain outcomes before retrying. requestId deduplication uses AIUsage's user/request unique index and can return AI_REQUEST_DUPLICATE.

The frontend stores only a per-user conversation pointer and clears visible state/aborts on logout. Server ownership is still authoritative. Deletion explicitly removes messages; a comprehensive account retention/export/deletion feature is not implemented.

[Section index](README.md) · [Documentation home](../README.md)
