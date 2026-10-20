# Decisions

One entry for each real choice between two options. Write down the option we
**rejected** and why. This file explains why the project looks the way it does,
so write it in your own words, the day you decide.

## Format

```markdown
### D<number> — <the decision, in one line>

- **Date / who:** 2026-10-12 · <name>
- **Chose:** <option>
- **Rejected:** <option>
- **Why:** <one or two sentences>
```

## Decisions

<!-- Newest at the bottom. -->

### D1 — Recommend with content-based filtering and a fair rating

- **Date / who:** 2026-10-16 · team
- **Chose:** Content-based filtering: 70 % genre match with the user's top 3 genres, plus 30 % weighted rating (the IMDb Top 250 formula)
- **Rejected:** Collaborative filtering ("people who liked X also liked Y") or a trained machine-learning model
- **Why:** Collaborative filtering needs ratings from many users, while CineMatch starts with only 3 demo users. Also, the reason under each poster needs a one-sentence explanation, which a content-based score provides.

### D2 — Log in with email and password, not with Google

- **Date / who:** 2026-10-16 · team
- **Chose:** Email and password, with bcrypt password hashes and a JWT login token
- **Rejected:** "Log in with Google" (OAuth)
- **Why:** Google login requires a Google Cloud project, a client ID and secret on every developer's laptop, and internet access at every login, whereas the demo must work offline. Email and password cover the app's needs without sending user data to Google.

### D3 — PostgreSQL, not SQLite

- **Date / who:** 2026-10-16 · team
- **Chose:** PostgreSQL 16 in Docker
- **Rejected:** An SQLite file
- **Why:** The schema relies on PostgreSQL features: an `INTEGER[]` list for starter genres, `TIMESTAMPTZ` times, and "insert or update" for the TMDB cache. Using PostgreSQL means Jenkins and every laptop run the exact same database.

### D4 — Only the database runs in Docker

- **Date / who:** 2026-10-16 · team
- **Chose:** PostgreSQL in Docker; the backend and frontend run directly on the computer
- **Rejected:** The backend and frontend in Docker as well
- **Why:** Installing the database the same way across several laptops is difficult. Running the app code directly outside a container keeps hot reload and a normal debugger working.

### D5 — Save TMDB answers in the database

- **Date / who:** 2026-10-16 · team
- **Chose:** The `tmdb_cache` table: an answer is reused for `CACHE_HOURS`, and an older copy is used when TMDB is down
- **Rejected:** Asking TMDB on every request
- **Why:** Saving answers lets repeated searches skip TMDB and lets the offline demo work.

### D6 — The browser never calls TMDB

- **Date / who:** 2026-10-16 · team
- **Chose:** Every TMDB call goes through the backend, in `backend/app/tmdb.py`
- **Rejected:** The React app calling TMDB directly
- **Why:** Calling TMDB from the browser would expose the TMDB token publicly and skip the backend's cache.

### D7 — Jenkins checks GitHub every 5 minutes

- **Date / who:** 2026-10-16 · team
- **Chose:** A Multibranch Pipeline job that scans GitHub every 5 minutes
- **Rejected:** A GitHub webhook that starts a build on every push
- **Why:** A webhook from outside cannot reach a home PC.

### D8 — Each Jenkins build slot gets its own test database

- **Date / who:** 2026-10-19 · team
- **Chose:** One test database per Jenkins build slot
- **Rejected:** One test database shared by every build
- **Why:** In `dev` build #7, 22 of 80 tests failed because two builds ran at once and deleted each other's test users. The code itself had no bug.

### D9 — A dark page

- **Date / who:** 2026-10-19 · team
- **Chose:** Night blue to black, with gold for anything you can click
- **Rejected:** A light page with amber tiles, as in the team's first picker sketch
- **Why:** Bright, colourful posters stand out well on a dark page. Gold tiles and buttons match the colours from the team's sketch.

### D10 — No animation

- **Date / who:** 2026-10-19 · team
- **Chose:** Pages appear at once; a chosen tile changes colour instantly
- **Rejected:** Fade-in and slide-in animations
- **Why:** With no animation, nothing can stutter during a demo, and users who set their system to reduce motion get none.

### D11 — "Movie rating" means the score

- **Date / who:** 2026-10-20 · team
- **Chose:** The TMDB score out of 10 (`min_rating`)
- **Rejected:** The age rating (PG, M, R)
- **Why:** The backend already filters films by score. Filtering by age rating would require new backend work for every film.

### D12 — Keep the login token in the browser's storage

- **Date / who:** 2026-10-20 · team
- **Chose:** `localStorage`, sent in the `Authorization` header of every API call
- **Rejected:** An httpOnly cookie
- **Why:** Sending a token in a header needs no CSRF protection and works the same in the browser, tests, and `/docs`. However, any script on the page can read `localStorage`, so the site must never run third-party scripts.

### D13 — Login tokens allow 30 seconds of clock difference

- **Date / who:** 2026-10-20 · team
- **Chose:** `CLOCK_LEEWAY` of 30 seconds when a token is checked
- **Rejected:** No leeway
- **Why:** The Docker clock once jumped back 3.8 seconds, making a new token look as if it came from the future. That caused a Jenkins test run to fail with 401.

### D14 — Equally good liked films take turns in the reasons

- **Date / who:** 2026-10-20 · team
- **Chose:** When several liked films share as many genres with a film, the one named least often so far is named
- **Rejected:** The most recent like wins every tie
- **Why:** In a test with 3 liked films, all 20 reasons said "Because you liked Up". With turns, the 20 reasons named the 3 films 7, 7 and 6 times.

### D15 — The film page backdrop is drawn at 20 %

- **Date / who:** 2026-10-20 · team
- **Chose:** Opacity 0.2
- **Rejected:** Opacity 0.5
- **Why:** Text sits over the backdrop image. At 0.5 opacity, grey text on a white area had a contrast of 1.48 : 1, whereas at 0.2 it reaches at least 4.55 : 1.

### D16 — Keep the scoring weights at 0.7 and 0.3

- **Date / who:** 2026-10-20 · team
- **Chose:** Taste 0.7, quality 0.3
- **Rejected:** Taste 0.5, quality 0.5
- **Why:** The evaluation found 4 of 8 hidden films under both settings (`docs/evaluation.md`). Because the weights only reorder a shortlist of films rated 8.1 to 9.1, improving the shortlist comes next.
