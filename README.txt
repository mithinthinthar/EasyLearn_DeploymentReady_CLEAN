EasyLearn Math Portal Snapshot Fix

Fixes two related integration issues:

1) Main portal shows Mathematics as 0
   Cause: the production Math API is mounted under /math-api, but the frontend
   activity tracker only recognized /api/... paths. It never sent Math events
   to the shared platform.

2) Existing Aiven progress does not exist in the portal Firestore dashboard
   Cause: Aiven is the Mathematics source of truth, while the portal summarizes
   shared Firestore analytics.

New design:
Aiven Math data -> lightweight /api/student/platform-summary -> background
frontend sync -> Firestore subject_snapshots -> main portal dashboard.

The sync runs AFTER successful Math login and is not awaited, so it does not
add time to the "Opening Mathematics" screen.

DEPLOYMENTS REQUIRED
A) Math backend (new lightweight summary endpoint)
B) Platform/Auth backend (new subject snapshot endpoint + dashboard merge)
C) Final frontend (tracker + background sync)

No database migration is required. Firestore creates subject_snapshots
automatically on first sync.

COPY
Copy the contents of this folder into:
C:\Users\User\Documents\EasyLearn_DeploymentReady_CLEAN
and replace files.


PERCEIVED MATH SPEED
The portal now also sends a non-blocking warm-up GET to /math-api/ after login.
This starts the Math Vercel Function while the user is viewing the portal, so
clicking Mathematics is less likely to wait for the full cold start.
