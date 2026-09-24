# EasyLearn Vercel deployment order

Deploy the backends as four separate Vercel projects from the same repository/folder, then deploy the root frontend project.

1. Mathematics backend — root `subjects/mathematics/backend`
2. Platform auth API — root `shared/auth`
3. History backend — root `subjects/history/backend`
4. Bahasa Melayu backend — root `subjects/bahasa_melayu/backend`
5. Final frontend shell — repository root

For Math, History and BM set `VERCEL_SUPPORT_LARGE_FUNCTIONS=1` before deployment if Vercel asks to enable Large Functions.

Vercel installs Python dependencies itself. A local `.venv` is not required for cloud deployment.
