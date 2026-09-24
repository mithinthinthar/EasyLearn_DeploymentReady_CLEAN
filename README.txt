EasyLearn FINAL PENDING FIXES
Prepared after the Vercel 100-deploy/day limit was reached.

WHY HISTORY IS CURRENTLY BROKEN
The deployed History app.py is the old local version. It contains:
  credentials.Certificate("sejarah-app-...json")
That file does not exist on Vercel, so the entire Flask app fails to import.

This bundle restores the Vercel-safe History entrypoint:
  app.py -> imports app from history_app_local.py
and keeps Firebase environment/base64 credential loading.

HISTORY ALSO
- uses recorded time_taken_ms for study time
- old untimed records count as 0 min
- frontend uses real total/weekly/heatmap minutes
- removes the fake fixed 7 PM personalized study time

BM
- total study time uses recorded session elapsed time
- weekly minutes are rounded/formatted (no 14.900000000000006m)
- removes fake fixed 7 PM personalized study time
- keeps Listening questions/results
- Listening TTS uses Gemini 3.8 generate_content AUDIO
- Listening player waits until the WAV is actually playable

IMPORTANT
CLI `vercel --prod` deploys LOCAL FILES. A Git commit is not required for that.
Commit/push only after the final working version is confirmed so future Git
deployments use the same code.

WHEN THE VERCEL LIMIT RESETS
Deploy in this order, once each:
1. History backend
2. BM backend
3. Platform backend only if the Math snapshot/platform patch is still pending
4. Math backend only if its snapshot patch is still pending
5. Final root portal ONCE

Do not repeatedly redeploy while debugging. Run the local build first.
