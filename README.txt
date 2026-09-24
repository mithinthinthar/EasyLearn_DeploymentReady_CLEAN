EasyLearn BM Vercel no-storage patch

Copy the contents of this folder over the matching files in EasyLearn_DeploymentReady_CLEAN.

Changes:
- Listening scripts/questions/results remain in Firestore.
- Listening MP3s use /tmp and are regenerated on demand through /api/listening/audio/{session_id}.
- No FIREBASE_STORAGE_BUCKET is required.
- Speaking uploads use Vercel /tmp instead of the read-only deployment filesystem.
- CPU-only PyTorch is used to reduce bundle size.
