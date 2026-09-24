# Bahasa Melayu final update

- Uses the shared Portal session and shared Firestore profile.
- Stores BM users, assessment sessions, and results in Firestore; MongoDB is no
  longer required.
- Displays the complete account name and shared `S-` Student ID.
- Uses the shared EasyLearn logo, aligned Mathematics-style header/profile menu,
  Student ID help tooltip, and reduced dashboard top spacing.
- Sends meaningful submissions to the canonical `learning_events` collection.
- Has no subject logout control; logout is available only from the Portal.

Existing practice, quiz, speaking, listening, writing, and AI tutor content is
preserved.
