# EasyLearn project status

This build has one Portal login, role dashboards, stable shared IDs, and one
canonical Firestore activity stream across History, Mathematics, and Bahasa
Melayu. Subject UIs use the same EasyLearn identity and Portal-only logout.

| Service | Data responsibility |
|---|---|
| Firestore | Identity, roles, relationships, BM results, unified analytics |
| Mathematics MySQL | Existing question/content catalogue and legacy internals |
| Subject files/models | Existing reviewed content and local AI assets |

The source compiles, but clean-computer acceptance testing and production cloud
deployment remain release tasks. Follow `TEST-CHECKLIST.md` before deleting any
legacy data or deploying publicly.
