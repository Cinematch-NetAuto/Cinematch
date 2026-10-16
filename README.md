# CineMatch

A film recommendation web app. You create an account, pick the genres you like,
search and browse films, like or dislike them and mark them watched. CineMatch then
recommends films back to you, each with a written reason — *"Because you liked
Inception"*.

Team project for TAFE NSW **ITNET205A Network Automation**, Assessment 3.
Everything runs on your own computer. There is no hosted version.

| | |
|---|---|
| Backend | Python 3.12 · FastAPI · PostgreSQL 16 (in Docker) |
| Frontend | React 18 · Vite · plain JavaScript and CSS |
| Movie data | [TMDB API](https://developer.themoviedb.org/) (free) |
| Automation | pytest · ruff · Jenkins pipeline |

**New to the project?** Read this file, then [CONTRIBUTING.md](CONTRIBUTING.md),
then pick a task from [docs/build-plan.md](docs/build-plan.md).

---

## Current status — 16 October 2026

The **backend starts**. It has a health check, the database tables and the core
maths, but no movie, account or recommendation endpoints yet. The frontend and
the `Jenkinsfile` are still empty files.

| Part | State |
|---|---|
| Setup files (`.gitignore`, `.env.example`, `docker-compose.yml`, `requirements.txt`, `pyproject.toml`) | done |
| Documentation (this file, `CONTRIBUTING.md`, `docs/build-plan.md`) | done |
| Database: the 8 tables (`db/schema.sql`) and `scripts/init_db.py` | done |
| Backend core: settings, database connection, `GET /health`, paging and scoring maths, password hashing | done — 34 tests pass |
| Backend endpoints: movies (TMDB), accounts, likes and history, recommendations | **not started** — phases 4–8 |
| Frontend, `Jenkinsfile` | **not started** — files exist, 0 bytes |

What that means for the setup steps below:

| Step | Works today? |
|---|---|
| 1. Clone and configure | yes |
| 2. Start the database | yes |
| 3. Start the backend | **yes** — `/health` and `/docs` work. `seed_data` does nothing yet (phase 6), and no endpoint uses the TMDB token yet |
| 4. Start the frontend | **not yet** — needs `frontend/package.json` |
| Run the tests | **yes** — `pytest -q` in `backend/` passes |

The next job is **Phase 3** in [docs/build-plan.md](docs/build-plan.md): the Jenkins pipeline.
Update this section whenever a row changes. Delete it when every row says yes.

---

## What it does

| # | Feature |
|---|---|
| 1 | Register and log in with email and password; stay logged in after a refresh |
| 2 | Search films by title |
| 3 | Browse and filter by genre, year, popularity, rating and country |
| 4 | Show 10 or 20 results per page |
| 5 | Film detail page: poster, overview, rating, genres, cast |
| 6 | Like or dislike a film; mark it watched; see your watch history |
| 7 | Pick starter genres at sign-up; edit your preferences later |
| 8 | **Personal recommendations, each with a one-sentence reason** |
| 9 | Switch content language (English and one other) |
| 10 | Automatic lint, test and build on every push (Jenkins) |

**Out of scope, on purpose:** TV shows, video playback, payments, comments or
sharing, a mobile app, an admin panel, public hosting, e-mail, anything paid.

---

## How it works

```mermaid
flowchart LR
    U["Browser<br/>React app :5173"]
    A["Backend<br/>FastAPI :8000"]
    D[("PostgreSQL :5432<br/>in Docker")]
    T["TMDB API"]
    J["Jenkins<br/>tests every push"]
    G["GitHub"]

    U -->|"/api/... (Vite proxy)"| A
    A -->|SQL| D
    A -->|"HTTPS + secret token"| T
    G --> J
```

Three parts:

1. The **frontend** (React) draws the pages in the browser.
2. The **backend** (Python) answers the frontend's requests.
3. The backend answers from its **own database**, or asks **TMDB** and saves a copy.

**The one rule:** the browser never talks to TMDB. Every TMDB call goes through
the backend, in one file (`backend/app/tmdb.py`). This keeps the API token secret,
lets one cache serve every user, and means a TMDB change touches only one file.

### One request, start to finish

```
1. You type "inception" in the search box.
2. React waits 300 ms after the last key, then calls
       GET /api/movies/search?q=inception&page=1&per_page=10
   with your login token in the Authorization header.
3. Vite forwards /api/* to the backend on port 8000.
4. FastAPI sends the request to search_movies() in app/routers/movies.py.
5. The router calls the service in app/services/movies.py.
6. The service looks in the tmdb_cache table:
     - a saved answer younger than CACHE_HOURS -> use it;
     - otherwise app/tmdb.py asks TMDB and the answer is saved.
7. TMDB always returns 20 films per page. We asked for 10, so we return one half.
8. The backend returns JSON. React draws the poster grid.
```

### How recommendations work

Three small functions in `backend/app/services/recommend.py`:

| Function | What it calculates |
|---|---|
| `weighted_rating` | A fair quality score. A 9.5 from 12 voters counts for less than an 8.4 from 36,000 voters (the IMDb Top 250 formula) |
| `genre_match` | How much of a film is made of genres you like, from 0.0 to 1.0 |
| `score_movie` | `0.7 × taste + 0.3 × quality`. Taste counts more than quality |

Around them, a pipeline:

1. Find your top 3 genres — from films you liked, plus the genres you picked at sign-up.
2. Ask TMDB for well-rated films in those genres (about 60 candidates).
3. Remove films you already watched, rated, or that are under your minimum rating.
4. Score each film. Sort. Keep the top 20.
5. Write a reason for each one: *"Because you liked Inception"*.

A brand-new user has no likes. That is the **cold-start problem**. We solve it by
asking for at least 3 genres at sign-up.

---

## Setup

### What you need installed

| Tool | Version | Check with |
|---|---|---|
| Python | 3.12 or newer | `python --version` |
| Node.js | 20 or newer | `node --version` |
| Docker Desktop | any recent | `docker compose version` |
| Git | any recent | `git --version` |
| A free TMDB account | — | [themoviedb.org/signup](https://www.themoviedb.org/signup) |

### 1. Get the code and make your settings file

```bash
git clone https://github.com/Cinematch-NetAuto/Cinematch.git
cd Cinematch
cp .env.example .env
```

(`cp` works in PowerShell, Git Bash, macOS and Linux. In `cmd.exe` use `copy`.)

Open `.env` and fill in two values:

| Setting | Where to get it |
|---|---|
| `TMDB_API_TOKEN` | TMDB → Settings → API → **API Read Access Token** (the long one, not the short "API Key") |
| `JWT_SECRET` | Run `python -c "import secrets; print(secrets.token_urlsafe(48))"` and paste the output |

Leave every other value as it is. `.env` is gitignored — **never commit it**, and
never paste your token into the group chat. Each developer uses their own token.

### 2. Start the database

```bash
docker compose up -d db
docker compose ps
```

Wait until the `cinematch-db` row says **healthy**. Your data survives
`docker compose down`.

### 3. Start the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# .venv\Scripts\activate.bat      # Windows cmd
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python -m scripts.init_db         # creates the tables
python -m scripts.seed_data       # adds genres and demo users
uvicorn app.main:app --reload
```

### 4. Start the frontend (a second terminal)

```bash
cd frontend
npm install
npm run dev
```

### You are set up when all four are true

- [ ] http://localhost:8000/health shows `{"status": "ok"}`
- [ ] http://localhost:8000/docs shows the interactive API page
- [ ] http://localhost:5173 shows the app
- [ ] `pytest -q` in `backend/` passes

### If something goes wrong

| Symptom | Fix |
|---|---|
| PowerShell: *"running scripts is disabled on this system"* | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use `cmd` and `activate.bat` |
| `docker compose up` fails: port 5432 is in use | Another PostgreSQL is running. Stop it, or change the port to `"5433:5432"` in `docker-compose.yml` **and** in `DATABASE_URL` |
| `cinematch-db` never becomes healthy | Run `docker compose logs db` and read the last lines |
| TMDB answers `401` | `TMDB_API_TOKEN` is empty or wrong. Use the Read Access Token, not the API Key |
| `pytest` says *"No module named 'app'"* | Run it from `backend/`, not from the repository root |

---

## Project layout

```
Cinematch/
├── backend/
│   ├── app/
│   │   ├── main.py            creates the app, CORS, /health, includes the routers
│   │   ├── config.py          reads .env — the ONLY file that calls os.getenv
│   │   ├── db.py              database connection and get_db()
│   │   ├── models.py          one SQLAlchemy class per table
│   │   ├── schemas.py         request and response shapes (Pydantic)
│   │   ├── tmdb.py            the ONLY file that talks to TMDB
│   │   ├── security.py        password hashing and login tokens
│   │   ├── deps.py            get_current_user() — "you must be logged in"
│   │   ├── routers/           URLs: auth, movies, library, recommend
│   │   └── services/          the real work: movies (search, cache, paging), recommend
│   ├── db/schema.sql          the 8 database tables
│   ├── scripts/               init_db, seed_data, warm_cache (offline demo)
│   ├── tests/                 pytest tests
│   ├── requirements.txt       pinned Python packages
│   └── pyproject.toml         pytest and ruff settings
├── frontend/
│   └── src/
│       ├── api/client.js      apiFetch() — every API call goes through it
│       ├── context/           AuthContext — who is logged in
│       ├── components/        MovieCard, MovieGrid, FilterPanel, Paginator, ...
│       ├── pages/             one file per screen (9 screens)
│       └── styles/            tokens.css (all colours) and global.css
├── docs/                      build plan, decisions, glossary, manual tests, AI log
├── docker-compose.yml         PostgreSQL only
├── Jenkinsfile                the CI pipeline
└── .env.example               settings template — copy to .env
```

### The three-layer rule (backend)

| Layer | Its job | It must NOT |
|---|---|---|
| Router (`routers/`) | Read the request, call one service function, return the result | Contain logic or SQL |
| Service (`services/`) | Do the work: query the database, call TMDB, calculate | Know about HTTP |
| Model (`models.py`) | Describe a table | Contain logic |

A service takes plain values and returns plain values, so you can test it
without starting a server.

---

## API (planned)

Once the backend runs, the live list is at http://localhost:8000/docs.

| Method and path | Login? | File |
|---|---|---|
| `GET /health` | no | `main.py` |
| `POST /api/auth/register` · `POST /api/auth/login` | no | `routers/auth.py` |
| `GET /api/users/me` | yes | `routers/auth.py` |
| `GET /api/genres` | no | `routers/movies.py` |
| `GET /api/movies/search?q=&page=&per_page=` | no | `routers/movies.py` |
| `GET /api/movies/discover?genres=&year_from=&year_to=&sort=&region=&min_rating=&page=&per_page=` | no | `routers/movies.py` |
| `GET /api/movies/{tmdb_id}` | no | `routers/movies.py` |
| `GET` / `PUT` / `DELETE /api/me/likes` · `GET` / `POST /api/me/history` | yes | `routers/library.py` |
| `GET` / `PATCH /api/me/preferences` | yes | `routers/library.py` |
| `GET /api/me/recommendations` | yes | `routers/recommend.py` |

---

## Before every push

```bash
cd backend
pytest -q
ruff check .
```

Both must pass. The Jenkins pipeline runs the same checks, plus `npm run build`
for the frontend.

## Working on the project

Branches, pull requests, file ownership and team rules are in
[CONTRIBUTING.md](CONTRIBUTING.md). In short: branch from `dev`, open a pull
request into `dev`, get one teammate to review it, never push to `main`.

## Documentation

| File | What it holds |
|---|---|
| [CONTRIBUTING.md](CONTRIBUTING.md) | How we work: branches, reviews, code rules |
| [docs/build-plan.md](docs/build-plan.md) | The app as numbered steps: one step = one commit, one phase = one pull request |
| [docs/decisions.md](docs/decisions.md) | Each design decision and the option we rejected |
| [docs/glossary.md](docs/glossary.md) | Every project term, in plain words |
| [docs/manual-tests.md](docs/manual-tests.md) | Click-through test steps |
| [docs/ai-usage-log.md](docs/ai-usage-log.md) | Every use of an AI tool — required by the assessment |

## Attribution and licence

This product uses the TMDB API but is not endorsed or certified by TMDB.

Code licensed under the [Apache License 2.0](LICENSE).
