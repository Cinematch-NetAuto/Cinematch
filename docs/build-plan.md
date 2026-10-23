# Build plan — one step, one commit

The whole app as small numbered steps, grouped into phases. There are no dates.
Work phase by phase, step by step.

- **One step = one commit.** Each step names its files, its commit message and its check.
- **One phase = one branch and one pull request** per owner.
- A phase can start when the phases in its **Needs** line are merged into `dev`.
  Phases with different owners can run at the same time.
- Tick the box (`[x]`) in the commit that finishes the step.
- The owner commits their own step, from their own GitHub account.

---

## How to commit each step

**Start of a phase** — make your branch from the latest `dev`:

```bash
git checkout dev
git pull origin dev
git checkout -b feat/<phase-name>
```

**Each step** — read your change, run the step's check, then commit only that step's files:

```bash
git diff
cd backend && pytest -q && ruff check . && cd ..   # from Phase 1 on
git add <the files in the step>
git commit -m "<the commit message in the step>"
git push -u origin feat/<phase-name>   # later pushes: just  git push
```

Use `git add <files>`, not `git add -A` or `git add .`. You see exactly what goes in.

**End of a phase:**

1. If you used an AI tool in this phase, add it to your own AI-use note (date, tool,
   what you asked, what you kept).
2. Open a pull request into `dev`. Review it out loud with a teammate. The teammate merges.
3. Everyone runs `git checkout dev` and `git pull origin dev`.
4. If the app runs end to end, Dev 1 merges `dev` into `main` with a pull request.

---

## Phase 0 — Save what already exists

**Owner:** Dev 1 · **Branch:** `main` (the only time anyone commits to `main` directly) · **Needs:** —

First, get anything teammates already pushed:

```bash
git checkout main
git pull origin main
```

If git says your local changes *"would be overwritten"*, run `git stash`, then
`git pull origin main`, then `git stash pop`, and fix any conflict it reports.

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 1 | `chore: fill setup files` | `.gitignore` `.env.example` `docker-compose.yml` `backend/requirements.txt` `backend/pyproject.toml` | `docker compose up -d db` → `docker compose ps` says **healthy**. `git status` does not list `.env` |
| [x] | 2 | `docs: add README, contributing guide, build plan and PR template` | `README.md` `CONTRIBUTING.md` `docs/` `.github/` | `git status` is clean |

Then create `dev` and make it the default branch:

```bash
git push origin main
git checkout -b dev
git push -u origin dev
```

On GitHub: **Settings → General → Default branch → `dev`**. From now on, nobody commits
to `main` directly.

---

## Phase 1 — First green tests

Pure logic: no database, no internet. Three people can do this at the same time,
each on their own branch. **After this phase `pytest -q` passes**, so the
"green before you push" rule works from here on.

**Needs:** Phase 0

| ✓ | # | Owner | Commit message | Files | Done when |
|---|---|---|---|---|---|
| [x] | 3 | Dev 2 | `feat: add to_tmdb_page() paging maths with tests` | `backend/app/services/movies.py` `backend/tests/test_pagination.py` | Tests pass: page 1 at 20/page; page 2 at 10/page; page 3 at 10/page; the 500-page cap; `per_page=15` raises `ValueError` |
| [x] | 4 | Dev 4 | `feat: add the three scoring functions with tests` | `backend/app/services/recommend.py` `backend/tests/test_scoring.py` | Tests pass: 8.4 from 36,000 votes beats 9.5 from 12; a liked genre beats an unliked one; `genre_match` with no genres returns 0.0 |
| [x] | 5 | Dev 3 | `feat: add bcrypt password hashing with tests` | `backend/app/security.py` `backend/tests/test_security.py` | Tests pass: right password passes; wrong fails; the same password hashed twice gives two different hashes; over 72 bytes is rejected |

---

## Phase 2 — The backend starts

**Owner:** Dev 1 · **Needs:** Phase 0

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 6 | `feat: create the 8 tables in schema.sql` | `backend/db/schema.sql` | Use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`, so it can run twice. Checked in step 9 |
| [x] | 7 | `feat: read every setting in config.py` | `backend/app/config.py` | From `backend/`: `python -c "from app.config import TMDB_BASE, CACHE_HOURS; print(TMDB_BASE, CACHE_HOURS)"` prints `https://api.themoviedb.org/3 6` |
| [x] | 8 | `feat: add database engine and get_db()` | `backend/app/db.py` | `python -c "from app.db import engine; engine.connect().close(); print('ok')"` prints `ok` |
| [x] | 9 | `feat: add init_db script` | `backend/scripts/init_db.py` | `python -m scripts.init_db` runs **twice** with no error. `docker exec cinematch-db psql -U cinematch -d cinematch -c "\dt"` lists 8 tables |
| [x] | 10 | `feat: add FastAPI app with /health` | `backend/app/main.py` `backend/app/schemas.py` | `uvicorn app.main:app --reload` → http://localhost:8000/health shows `{"status":"ok"}` and `/docs` loads |
| [x] | 11 | `docs: README status — backend starts` | `README.md` | The status table says the backend starts |

> **Traps**
> - Run scripts as `python -m scripts.init_db` from `backend/`. Plain
>   `python scripts/init_db.py` fails with *"No module named 'app'"*.
> - `load_dotenv()` in `config.py` finds the `.env` in the repo root on its own.
>   `config.py` is the only file that calls `os.getenv`.
> - Do **not** include the routers in `main.py` yet. An empty router file has no
>   `router` object, so the app will not start. Each router is added to `main.py` in
>   the step that gives it its first endpoint.

---

## Phase 3 — Automatic checks (CI)

**Owner:** Dev 1 · **Needs:** Phases 1 and 2

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 12 | `ci: add Jenkinsfile with install, lint and test stages` | `Jenkinsfile` `jenkins/Dockerfile` `docker-compose.yml` | Jenkins runs on a push and goes green. Break one test on purpose → it goes red. Screenshot both |

> **Traps**
> - The official Jenkins image has no Python. `jenkins/Dockerfile` adds it.
>   Start Jenkins with `docker compose up -d jenkins` → http://localhost:8081.
> - Secrets go in Jenkins (**Manage Jenkins → Credentials**), never in the `Jenkinsfile`.
> - Check GitHub on a timer, every 5 minutes. A GitHub webhook cannot reach a home
>   laptop. In a **Multibranch Pipeline** job this is *Scan triggers → Periodically,
>   5 minutes*; a plain Pipeline job uses **Poll SCM** (`H/5 * * * *`).
> - Break the test on a **throwaway branch**, screenshot the red build, then delete
>   the branch. The real history stays clean.
> - If Jenkins takes more than one day to set up, stop. Add a GitHub Actions
>   workflow instead, keep the `Jenkinsfile`, and document the comparison.
> - The frontend build stage comes later, in step 39.

---

## Phase 4 — Movies from TMDB

**Owner:** Dev 2 · **Needs:** Phase 2

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 13 | `feat: add TMDB client with timeout and retries` | `backend/app/tmdb.py` | Functions `search`, `discover`, `movie_detail`, `genres`. In a Python shell, `search("inception")` returns real titles |
| [x] | 14 | `feat: add Genre, Movie, MovieGenre and TmdbCache models` | `backend/app/models.py` | Imports clean. Every column name matches `schema.sql`. **Hot file — announce it** |
| [x] | 15 | `feat: add get_or_fetch() TMDB cache` | `backend/app/services/movies.py` | The same search twice → the log shows only **one** TMDB call |
| [x] | 16 | `feat: add genres and title search endpoints` | `backend/app/routers/movies.py` `backend/app/schemas.py` `backend/app/main.py` | `GET /api/genres` and `GET /api/movies/search` work in `/docs`. 10 and 20 per page both correct |
| [x] | 17 | `feat: add discover and movie detail endpoints` | `backend/app/routers/movies.py` `backend/app/services/movies.py` `backend/app/schemas.py` `backend/app/tmdb.py` | Every filter (genres, years, sort, region, minimum rating) works in `/docs`. Detail returns cast and saves the film in `movies` |

> **Traps**
> - `tmdb.py` is the only file that imports `requests`. Every call has a timeout.
> - Genres in discover are joined with `|` (OR). A `,` means AND and returns almost nothing.
> - "Top rated" needs `vote_count.gte=200`, or films with one vote win.
> - When TMDB cannot be reached, `get_or_fetch` should return the old saved copy
>   instead of failing. The offline demo (step 53) depends on this.
> - Declare `/movies/discover` **before** `/movies/{tmdb_id}`, or "discover" is read
>   as a film id. An unknown film must answer 404 (`TmdbNotFound`), not 502.
> - Use `Annotated[...]` for `Depends`/`Query` parameters: ruff's B008 rejects
>   `= Depends(...)` defaults, and Jenkins runs ruff.

---

## Phase 5 — Accounts

**Needs:** Phase 1 (hashing) and Phase 2

| ✓ | # | Owner | Commit message | Files | Done when |
|---|---|---|---|---|---|
| [x] | 18 | Dev 3 | `feat: add User model` | `backend/app/models.py` | Matches `users` in `schema.sql`. **Hot file** |
| [x] | 19 | Dev 4 | `feat: add Rating, WatchHistory and UserPreferences models` | `backend/app/models.py` | Match the schema. **Hot file — coordinate with step 18** |
| [x] | 20 | Dev 3 | `feat: add login tokens with tests` | `backend/app/security.py` `backend/tests/test_security.py` | `create_token` and `read_token`. Tests pass: a tampered token fails; an expired token fails |
| [x] | 21 | Dev 3 | `feat: add get_current_user() dependency` | `backend/app/deps.py` | Reads the `Authorization` header, loads the user, raises 401 otherwise |
| [x] | 22 | Dev 3 | `feat: add register, login and current-user endpoints` | `backend/app/routers/auth.py` `backend/app/schemas.py` `backend/app/main.py` | In `/docs`: register (with 3+ genres) → login → **Authorize** → `GET /api/users/me` returns you. Duplicate email → 409. Wrong password → only *"Invalid email or password"* |

> **Trap:** register also creates the user's `user_preferences` row with the genres
> they picked. Without it, the recommender has nothing for a new user (cold start).

---

## Phase 6 — Test setup and demo data

**Needs:** Phases 4 and 5

| ✓ | # | Owner | Commit message | Files | Done when |
|---|---|---|---|---|---|
| [x] | 23 | Dev 1 | `test: add shared fixtures client, db and auth_headers` | `backend/tests/conftest.py` `backend/app/config.py` `.env.example` | A new test file needs no setup code of its own |
| [x] | 24 | Dev 3 | `test: register, login and protected route` | `backend/tests/test_api_auth.py` `Jenkinsfile` | Register → login → `/api/users/me` gives 200 → the same call without a token gives 401 |
| [x] | 25 | Dev 1 | `feat: add seed_data script` | `backend/scripts/seed_data.py` | `python -m scripts.seed_data` on an empty database adds 19 genres, 3 demo users and some likes. The demo users can log in |
| [x] | 26 | Dev 1 | `docs: README status — tests and demo data` | `README.md` | Status table updated |

> **Traps**
> - Tests use a **separate database** (`cinematch_test`), never the one you develop
>   on. `conftest.py` creates it on first use.
> - Tests must never call TMDB. Replace `app.tmdb` with a mock.
> - Use `127.0.0.1`, not `localhost`, in `DATABASE_URL`: on some Windows PCs
>   "localhost" tries IPv6 first and every new connection waits about 20 seconds.
> - Jenkins now needs to reach PostgreSQL too. Jenkins and the database share the
>   docker-compose network, so the host is `db`. The Jenkinsfile sets `DATABASE_URL`
>   to a separate name per executor (build slot), so CI tests use `cinematch_ci_0_test`
>   or `cinematch_ci_1_test`. Two builds can run at once, and a shared test database
>   lets each run empty the other's tables.
> - A like points at a row in `movies`, so the seed script must insert those films first.

---

## Phase 7 — Likes and watch history

**Owner:** Dev 4 · **Needs:** Phase 5

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 27 | `feat: add like, dislike and watch-history endpoints` | `backend/app/routers/library.py` `backend/app/schemas.py` `backend/app/main.py` | `GET`/`PUT`/`DELETE /api/me/likes`, `GET`/`POST /api/me/history` work in `/docs`. Liking twice leaves one row. A dislike replaces a like |
| [x] | 28 | `test: likes and watch history` | `backend/tests/test_api_library.py` (new) | Those rules as tests, plus 401 without a token |

> **Trap:** before saving a like, make sure the film is in `movies` (fetch and save it
> if not). Otherwise the database rejects the like.

---

## Phase 8 — Recommendations

**Owner:** Dev 4 · **Needs:** Phases 4 and 7

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 29 | `feat: add recommendation pipeline` | `backend/app/services/recommend.py` | Top 3 genres → candidates from discover → drop watched, rated and below minimum rating → score → top 20, in under a second |
| [x] | 30 | `feat: add recommendations endpoint with reasons` | `backend/app/routers/recommend.py` `backend/app/schemas.py` `backend/app/main.py` | `GET /api/me/recommendations` returns 20 films, each with a score **and** a sentence such as *"Because you liked Inception"* |
| [x] | 31 | `test: recommendations skip seen films and give reasons` | `backend/tests/test_scoring.py` | A watched film is never recommended. Every reason names a real liked film or genre |
| [x] | 32 | `docs: README status — backend complete` | `README.md` | Status table updated |

---

## Phase 9 — Design and frontend shell

**Owner:** Dev 1 · **Needs:** Phase 0 (can run alongside the backend phases)

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 33 | `docs: add the design plan` | `docs/design.md` (new) | One line each: who uses CineMatch, and the one job of the site. A palette of 4–6 named colours with hex values. The typefaces and their roles. A sketch of Home and the poster grid. Three design principles. A short list of the generic looks you checked against, and what you changed |
| [x] | 34 | `feat: set up React with Vite` | `frontend/package.json` `frontend/package-lock.json` `frontend/vite.config.js` `frontend/index.html` `frontend/src/main.jsx` `frontend/src/App.jsx` | `npm run dev` serves a page on 5173. `/api` is proxied to `http://127.0.0.1:8000`. `npm run build` passes |
| [x] | 35 | `feat: add design tokens and global styles` | `frontend/src/styles/tokens.css` `frontend/src/styles/global.css` `frontend/src/main.jsx` `frontend/package.json` `frontend/package-lock.json` | Colours, fonts, spacing and radius from `docs/design.md`, as CSS variables in `tokens.css` only. Fonts are installed locally, not loaded from the internet |
| [x] | 36 | `feat: add all nine routes with placeholder pages` | `frontend/src/App.jsx` `frontend/src/pages/*.jsx` `frontend/package.json` `frontend/package-lock.json` | Routes use `react-router-dom`. Each URL shows its page name: `/` `/login` `/register` `/search` `/discover` `/movie/:id` `/me/recommendations` `/me/library` `/me/preferences` |
| [x] | 37 | `feat: add Layout, NavBar and footer` | `frontend/src/components/Layout.jsx` `frontend/src/components/NavBar.jsx` `frontend/src/App.jsx` `frontend/src/styles/global.css` | The nav bar moves between all nine screens. The footer shows the TMDB notice: *"This product uses the TMDB API but is not endorsed or certified by TMDB."* |
| [x] | 38 | `feat: add loading, empty and error states` | `frontend/src/components/States.jsx` `frontend/src/styles/global.css` | Three small components every list screen can use |
| [x] | 39 | `ci: add frontend build stage to Jenkinsfile` | `Jenkinsfile` `jenkins/Dockerfile` | The image gets Node.js 20 or newer: `docker compose build jenkins`, then `docker compose up -d jenkins`. Jenkins runs `npm ci && npm run build` and stays green |

> **Traps**
> - Commit `package-lock.json`. `npm ci` in Jenkins fails without it.
> - The offline demo has no internet, so fonts loaded from a font website would fail.
>   Install the font as an npm package (for example from `@fontsource`) instead.
> - The TMDB footer notice is a condition of using the API, not decoration.
> - Point the Vite proxy at `http://127.0.0.1:8000`, not `localhost`. The backend
>   listens on 127.0.0.1 only, and "localhost" can resolve to the IPv6 address first.
> - The Jenkins image has Python but no Node.js. Step 39 adds Node to
>   `jenkins/Dockerfile` and rebuilds the image.
> - After `npm install` of a new package, stop and restart `npm run dev`. A running
>   dev server can load two copies of React, and the page fails with "Invalid hook
>   call". Restart it too when the page breaks right after edits to several files
>   (for example "useAuth() must be used inside <AuthProvider>" although it is):
>   the hot reload can mix old and new copies of a file.

---

## Phase 10 — Login screens

**Owner:** Dev 3 · **Needs:** Phases 5 and 9

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 40 | `feat: add apiFetch() for every API call` | `frontend/src/api/client.js` | Adds the token. Throws on errors. On 401, clears the token and goes to `/login`. **Every page waits on this — do it first** |
| [x] | 41 | `feat: add AuthContext and protected routes` | `frontend/src/context/AuthContext.jsx` `frontend/src/App.jsx` `frontend/src/components/NavBar.jsx` `frontend/src/styles/global.css` | A refresh keeps you logged in. A logged-out user is sent away from `/me/*` |
| [x] | 42 | `feat: add Login and Register pages` | `frontend/src/pages/Login.jsx` `frontend/src/pages/Register.jsx` `frontend/src/context/AuthContext.jsx` `frontend/src/styles/global.css` `frontend/src/styles/tokens.css` | Register (pick at least 3 genres) logs you in and lands on Home |

---

## Phase 11 — Search and browse screens

**Owner:** Dev 2 · **Needs:** Phases 4, 9 and step 40

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 43 | `feat: add MovieCard and MovieGrid` | `frontend/src/components/MovieCard.jsx` `frontend/src/components/MovieGrid.jsx` `frontend/src/styles/global.css` `docs/design.md` | Poster, title, year, rating, link to detail. A film with **no poster** shows a placeholder |
| [x] | 44 | `feat: add Search page` | `frontend/src/pages/Search.jsx` `frontend/src/styles/global.css` | Typing (300 ms pause) shows posters. Loading, empty and error states all show |
| [x] | 45 | `feat: add FilterPanel and Paginator` | `frontend/src/components/FilterPanel.jsx` `frontend/src/components/Paginator.jsx` `frontend/src/styles/global.css` | Filters are written into the URL. "Page N of M" with a 10/20 toggle |
| [x] | 46 | `feat: add Discover page` | `frontend/src/pages/Discover.jsx` | Every filter works in the browser. A refresh keeps them |
| [x] | 47 | `feat: add Home page` | `frontend/src/pages/Home.jsx` `frontend/src/styles/global.css` | Popular films for everyone, plus a "For you" row when logged in |

---

## Phase 12 — Your films screens

**Owner:** Dev 4 · **Needs:** Phases 7, 8, 9 and step 40

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 48 | `feat: add MovieDetail page with like, dislike and watched` | `frontend/src/pages/MovieDetail.jsx` `frontend/src/styles/global.css` `frontend/src/styles/tokens.css`; the backdrop: `backend/app/services/movies.py` `backend/app/schemas.py` `backend/tests/conftest.py` `backend/tests/test_api_movies.py` (new) | Poster, overview, cast. The buttons still show the right state after a refresh |
| [x] | 49 | `feat: add Library page` | `frontend/src/pages/Library.jsx` `frontend/src/styles/global.css` | Liked, Disliked and History tabs (the History tab is labelled "Watched"). A like can be removed |
| [x] | 50 | `feat: add Recommendations page with reasons` | `frontend/src/components/ReasonChip.jsx` `frontend/src/pages/Recommendations.jsx` `frontend/src/components/MovieCard.jsx` `frontend/src/styles/global.css` | **Like 3 films → refresh → the list changes** |

---

## Phase 13 — Preferences and language

**Owner:** Dev 3 · **Needs:** Phases 8 and 10

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 51 | `feat: add preferences endpoints and page` | `backend/app/routers/library.py` `backend/app/schemas.py` `backend/tests/test_api_library.py` `frontend/src/pages/Preferences.jsx` | `GET` and `PATCH /api/me/preferences`, with tests: a change is saved, a bad value gives 422, no token gives 401. Raise the minimum rating → recommendations change |
| [ ] | 52 | `feat: switch content language` | `frontend/src/api/client.js` `backend/app/tmdb.py` `backend/app/services/movies.py`, the routers that pass the language on, and a test | Switch language → film titles and overviews change. A test shows that two languages get two cache entries. **`tmdb.py` is Dev 2's file — agree the change with them** |

> **Traps**
> - The language must be part of the TMDB cache key. Otherwise the cache serves the
>   English copy of a page to someone who chose another language.
> - Each user already has a language: `users.content_language` (default `en-US`),
>   returned by `GET /api/users/me`. Save a logged-in user's choice there. A visitor
>   who is not logged in keeps the choice in the browser.

---

## Phase 14 — Offline demo and polish

**Owner:** Dev 1 · **Needs:** Phases 4 and 9–13

| ✓ | # | Commit message | Files | Done when |
|---|---|---|---|---|
| [x] | 53 | `feat: add warm_cache script for the offline demo` | `backend/scripts/warm_cache.py` | `python -m scripts.warm_cache` saves about 300 films. **Wi-fi off → search and discover still work** |
| [x] | 54 | `fix: responsive layout, keyboard focus and reduced motion` | `frontend/src/styles/*.css` and the components that need it | Every page works at 375 px wide. Tab reaches every control, with a visible focus ring. Motion stops when the system asks for reduced motion. Text contrast is at least 4.5:1 |

> **Trap:** posters come from TMDB's image server, so offline they show the placeholder.
> If you want real posters offline, let `warm_cache` also save them in `backend/cache/`
> (already gitignored) and serve them from the backend.

---

## Phase 15 — Feature freeze, checks and release

**Needs:** all the phases above. **No new features from here on** — only fixes,
tests, docs and demo practice.

| ✓ | # | Owner | Commit message | Files | Done when |
|---|---|---|---|---|---|
| [x] | 55 | Dev 3 | `docs: add manual test checklist` | `docs/manual-tests.md` | 15 or more click-through steps that someone else can follow |
| [x] | 56 | Dev 4 | `docs: add recommender evaluation` | `backend/scripts/evaluate.py` (new) `docs/evaluation.md` (new) `backend/tests/test_evaluate.py` (new) | `python -m scripts.evaluate` prints Precision@10: hide some of each demo user's likes, then count how many come back in their top 10. Two numbers, before and after one weight change, and what changed |
| [x] | 57 | everyone | `docs: complete decisions and glossary` | `docs/decisions.md` `docs/glossary.md` | At least 8 decisions, each with the rejected option. One of them is why OAuth ("log in with Google") was left out. Every term someone asked about |
| [ ] | 58 | everyone | *(no commit — AI-use notes)* | — | Everyone's AI-use notes are complete: tool, version, prompt and what was kept |
| [x] | 59 | Dev 1 | `docs: final README with screenshots` | `README.md` `docs/screenshots/` | Status section removed. A teammate sets up on a clean laptop without asking a question |
| [ ] | 60 | Dev 1 | *(no commit — release)* | — | Pull request `dev` → `main`, merged. Then `git tag v1.0` and `git push origin v1.0` |

---

## If we run out of time — cut in this order

Cut from the top. Never cut the last row.

| Cut | Steps affected | Cost |
|---|---|---|
| 1. Jenkins → GitHub Actions (keep the `Jenkinsfile`, document the comparison) | 12, 39 | Small |
| 2. Library → one list instead of three tabs | 49 | Small |
| 3. Preferences page → fold into Register | 51 | Medium — lose the "change minimum rating" demo |
| 4. FilterPanel → genre and year only | 45 | Medium — the requirements ask for region |
| 5. Language switch | 52 | Medium — the requirements ask for it |
| 6. Evaluation → describe it in words only | 56 | Medium — lose the "we measured it" result |
| **Never cut** | 25, 30 (reasons), 53, 59, all tests | Demo data, offline demo, unit tests, recommendation reasons, README |
