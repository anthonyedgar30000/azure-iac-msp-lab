# Connector tooling incident — accidental placeholder write to main

At `2026-07-27T14:00Z`, a placeholder file named `tmp` was accidentally created directly on `main` while preparing the bounded collector verify-only branch. It was removed immediately in the next commit.

```text
placeholder add commit: 3a528048e87eac01b112daa671facb2ef57a310f
placeholder removal commit: b31f5288744669f2587d136e3ba8024b5d6c5316
Azure action performed: false
workflow dispatch performed by incident: false
repository content after removal: no placeholder file
```

The incident does not authorize or imply any Azure mutation. It is preserved so repository history remains explainable.
