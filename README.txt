EasyLearn — Common Vercel google-crc32c Fix

Copy the `shared` and `subjects` folders into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN

Choose "Replace files in destination".

WHY
Fresh Vercel Python deployments are currently resolving google-crc32c==1.9.0,
but that build is failing on Vercel Linux x86_64. This patch explicitly pins
google-crc32c==1.8.0, which has a CPython 3.12 manylinux x86_64 wheel.

IMPORTANT
You do NOT need to redeploy every backend just because these files changed.

Redeploy only the services that need current code changes:
1. easylearn-bm-api
2. easylearn-platform-api
3. easylearn-math-api only if the Math snapshot backend patch has not yet
   successfully deployed.

History does not need redeployment now. Its requirements file is included only
so a future History redeploy will not hit the same crc32c problem.

The final frontend is deployed separately after backend fixes are stable.
