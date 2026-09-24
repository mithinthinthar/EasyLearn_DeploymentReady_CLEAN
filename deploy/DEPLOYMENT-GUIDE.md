# EasyLearn — Final Deployment Guide

This guide matches the current project in this folder. Do **not** deploy the old local-only structure as four unrelated websites.

## Final production architecture

```text
Final tester
   |
   v
ONE Vercel URL
   |-- /                  EasyLearn shared portal
   |-- /history/          History frontend
   |-- /mathematics/      Mathematics frontend
   |-- /bahasa-melayu/    BM frontend
   |
   |-- /platform-api/* --> Cloud Run: easylearn-platform
   |-- /history-api/*  --> Cloud Run: easylearn-history
   |-- /math-api/*     --> Cloud Run: easylearn-math --> Aiven MySQL
   `-- /bm-api/*       --> Cloud Run: easylearn-bm --> Firestore/Storage

Firebase Authentication + Firestore are shared by the portal and subjects.
```

The single Vercel origin is important because EasyLearn uses an HttpOnly `easylearn_session` cookie. The API proxy paths keep that cookie first-party even though the Python APIs run on Cloud Run.

---

## Phase 0 — What is already prepared in this copy

- Portal production routing + localhost fallback.
- History/Math/BM frontends can live under one domain.
- Mathematics and BM use hash routing so refreshing a nested page does not require four separate SPA servers.
- Vercel reverse-proxy configuration for all four APIs.
- Cloud-safe Firebase Admin loading (base64, JSON, path, or ADC).
- Cloud-safe Aiven CA loading (`DB_SSL_CA_BASE64`).
- Every Mathematics runtime DB connection now uses the same Aiven-aware `config.py`.
- Cloud Run Dockerfiles for all four Python services.
- Reduced production dependency lists for the large backends.
- BM generated listening MP3s can persist in Firebase/Google Cloud Storage instead of disappearing with a Cloud Run container.
- `.env.example` templates contain names only; real secrets must stay out of GitHub.

---

# Phase 1 — Protect credentials before GitHub

Use the **sanitized deployment ZIP** supplied with this guide rather than pushing the original project ZIP.

Never commit:

- `.env` or `.env.local`
- Firebase Admin service-account JSON
- Aiven password
- `ca.pem`
- Gemini/Pinecone/Cloudinary keys

The included `.gitignore`, `.dockerignore`, and `.vercelignore` files protect these paths, but still inspect `git status` before every push.

Recommended: create a **private GitHub repository** for EasyLearn and push the sanitized folder.

---

# Phase 2 — Prepare the two long cloud values

On your Windows computer run, from the project root:

```powershell
.\deploy\Prepare-Cloud-Secrets.ps1 `
  -FirebaseServiceAccountJson "C:\path\to\your-firebase-admin.json" `
  -AivenCaPem "C:\Users\User\Downloads\ca.pem"
```

It prints:

- `FIREBASE_SERVICE_ACCOUNT_BASE64`
- `DB_SSL_CA_BASE64`

Copy them temporarily somewhere private. Do not send them in chat and do not put them in GitHub.

---

# Phase 3 — Prepare Google Cloud Run

Use the same Google/Firebase project if possible: `easylearn-fyp-2026`.

1. Open Google Cloud Console.
2. Select project `easylearn-fyp-2026`.
3. Enable billing for the project.
4. Enable Cloud Run, Cloud Build, Artifact Registry and Cloud Logging APIs.
5. Use region **Kuala Lumpur — `asia-southeast4`** for all four services.
6. Use request-based billing.
7. Set **Minimum instances = 0**.
8. Set **Maximum instances = 1** while this is a school/evaluation deployment.
9. Allow unauthenticated HTTP access. Application-level Firebase auth still protects user data/routes.

## Service 1 — `easylearn-platform`

Source directory:

```text
shared/auth
```

Dockerfile is already included.

Suggested resources:

```text
CPU: 1
Memory: 512 MiB
Concurrency: 20
Timeout: 300 seconds
Min instances: 0
Max instances: 1
```

Environment variables:

```text
FIREBASE_SERVICE_ACCOUNT_BASE64=<your base64 value>
AUTH_COOKIE_SECURE=true
ALLOW_TEACHER_SELF_REGISTRATION=true
```

`AUTH_ALLOWED_ORIGINS` may be left blank while the browser uses Vercel's same-origin proxy. You may add the final Vercel origin later.

After deployment copy the Cloud Run URL. Call it:

```text
PLATFORM_BACKEND_URL
```

Test directly:

```text
https://YOUR-PLATFORM-RUN-URL/health
```

Expected: JSON with `status: ok`, `service: easylearn-platform`, `database: firestore`.

## Service 2 — `easylearn-history`

Source directory:

```text
subjects/history/backend
```

Suggested resources:

```text
CPU: 1
Memory: 2 GiB
Concurrency: 2
Timeout: 300 seconds
Min instances: 0
Max instances: 1
```

Environment variables:

```text
FIREBASE_SERVICE_ACCOUNT_BASE64=<same Firebase base64>
GEMINI_API_KEY=<your Gemini key>
GEMINI_MODEL=gemini-3.5-flash-lite
```

The Docker build caches `all-MiniLM-L6-v2`, and the repository contains the CSKT model file.

Copy the resulting URL as:

```text
HISTORY_BACKEND_URL
```

Test:

```text
https://YOUR-HISTORY-RUN-URL/health
```

Important fields should show `status: ok`. For the complete production feature set, `firebase_enabled`, `gemini_enabled`, and `semantic_model_enabled` should be true.

## Service 3 — `easylearn-math`

Source directory:

```text
subjects/mathematics/backend
```

Suggested resources:

```text
CPU: 1
Memory: 2 GiB
Concurrency: 4
Timeout: 300 seconds
Min instances: 0
Max instances: 1
```

Required environment variables:

```text
FIREBASE_SERVICE_ACCOUNT_BASE64=<same Firebase base64>

DB_HOST=mysql-8de9fa3-easy-learn.j.aivencloud.com
DB_PORT=14197
DB_USER=avnadmin
DB_PASSWORD=<Aiven password>
DB_NAME=mathsy_db
DB_SSL_CA_BASE64=<base64 of ca.pem>

GEMINI_API_KEY=<your Gemini key>
PINECONE_API_KEY=<your Pinecone key>
PINECONE_INDEX_NAME=mathsy-rag
PINECONE_CONCEPT_NAMESPACE=concept_notes
PINECONE_QUESTION_NAMESPACE=question_bank

CLOUDINARY_CLOUD_NAME=<your value>
CLOUDINARY_API_KEY=<your value>
CLOUDINARY_API_SECRET=<your value>
CLOUDINARY_CLOUD_API_KEY=<same API key if existing parser uses this alias>
CLOUDINARY_CLOUD_API_SECRET=<same API secret if existing parser uses this alias>
```

Copy the URL as:

```text
MATH_BACKEND_URL
```

Test in this order:

```text
https://YOUR-MATH-RUN-URL/health
https://YOUR-MATH-RUN-URL/api/syllabus
```

`/api/syllabus` is the important test: it proves the deployed Python service can actually read the Aiven `mathsy_db`, not merely start.

## Service 4 — `easylearn-bm`

Source directory:

```text
subjects/bahasa_melayu/backend
```

Suggested resources:

```text
CPU: 2
Memory: 4 GiB
Concurrency: 1
Timeout: 300 seconds
Min instances: 0
Max instances: 1
```

Environment variables:

```text
FIREBASE_SERVICE_ACCOUNT_BASE64=<same Firebase base64>
FIREBASE_STORAGE_BUCKET=easylearn-fyp-2026.firebasestorage.app
GEMINI_API_KEY=<your Gemini key>
```

Optional legacy route variable if you still use BM's direct Google-login endpoint:

```text
GOOGLE_CLIENT_ID=<your Google OAuth client ID>
```

Copy the URL as:

```text
BM_BACKEND_URL
```

Test:

```text
https://YOUR-BM-RUN-URL/
```

Expected: `status: ok` and `BM SPM API is running`.

For listening exercises, the new production path uploads generated MP3 files to the configured Firebase Storage bucket and returns a temporary signed URL. If the Cloud Run log says it cannot persist listening audio, check the service account's permission to write objects into that bucket.

---

# Phase 4 — Deploy Firestore rules/indexes

From the project root, while logged into Firebase CLI:

```powershell
firebase use easylearn-fyp-2026
firebase deploy --only firestore:rules,firestore:indexes
```

Do this before the final tester starts creating activity data.

---

# Phase 5 — Deploy the ONE frontend on Vercel

Do not make four Vercel projects.

Create/import **one** Vercel project using this repository root.

The root `package.json` runs:

```text
npm run build
```

The build script creates:

```text
dist/
  index.html
  login.html
  history/
  mathematics/
  bahasa-melayu/
```

`vercel.mjs` then proxies API paths to Cloud Run.

Before deploying, add these Vercel environment variables using the four real Cloud Run URLs:

```text
PLATFORM_BACKEND_URL=https://...
HISTORY_BACKEND_URL=https://...
MATH_BACKEND_URL=https://...
BM_BACKEND_URL=https://...
```

No database password, Gemini key, Firebase Admin key, or Aiven CA belongs in Vercel's frontend variables.

Deploy. The result should be one URL such as:

```text
https://easylearn-xxxx.vercel.app
```

This is the URL you give to the final tester/KPM.

---

# Phase 6 — Authorize the production domain in Firebase Authentication

Firebase Console:

```text
Authentication
  -> Settings
  -> Authorized domains
  -> Add domain
```

Add only the hostname, for example:

```text
easylearn-xxxx.vercel.app
```

Do not include `https://` or a path.

---

# Phase 7 — Production smoke tests

Run these from a browser using the **Vercel URL**, not the Cloud Run URLs:

```text
/                            Portal
/platform-api/health         Shared auth/Firestore API
/history/                    History frontend
/history-api/health          History API
/mathematics/                Mathematics frontend
/math-api/health             Mathematics API
/math-api/api/syllabus       Mathematics -> Aiven database
/bahasa-melayu/              BM frontend
/bm-api/                     BM API
```

Then test the real user workflow:

1. Open the Vercel root URL in a private/incognito window.
2. Log in once through the EasyLearn portal.
3. Confirm the portal dashboard loads.
4. Open History. It must use the same account without a second login.
5. Return to the portal and open Mathematics. It must use the same account.
6. Open Mathematics syllabus/practice and verify questions load from Aiven.
7. Complete one Mathematics attempt and verify it appears in the dashboard/database.
8. Open BM. It must use the same portal session.
9. Complete one BM activity.
10. Test BM Listening and confirm the MP3 plays.
11. Return to the shared dashboard and confirm cross-subject activity appears.
12. Log out once from any subject/portal and verify the shared session is cleared.

Use `deploy/FINAL-TEST-CHECKLIST.md` for the final acceptance pass.

---

# Cost-safety settings for this evaluation build

Keep these until you intentionally scale the product:

```text
Cloud Run billing: request-based
Minimum instances: 0
Maximum instances: 1 per service
```

This allows scale-to-zero. The first request after idle may therefore take longer; for an evaluation session, open each subject once shortly before the tester begins so the ML-heavy services are warm.

---

# What not to do

- Do not deploy the four frontends on four unrelated domains.
- Do not put `DB_PASSWORD` or `FIREBASE_SERVICE_ACCOUNT_BASE64` in React/Vite variables.
- Do not set `DB_SSL_CA` to your Windows `C:\...` path in Cloud Run.
- Do not use the old local MySQL fallback in production.
- Do not rely on Cloud Run's local filesystem for persistent user data.
- Do not give the final tester the Cloud Run backend URLs. Give them the one Vercel portal URL and test credentials.
