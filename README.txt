EasyLearn Runtime Fix v2

This patch addresses the remaining deployed-runtime issues:

MATHEMATICS
- Quick Snap images are resized/compressed before Base64 upload to stay below
  Vercel's 4.5 MB Function body limit.
- Heavy PDF parser imports are moved out of Flask startup and loaded only by
  admin PDF-import routes, reducing cold-start time.
- Dashboard intelligence import is deferred until a dashboard route is used.

BM
- Chatbot defaults to gemini-3.5-flash-lite with gemini-3.8-flash fallback.
- Listening MP3 can be uploaded to a public Vercel Blob store and played from
  the Blob CDN instead of being returned from the Python Function.
- Speaking recordings use 24 kbps Opus and a 180-second per-clip cap; the UI
  also blocks submissions above ~4 MB total to avoid Vercel's 4.5 MB request limit.

COPY
Copy the contents of this folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN
and replace files.

AFTER COPYING
1. Create/connect a PUBLIC Vercel Blob store to easylearn-bm-api.
2. Redeploy Math backend.
3. Redeploy BM backend.
4. Redeploy the final frontend because Quick Snap and Speaking frontend files changed.
