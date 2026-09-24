EasyLearn Real Study Time Fix — Bahasa Melayu + History

WHAT WAS WRONG

Bahasa Melayu:
- Total Study Time = total_questions * 2
- Each completed result/day = attempts * 20 minutes
So 14 questions became 28 minutes, and 4 attempts became 80 minutes.

History:
- Total Study Time = total_questions * 2
- Weekly/heatmap minutes = questions_answered * 2

Those numbers were estimates, not measured study time.

WHAT THIS PATCH DOES

Bahasa Melayu:
- Uses the real session created_at and result saved_at timestamps.
- Dashboard total/weekly/heatmap time is based on recorded session elapsed time.
- Adds Ujian Mendengar results to the BM dashboard aggregation.
- Removes the fake "Best study time window: 7:00 PM - 7:20 PM".
- Keeps 20 minutes only as a RECOMMENDED future session length, not past usage.

History:
- History already records real per-question duration_minutes and stores it as
  time_taken_ms in Firestore.
- Backend now aggregates those actual recorded durations.
- Dashboard total/weekly/heatmap time uses that real value.
- Older History records that have no timing field contribute 0 minutes instead
  of inventing 2 minutes per question.
- Removes the fake fixed 7:00 PM personalized timing claim.

DEPLOYMENTS REQUIRED

1) BM backend
2) History backend
3) Final frontend

Platform API does NOT need another deployment for this patch.

NOTE
"Recorded study time" is elapsed time between starting and submitting an
activity. It is far more truthful than a fixed estimate, but if a learner
leaves a quiz open while away from the computer, that idle time can still be
included. A future version can add browser active-time tracking if needed.
