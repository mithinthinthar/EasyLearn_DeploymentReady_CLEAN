EasyLearn Final Integration Fix

Copy the contents of this folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN

Choose "Replace files in destination".

Fixes:
1) Mathematics registers math_portal_app so /api/auth/portal-login exists.
2) BM essay grading removes XLM-RoBERTa runtime/model loading. The old CLS
   embedding was calculated but never used by any scoring formula.
3) BM listening creation no longer waits for Edge TTS on Vercel; audio is
   generated lazily at /api/listening/audio/{session_id}.
4) BM listening marking falls back to the stored answer scheme if Gemini
   marking temporarily fails.

After copying:
- Redeploy Math from subjects\mathematics\backend
- Redeploy BM from subjects\bahasa_melayu\backend
- No final frontend rebuild is required for these backend-only changes.
