EasyLearn BM Cloud Audio Fix

WHY
The Vercel log proves Speaking fails while downloading
SeamlessX/malaysian-faster-whisper-small-v3-ct2:
"No space left on device (os error 28)".

This patch removes the local production audio-model architecture.

NEW PRODUCTION FLOW

Listening:
Gemini creates listening text/questions
 -> Firestore
 -> Gemini 3.8 Flash-Lite TTS generates WAV
 -> Vercel Blob stores/serves the WAV
 -> browser plays the Blob URL

Speaking:
Browser records 5 clips
 -> BM FastAPI
 -> each REAL audio clip is sent to Gemini 3.5 Flash-Lite
 -> Gemini transcribes and assesses grammar, pronunciation, fluency, and ideas
 -> existing SpeakingSubmitResponse shape is preserved
 -> Firestore saves the result

REMOVED FROM BM PRODUCTION DEPENDENCIES
- PyTorch
- faster-whisper
- Silero VAD
- Hugging Face Hub
- Edge TTS
- soundfile
- jiwer

COPY
Copy the contents of this folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN

Choose "Replace files in destination".

DEPLOY
Only BM backend must be redeployed for this patch:

cd C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN\subjects\bahasa_melayu\backend
vercel --prod --force

No frontend redeploy is required for this BM patch.

ENVIRONMENT
Existing GEMINI_API_KEY is reused.
Optional (defaults already work):
GEMINI_SPEAKING_MODEL=gemini-3.5-flash-lite
GEMINI_TTS_MODEL=gemini-3.8-flash-lite-tts
GEMINI_TTS_VOICE=Kore

Make sure the public Vercel Blob store remains connected to easylearn-bm-api.
