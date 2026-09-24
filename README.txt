EasyLearn Mathematics Connecting Screen Fix

Copy the 'subjects' folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN

Choose Replace files in destination.

What this fixes:
- Math portal-login already returns HTTP 200.
- The old App.js changed only the URL hash, returned early, and never set
  authenticationChecked=true.
- This patch updates the hash without relying on a page reload and then
  immediately unlocks the Mathematics UI.

Only the FINAL FRONTEND needs redeployment.
The Math API/backend does NOT need redeployment for this fix.
