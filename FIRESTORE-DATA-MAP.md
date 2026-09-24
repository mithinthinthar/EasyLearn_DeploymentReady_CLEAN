# Firestore data map

| Collection | Purpose |
|---|---|
| `easylearn_users` | Shared profile, role, and `S-/P-/T-` account ID |
| `student_relationships` | Parent/teacher links to students |
| `learning_events` | Canonical normalized activity across all subjects |
| `user_interactions` | History detailed-dashboard compatibility data |
| `bm_*_sessions` | BM in-progress assessment sessions |
| `bm_*_results` | BM saved assessment results |
| `bm_user_results` | BM per-user result memory |

The Portal aggregates only `learning_events`, which prevents subject-specific
schemas from leaking into cross-subject dashboards. Backend services use the
Firebase Admin SDK; browsers have no direct Firestore read/write permission.
