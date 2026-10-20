# Glossary

Every word someone on the team had to ask about, explained in plain language.
Add a term the day you first use it. One name per thing: if two words mean the
same thing, pick one and list the other as "also called".

| Term | Meaning | Example in our code |
|---|---|---|
| API | The list of addresses that the website calls to get or save data, also called the backend's endpoints. | `backend/app/routers/` |
| Backend | The Python program that handles calls from the website and talks to the database and TMDB. | `backend/` |
| Branch | A separate line of work in Git. This project uses `dev`, `main`, and one `feat/<what>` or `fix/<what>` branch for each task. | `feat/evaluation` |
| Cache | Saved answers that are reused so the app does not ask the same question twice. | The `tmdb_cache` table and `get_or_fetch()` in `backend/app/services/movies.py` |
| CI (continuous integration) | A server that runs automatic checks on every push. This project uses Jenkins. | `Jenkinsfile` |
| Cold start | A new user who has not liked any films yet. The recommender uses the genres picked at sign-up instead. | `top_genres()` in `backend/app/services/recommend.py` |
| Commit | A saved set of changes in the project's history, stored with a short message. | `docs: add recommender evaluation` |
| Component | A single reusable building block of a web page. | `frontend/src/components/MovieCard.jsx` |
| Content-based filtering | Suggesting films similar to ones the user already liked, matched here by their genres. | `genre_match()` in `backend/app/services/recommend.py` |
| Contrast ratio | How much brighter text is compared to its background. Text needs a ratio of at least 4.5 : 1 to be easy to read. | `--programme` on `--night` is 7.89 : 1 |
| Design tokens | Named colours, fonts, and sizes kept in one file so the whole site shares the same look. | `frontend/src/styles/tokens.css` |
| Docker | A tool that runs a program inside its own isolated box so it works the same on every computer. This project uses it for PostgreSQL and Jenkins. | `docker-compose.yml` |
| Endpoint | A single API address paired with one action method, such as GET or POST. | `POST /api/auth/login` |
| FastAPI | The Python library used to build the backend. | `backend/app/main.py` |
| Fixture | A ready-made helper that pytest passes to a test, such as a test client or a logged-in user. | `client`, `db`, `auth_headers` in `backend/tests/conftest.py` |
| Focus ring | The gold outline showing which button, link, or input the keyboard is currently on. | `:focus-visible` in `frontend/src/styles/global.css` |
| Frontend | The part of the website that runs inside the user's browser. | `frontend/` |
| Genre match | The share of a film's genres that are among the user's favourite genres, from 0 to 1. The favourite genres come from the user's likes and sign-up choices. | `genre_match()` |
| Hash (bcrypt) | A one-way scramble of a password. The database saves only this hash, never the real password. | `hash_password()` in `backend/app/security.py` |
| Hot reload | A feature where the development server updates the page automatically whenever a file is saved. Restart it after running `npm install`. | `npm run dev` |
| Jenkins | The project's CI server. It runs install, lint, test, and the frontend build for every new commit on `dev`, `feat/*`, and `fix/*` branches. | http://localhost:8081 |
| JWT (login token) | A signed piece of text from the backend given at login and sent with every call to prove who you are. Also called a token or access token. | `create_token()` in `backend/app/security.py` |
| Leave-one-out | A way to test the recommender by hiding one liked film and checking whether the app recommends it. | `backend/scripts/evaluate.py` |
| Lint | An automatic check that spots code style issues and common mistakes. This project uses ruff. | `ruff check .` |
| Merge | Combining the commits from one branch into another branch. | Pull request #16 into `dev` |
| Merge conflict | A problem where two branches changed the same or nearby lines, so Git cannot combine them automatically. | Why the tick for step 54 waits: rows 53 and 54 of `docs/build-plan.md` are neighbours |
| Pipeline stage | One step in a Jenkins build. If a stage fails, the rest of the build stops. | "Backend: test", "Frontend: build" |
| Precision@10 | The share of the top 10 recommended films that the user actually liked. | `precision_at_k()` in `backend/scripts/evaluate.py` |
| Proxy | A setup where the development server forwards the website's `/api` calls to the backend. | `frontend/vite.config.js` |
| Pull request | A request to merge a branch into `dev`, including a code review and the Jenkins test result. | `.github/pull_request_template.md` |
| Push / pull | Push uploads local commits to GitHub, while pull downloads commits made by others. | GitHub Desktop: Push origin, Pull origin |
| Reason | The short sentence under a recommended film explaining why it was chosen. | `reason_for()` and `ReasonChip.jsx` |
| Reduced motion | A computer or phone setting that tells apps to turn off animations. | `prefers-reduced-motion` in `frontend/src/styles/global.css` |
| Regression test | A test written to make sure a fixed bug does not happen again. | `test_token_survives_a_small_clock_step_back` |
| Route | A page address on the website. | `/me/library` in `frontend/src/App.jsx` |
| Seed data (demo data) | Starter data with sample genres, films, and 3 demo users so the app has content to display right away. | `backend/scripts/seed_data.py` |
| Test suite | The full collection of automatic tests located in `backend/tests/`. | `pytest -q` (93 tests on 20 October 2026) |
| Testing framework (pytest) | The tool that finds tests, runs them, and reports any failures. | `backend/pyproject.toml` |
| TMDB | The Movie Database, which is the external website that supplies the project's film data. | `backend/app/tmdb.py` |
| Virtual environment (venv) | A private folder holding Python packages for this project alone. | `backend/.venv` |
| Vite | The tool that runs the website during development and packages it for release. | `npm run build` |
| Weighted rating | A film's rating adjusted towards the overall site average when it has only a few votes. | `weighted_rating()` in `backend/app/services/recommend.py` |
