EasyLearn Platform CRC32 Vercel Fix

Copy the `shared` folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN

Choose "Replace files in destination".

Then, from shared\auth, remove any stale uv lock files before redeploying:

Remove-Item .\uv.lock -ErrorAction SilentlyContinue
Remove-Item .\pyproject.toml -ErrorAction SilentlyContinue

IMPORTANT:
Only run the second command if pyproject.toml was not intentionally created by you
for this Platform API. The original EasyLearn shared/auth service uses requirements.txt.

Then deploy:
vercel --prod --force
