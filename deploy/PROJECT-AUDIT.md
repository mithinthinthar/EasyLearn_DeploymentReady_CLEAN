# EasyLearn — Deployment Readiness Audit

Date: 24 September 2026

## Project structure found

EasyLearn is a multi-application repository rather than a single frontend/backend pair:

- `portal/` — shared EasyLearn entry/login/dashboard.
- `shared/auth/` — FastAPI shared identity, role, relationship and cross-subject activity API.
- `subjects/history/frontend/` — History React frontend.
- `subjects/history/backend/` — History Flask backend with semantic/CSKT model features.
- `subjects/mathematics/frontend/` — Mathematics React frontend.
- `subjects/mathematics/backend/` — Mathematics Flask backend and Aiven MySQL access.
- `subjects/bahasa_melayu/frontend/` — Bahasa Melayu Vite/React frontend.
- `subjects/bahasa_melayu/backend/` — Bahasa Melayu FastAPI backend.

## Final deployment design

One Vercel origin serves the portal and all three subject frontends. Vercel reverse-proxy paths forward API requests to four independently deployed Cloud Run services. This deliberately preserves the existing shared HttpOnly session cookie as a first-party cookie.

Production paths:

- `/` -> shared portal
- `/history/` -> History frontend
- `/mathematics/` -> Mathematics frontend
- `/bahasa-melayu/` -> BM frontend
- `/platform-api/*` -> shared auth Cloud Run service
- `/history-api/*` -> History Cloud Run service
- `/math-api/*` -> Mathematics Cloud Run service
- `/bm-api/*` -> BM Cloud Run service

## Important issues found and addressed

### Shared login / routing

The local project used different localhost ports. Deploying each frontend on an unrelated domain would make the shared cookie design fragile. Production routing was changed to use one origin and subpaths while retaining localhost fallbacks for development.

### Mathematics database configuration

Several Mathematics modules previously had their own local MySQL assumptions. Runtime database access has been centralized through the Aiven-aware `config.py`. The production configuration accepts the Aiven CA certificate through `DB_SSL_CA_BASE64`, `DB_SSL_CA_PEM`, or a local file path.

### Firebase Admin credentials

Backends previously depended heavily on local credential-file paths. A shared pattern now accepts Firebase Admin credentials as JSON, base64, file path, or Google Application Default Credentials.

### Cloud filesystem persistence

BM listening MP3s were generated into a local upload folder. Container local files are not a durable production store. BM can now persist generated listening audio in the configured Firebase/Google Cloud Storage bucket and return an absolute signed URL to the frontend.

### Heavy backend dependencies

History and BM load ML libraries/models, so the deployment design does not assume a small 512-MiB free web container. Docker/Cloud Run definitions were added with separate resource profiles per service.

### Mathematics build size

Training-only synthetic Mathematics data (~20 MB) is excluded from the runtime Docker context. Runtime models remain included.

### Frontend production paths

History, Mathematics and BM now build for subpaths under the single Vercel origin. Mathematics and BM use hash-based client routing where appropriate to avoid requiring independent SPA rewrite servers.

## Validation completed in the sandbox

Passed:

- Python byte-code compilation for all four backend code trees.
- Node syntax check for portal JavaScript.
- Node syntax check for the root multi-frontend build script.
- Node syntax check for `vercel.mjs`.
- Mathematics source scan confirmed the runtime uses the centralized MySQL connector.
- Deployment secret templates contain placeholders rather than production secret values.

Not completed in the sandbox:

- A fresh full `npm ci` / React production build. The execution environment could not resolve `registry.npmjs.org` and returned `EAI_AGAIN`. Vercel's build is therefore the first authoritative full frontend dependency/build test.
- Live Cloud Run/Vercel/Firebase dashboard deployment, because those account sessions are not connected to this chat.
- Final browser end-to-end testing, which requires the resulting live Vercel URL.

## Release gate

The code is prepared for the cloud deployment sequence in `DEPLOYMENT-GUIDE.md`. Do not call the project production-tested until:

1. all four Cloud Run health/API checks pass;
2. the one Vercel build succeeds;
3. the Vercel hostname is added to Firebase Authentication Authorized Domains; and
4. every item in `FINAL-TEST-CHECKLIST.md` passes from an incognito browser.
