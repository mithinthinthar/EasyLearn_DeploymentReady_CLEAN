EasyLearn BM Vercel Librosa Fix

Copy the contents of this folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN

Choose "Replace files in the destination".

Changes:
- Removes librosa from BM runtime dependencies.
- Uses faster_whisper.decode_audio (PyAV) for audio decode/resampling.
- Uses NumPy for frame-wise RMS energy.
- Preserves BM speaking scoring and common browser audio formats.
