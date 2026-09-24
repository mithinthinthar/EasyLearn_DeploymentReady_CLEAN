# EasyLearn final verification

## Startup

- Run `Start-EasyLearn.cmd` and confirm ports 3000, 3001, 4000, 4500, 5000,
  5001, 5173, and 8000 are listening.
- Confirm the Portal and all three subject cards become ready.

## Identity and roles

- Sign in as a Student and confirm a single `S-1234567` ID appears in Portal,
  History, Mathematics, and Bahasa Melayu.
- Confirm the complete display name appears in BM.
- Hover the Student ID information icon and confirm its explanation appears.
- Sign in as Parent and Teacher test accounts; confirm `P-` and `T-` IDs.
- Link the student from a Parent account and view the learner dashboard.
- Confirm there is no subject logout button; Portal logout returns to login.

## New Firestore activity

Complete one scored activity in each subject. In Firestore, verify:

- `learning_events` has `subject`, `studentUid`, `accountId`, `activityType`,
  `percentage`, and `createdAt`.
- History also updates `user_interactions` for its detailed dashboard.
- BM creates or updates the relevant `bm_*_sessions` and `bm_*_results` data.
- Portal totals increase once per meaningful submission, not while idle or
  simply refreshing a page.

## Visual checks

- The same purple list-style EasyLearn logo appears on Portal and all subjects.
- At 100%, 120%, and a narrow mobile width, nav items and profile menus align.
- BM has no excessive empty gap above the dashboard.
- Profile menus animate and do not overflow the right edge.

## Regression checks

- Mathematics questions still load from MySQL.
- History quiz results update its dashboard.
- BM writing, comprehension, speaking, and listening submissions save.
- Each AI tutor answers only its own subject.

Only after every check passes should old MongoDB BM data be deleted. Never
delete `mathsy_db` until Mathematics learning content has also been migrated.
