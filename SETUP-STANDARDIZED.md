# EasyLearn final local setup

## 1. Keep the Firebase Admin key outside this project

Use one JSON key for the same Firebase project (`easylearn-fyp-2026`). A safe
example location is:

```text
C:\Users\User\Documents\EasyLearn_Secrets\easylearn-firebase-admin.json
```

Copy each `.env.example` to `.env`, then replace the example path. Both accepted
variable names point to the same file. Do not copy the JSON into the ZIP or Git.

## 2. Configure environments

Create these files from their examples:

- `shared/auth/.env`
- `subjects/history/backend/.env`
- `subjects/mathematics/backend/.env`
- `subjects/bahasa_melayu/backend/.env`
- each frontend's `.env.local` from `.env.example`

Bahasa Melayu no longer needs `MONGO_URI`. Mathematics still needs the local
MySQL credentials because its question/content catalogue remains in `mathsy_db`.

## 3. Install excluded dependencies

The delivered ZIP intentionally excludes `.venv` and `node_modules`. In a
PowerShell opened in the project root, run:

```powershell
py -3.12 -m venv .\shared\auth\.venv
& .\shared\auth\.venv\Scripts\python.exe -m pip install -r .\shared\auth\requirements.txt

py -3.12 -m venv .\subjects\history\backend\.venv
& .\subjects\history\backend\.venv\Scripts\python.exe -m pip install -r .\subjects\history\backend\requirements.txt

py -3.12 -m venv .\subjects\mathematics\backend\.venv
& .\subjects\mathematics\backend\.venv\Scripts\python.exe -m pip install -r .\subjects\mathematics\backend\requirements.txt

py -3.12 -m venv .\subjects\bahasa_melayu\backend\.venv
& .\subjects\bahasa_melayu\backend\.venv\Scripts\python.exe -m pip install -r .\subjects\bahasa_melayu\backend\requirements.txt

Push-Location .\subjects\history\frontend; npm install; Pop-Location
Push-Location .\subjects\mathematics\frontend; npm install; Pop-Location
Push-Location .\subjects\bahasa_melayu\frontend; npm install; Pop-Location
```

If you copied working `.venv` and `node_modules` folders from the same computer,
you may use those instead. Reinstall them after moving to another computer.

## 4. Deploy the Firestore server-only rules

Install the Firebase CLI, sign in, and deploy from the project root:

```powershell
npm install -g firebase-tools
firebase login
firebase deploy --only firestore:rules,firestore:indexes --project easylearn-fyp-2026
```

These rules intentionally block direct browser access. All writes pass through
the authenticated EasyLearn backend using Firebase Admin.

## 5. Start and verify

Keep MySQL running, then double-click `Start-EasyLearn.cmd`. Visit
`http://localhost:4000`, sign in, and follow `TEST-CHECKLIST.md`.

The first login upgrades an existing account to its role ID automatically:

| Role | ID format |
|---|---|
| Student | `S-1234567` |
| Teacher | `T-1234567` |
| Parent | `P-1234567` |

## 6. Old data cleanup (optional, after testing)

- MongoDB: BM is no longer read by this build, so its old BM database can be
  deleted in Atlas after confirming new BM results appear in Firestore.
- MySQL: do not delete `mathsy_db`; it still supplies Mathematics content.
- Firestore: old test collections may be removed manually, but keep
  `easylearn_users`, `student_relationships`, `learning_events`,
  `user_interactions`, and every `bm_*` collection.

No automatic destructive cleanup is included.
