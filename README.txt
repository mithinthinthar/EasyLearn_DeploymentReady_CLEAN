EasyLearn BM Listening Playback Fix

What this fixes
1. Gemini 3.8 TTS now uses the official unary response_format={"type":"audio"}.
   Gemini 3.8 unary TTS returns a complete WAV file.
2. The backend attempts to create/upload the WAV before returning the listening
   session, so the frontend receives a direct Blob URL whenever possible.
3. The Quiz player no longer rewinds itself through onTimeUpdate.
   The custom one-play button already prevents ordinary seeking.
4. The Quiz waits until the browser reports canplay before enabling Play and
   displays an actual audio-load/playback error.
5. Listening Practice no longer hardcodes type="audio/mpeg" for a WAV file.

Deployments required
- BM backend
- Final frontend

No Math API or Platform API change is required for this listening fix.
