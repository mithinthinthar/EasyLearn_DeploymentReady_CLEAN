# START HERE — EasyLearn Production Deployment

This is the sanitized deployment copy. It intentionally does **not** contain your real `.env` files, Firebase Admin JSON, Aiven CA certificate, database password, or API secrets.

## Final design

- **One Vercel website**: Portal + History + Mathematics + Bahasa Melayu.
- **Four Cloud Run APIs**: shared platform/auth, History, Mathematics, BM.
- **Firebase**: Authentication + Firestore + Storage.
- **Aiven**: Mathematics MySQL (`mathsy_db`).

## Do these in order

1. Put this sanitized folder in a **private GitHub repository**.
2. Read `deploy/DEPLOYMENT-GUIDE.md` and deploy the four Cloud Run services.
3. Test each Cloud Run service before touching Vercel.
4. Put the four Cloud Run URLs into Vercel Environment Variables.
5. Deploy **one** Vercel project from the repository root.
6. Add the final Vercel hostname to Firebase Authentication -> Authorized domains.
7. Run every item in `deploy/FINAL-TEST-CHECKLIST.md` from an incognito browser.

## Before sharing with a tester

The final tester should receive only:

- the one Vercel portal URL;
- a tester account/credentials created for the evaluation;
- any short testing instructions required by your evaluation.

Do not give a tester your Aiven credentials, Firebase Admin service account, API keys, Cloud Run environment variables, or private GitHub access.

## Validation status of this package

See `deploy/PROJECT-AUDIT.md`. Backend Python and deployment JavaScript syntax checks passed. A fresh frontend dependency build could not be completed in the ChatGPT sandbox because npm registry DNS access failed; the Vercel build is the first full production frontend build gate.
