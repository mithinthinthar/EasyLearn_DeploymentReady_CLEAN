# EasyLearn — Final Tester Acceptance Checklist

Record PASS/FAIL beside each item before sharing the production URL.

## A. Infrastructure

- [ ] Vercel root URL returns EasyLearn portal over HTTPS.
- [ ] `/platform-api/health` returns HTTP 200.
- [ ] `/history-api/health` returns HTTP 200.
- [ ] `/math-api/health` returns HTTP 200.
- [ ] `/math-api/api/syllabus` returns real Aiven chapter data.
- [ ] `/bm-api/` returns HTTP 200.
- [ ] Production Vercel domain is listed in Firebase Authentication Authorized Domains.
- [ ] No `.env`, Firebase Admin JSON, `ca.pem`, or private API keys are present in the GitHub repository.

## B. One-login behavior

- [ ] Fresh incognito visitor is sent to portal login.
- [ ] Google/email login succeeds.
- [ ] Portal dashboard shows correct name and role.
- [ ] History opens without another login.
- [ ] Mathematics opens without another login.
- [ ] Bahasa Melayu opens without another login.
- [ ] Logout clears the shared session.

## C. Mathematics

- [ ] Syllabus loads.
- [ ] Kertas 1 question loads.
- [ ] Kertas 2 question loads.
- [ ] One attempt can be submitted.
- [ ] Progress/dashboard reads saved data.
- [ ] Quick Snap works on a test image.
- [ ] AI explanation/chatbot responds.
- [ ] Pinecone-backed retrieval works (if part of demo).

## D. History

- [ ] Dashboard loads.
- [ ] Chapter questions load.
- [ ] Quick quiz works.
- [ ] Arcade/bucket game works.
- [ ] Essay/structured practice loads.
- [ ] Semantic scoring works.
- [ ] History AI tutor responds.
- [ ] `/history-api/health` reports Firebase, Gemini and semantic model enabled.

## E. Bahasa Melayu

- [ ] Dashboard loads.
- [ ] Essay feature works.
- [ ] Comprehension feature works.
- [ ] Speaking flow can accept audio and return a result.
- [ ] Listening session generates/loads audio.
- [ ] Listening MP3 still works after opening another page/reloading.
- [ ] Latihan feature works.
- [ ] BM AI assistant responds.

## F. Shared dashboard / roles

- [ ] Student activity is visible in the shared dashboard.
- [ ] New activity from more than one subject appears.
- [ ] Student code is visible for a student account.
- [ ] Parent/teacher read-only behavior is correct if those accounts are part of the evaluation.

## G. Browser/reliability pass

- [ ] Chrome normal window.
- [ ] Chrome incognito window.
- [ ] One mobile-width browser test.
- [ ] Refresh Mathematics on a hash route does not 404.
- [ ] Refresh BM on a hash route does not 404.
- [ ] Browser console has no repeating CORS/auth errors.
- [ ] No UI points to `localhost` when running on Vercel.

## H. Tester handoff

- [ ] Final tester receives only the Vercel portal URL.
- [ ] Final tester receives a dedicated test account, not an admin's personal account.
- [ ] Test account login has been verified immediately before handoff.
- [ ] Demo data is safe to modify/reset.
- [ ] A fallback screenshot/video exists in case an external AI/cloud provider is temporarily unavailable during presentation.

## Evaluation-day warm-up

Because Cloud Run is configured with minimum instances = 0, warm the application shortly before the tester arrives:

- [ ] Open the portal and all three subject pages once.
- [ ] Open one History feature that uses semantic retrieval.
- [ ] Load the Mathematics syllabus/practice once.
- [ ] Run one BM essay scoring request so XLM-RoBERTa is loaded.
- [ ] Run one short BM Speaking request so the Whisper models are downloaded/loaded.
- [ ] Confirm BM Listening generates and plays one audio file.
- [ ] Re-run the health/API checks after warm-up.

The BM Speaking model is lazy-loaded, so the first speaking request can be much slower than later requests on the same warm instance.
