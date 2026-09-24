EASYLEARN - FIRESTORE UNIFIED FINAL
===================================

WHAT CHANGED
------------
- One Portal login for Student, Teacher, and Parent.
- Stable Firestore account IDs: S-1234567, T-1234567, P-1234567.
- Firestore is the canonical identity, relationship, and cross-subject activity store.
- Bahasa Melayu assessment sessions/results now use Firestore instead of MongoDB.
- History and Mathematics send every new learner activity to Firestore learning_events.
- Logout appears only in the main Portal.
- One EasyLearn logo, aligned headers, complete names, and Student ID help messages.

IMPORTANT
---------
Do NOT delete the Mathematics MySQL database. It still contains Mathematics
questions, chapters, marking schemes, and other learning content. Firestore is
now the canonical progress/analytics store, but MySQL remains the Mathematics
content catalogue until a later content migration.

START
-----
1. Complete SETUP-STANDARDIZED.md once.
2. Double-click Start-EasyLearn.cmd.
3. Open http://localhost:4000 if the browser does not open automatically.
4. Sign out only from the Portal.

Existing accounts receive their new role-prefixed ID automatically on the next
Portal login. Old MySQL/MongoDB interaction history is not imported and may be
removed only after the Firestore verification checklist passes.

Never share .env files, Firebase Admin JSON, passwords, or API keys.
