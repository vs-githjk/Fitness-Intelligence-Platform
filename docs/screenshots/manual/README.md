# User-manual screenshot index

These screenshots were captured from the running local application by `frontend/e2e/manual-docs.spec.ts`. They contain synthetic demonstration data only.

Full-page capture means the PNG can be taller than the browser viewport. The viewport column records the browser size used to render the responsive layout.

| Screenshot | Role and route | Viewport |
|---|---|---:|
| `login-desktop.png` | Public `/login` | 1440×1000 |
| `registration-desktop.png` | Public `/register` | 1440×1000 |
| `session-expired-desktop.png` | Expired trainee session redirected to `/login` | 1440×1000 |
| `trainee-onboarding-goal-mobile.png` | New trainee `/onboarding`, Goal step | 375×812 |
| `trainee-onboarding-cardio-desktop.png` | New trainee `/onboarding`, Cardio step | 1440×1000 |
| `trainee-onboarding-review-desktop.png` | New trainee `/onboarding`, Review step | 1440×1000 |
| `trainee-baseline-reference-desktop.png` | New trainee `/trainee/dashboard` after submission | 1440×1000 |
| `trainee-daily-check-in-mobile.png` | Seeded trainee `/trainee/check-in` | 375×812 |
| `trainee-today-desktop.png` | Seeded trainee `/trainee/today` | 1440×1000 |
| `trainee-progress-desktop.png` | Seeded trainee `/trainee/progress` | 1440×1000 |
| `coach-dashboard-desktop.png` | Seeded coach `/coach/dashboard` | 1440×1000 |
| `coach-roster-mobile.png` | Seeded coach `/coach/dashboard` | 375×812 |
| `coach-trainee-detail-desktop.png` | Seeded coach, Arjun trainee detail | 1440×1000 |

For stable coach documentation images, the screenshot test filters the live roster response to the two real seeded demo trainees, Arjun and Nila. Scores, alerts, check-in states, and trainee-detail responses still come from the running API.

Regenerate the images after starting Compose:

```bash
cd frontend
npx playwright test e2e/manual-docs.spec.ts
```

Playwright expects the frontend at `http://localhost:5175`, the API at `http://localhost:8000`, and a local Chrome installation.
