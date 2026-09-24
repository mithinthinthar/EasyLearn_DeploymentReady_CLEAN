# Final consolidation changelog

## Visual and navigation

- Replaced every header/Portal mark with the same Mathematics-style list logo.
- Corrected BM dashboard top spacing, account alignment, full-name greeting, and
  Student ID help tooltip.
- Removed subject-level logout controls; Portal is the only logout authority.
- Preserved the standardized dashboards, navigation, profile animation, and AI
  tutor widgets created in the preceding visual pass.

## Shared identity

- Firestore `easylearn_users` is authoritative for role and account identity.
- New and existing accounts receive `S-`, `P-`, or `T-` plus seven digits on
  their next Portal login.
- The same account ID is synchronized into each subject login adapter.

## Unified data

- `learning_events` is the canonical cross-subject interaction stream.
- History records normalized events and a Firestore compatibility record for
  its detailed dashboard.
- BM's former PyMongo-shaped data layer now persists its existing models to
  Firestore collections, so existing BM routes did not need to be removed.
- Mathematics records meaningful submissions in Firestore while retaining
  MySQL as its required question/content catalogue.

## Validation performed

- History production build: passed (pre-existing lint warnings only).
- Mathematics production build: passed (pre-existing lint warnings only).
- Bahasa Melayu TypeScript/Vite production build: passed.
- Updated Python modules: byte-compiled successfully.
- Portal and tracker JavaScript: syntax-checked successfully.
- Secret/environment files, virtual environments, dependencies, and generated
  build folders are excluded from the delivery ZIP.
