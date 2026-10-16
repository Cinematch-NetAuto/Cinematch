# Contributing to CineMatch

How the four of us work on this repository. Read [README.md](README.md) first
and finish the setup steps there.

---

## 1. Who owns what

Everyone writes some backend **and** some frontend. Your individual contribution
is assessed, and `git shortlog -sn` shows it.

| Role | Owns | Main files |
|---|---|---|
| **Dev 1 — Setup** | Repo, database, scripts, app shell, look and feel, Jenkins, README | `docker-compose.yml` · `backend/db/` · `backend/scripts/` · `app/config.py` · `app/db.py` · `app/main.py` · `Jenkinsfile` · `App.jsx` · `Layout.jsx` · `NavBar.jsx` · `States.jsx` · `styles/` |
| **Dev 2 — Movie data** | TMDB, cache, search, filters, paging | `app/tmdb.py` · `services/movies.py` · `routers/movies.py` · `MovieCard` · `MovieGrid` · `FilterPanel` · `Paginator` · `Home`, `Search` and `Discover` pages |
| **Dev 3 — Accounts** | Sign-up, login, tokens, `apiFetch`, preferences | `app/security.py` · `app/deps.py` · `routers/auth.py` · `api/client.js` · `AuthContext` · `Login`, `Register`, `Preferences` pages |
| **Dev 4 — Recommender** | Likes, history, scoring, reasons | `services/recommend.py` · `routers/library.py` · `routers/recommend.py` · `ReasonChip` · `MovieDetail`, `Library`, `Recommendations` pages |

**Names:** Dev 1 = ______ · Dev 2 = ______ · Dev 3 = ______ · Dev 4 = ______

**Where do I start?** [docs/build-plan.md](docs/build-plan.md) splits the app into
numbered steps. **One step = one commit. One phase = one branch and one pull
request.** Take the next open step in your lane.

---

## 2. Branches

```
main  <-  dev  <-  feat/<what>
```

| Branch | Purpose | Who writes to it |
|---|---|---|
| `main` | Always runs. Demo-ready. Updated when a phase is merged and demoed | Dev 1 only, by merging `dev` |
| `dev` | The shared workspace. **Default branch** | Pull requests only |
| `feat/<what>` | Your work, e.g. `feat/search-api` | You |
| `fix/<what>` | A bug fix, e.g. `fix/null-poster` | You |

**Never push to `main`. Never merge your own pull request.**

### The daily loop

```bash
git checkout dev
git pull origin dev                     # start from the latest work
git checkout -b feat/jd-search-api      # one branch per task

# ... write code, commit small steps ...

cd backend && pytest -q && ruff check . # both must pass
git push -u origin feat/jd-search-api
# open a pull request into dev on GitHub
```

If your branch is more than a day old, run `git pull origin dev` on it before you
open the pull request. It is easier to fix a conflict on your branch than in review.

### Commit messages

One line, present tense, with a type:

```
feat: add title search endpoint
fix: show placeholder when a film has no poster
test: cover the 500-page cap in to_tmdb_page
docs: add the cold-start decision
chore: pin pytest-cov
```

---

## 3. Pull requests

1. **Small.** Under about 400 changed lines. Big pull requests get waved through,
   not reviewed.
2. **Green.** `pytest -q` and `ruff check .` pass. For frontend work, `npm run build`
   passes.
3. **Reviewed out loud.** Share your screen and read your change to one teammate,
   line by line, for about 15 minutes. The reviewer asks *"why?"* at least twice.
   Then the reviewer approves and merges.
4. **Rotate reviewers.** Never the same pair twice in a row.

The read-aloud review is not bureaucracy. Every one of us should be able to
explain every part of the app. This is how we get there.

The pull request template has a checklist. Fill it in.

---

## 4. Hot files — announce before you edit

Several people edit these files. **Post in the group chat before you start,** push
the same day, and keep your additions in their own block.

`backend/app/main.py` · `backend/app/models.py` · `backend/app/schemas.py` ·
`backend/db/schema.sql` · `backend/requirements.txt` · `frontend/src/App.jsx` ·
`frontend/package.json`

---

## 5. Code rules

These rules are what keep four people's code readable as one app.

### Backend

| Rule | Why |
|---|---|
| Only `app/tmdb.py` calls TMDB, and only it imports `requests` | One place to change if TMDB changes; the token never leaks |
| Only `app/config.py` calls `os.getenv` | Every setting is in one file, with a comment |
| Routers stay thin: read the request, call one service, return | Logic in services can be tested without a server |
| Every TMDB call has a timeout | One slow call must not freeze the app |
| Tests never touch the internet | Mock `app.tmdb`. Tests must pass on the train and in Jenkins |
| Passwords: bcrypt only. Reject passwords over 72 bytes | bcrypt silently cuts longer ones |
| A failed login says only *"Invalid email or password"* | Do not tell an attacker which half was wrong |
| Use `TIMESTAMPTZ` and `NUMERIC`, never plain `TIMESTAMP` or `FLOAT` | Time zones and exact decimals |

### Frontend

| Rule | Why |
|---|---|
| Every API call goes through `apiFetch()` in `src/api/client.js` | Adds the token and handles errors in one place |
| Never call TMDB from the browser | The token would be public |
| Colours, spacing and fonts come only from `styles/tokens.css` | One look; no raw colour codes anywhere else |
| Every screen that loads data shows three states: loading, empty, error | Use the components in `States.jsx` |
| Filter and page state lives in the URL | Back button works; a demo is one pasted link |
| Every film card works when the poster is missing | Some TMDB films have no poster |

### Both

- **No secrets in the repo.** `.env` is gitignored. Do not commit tokens, keys or
  passwords, and do not paste them into the group chat.
- **Pinned versions.** Add a package with an exact version and a comment saying
  why. Commit `frontend/package-lock.json` — the pipeline runs `npm ci`, which
  fails without it.
- Python style is whatever `ruff check .` accepts. Line length is 100.

---

## 6. Tests

| Test it | Do not test it |
|---|---|
| Pure logic: paging maths, scoring, hashing, token expiry | FastAPI, SQLAlchemy or React themselves |
| Each endpoint's success case and its main failure (401, 404, 409, 422) | TMDB's real answers — mock them |
| Every bug you fix — add a test that fails before the fix | Exact pixel layout |

Run from `backend/`:

```bash
pytest -q                 # quick
pytest --cov=app          # with coverage, as the pipeline does
```

We report coverage. We do not block merges on a coverage number.

---

## 7. Team rhythm

| What | When |
|---|---|
| Stand-up: what I did, what is next, what is blocking me (15 min) | Tuesday and Thursday |
| Demo: run the app together and show the week's result (20 min) | Every Friday |
| Merge `dev` into `main` | After a phase is merged and shown at the demo |
| Stuck for 2 hours? **Ask in the chat.** | Always |

---

## 8. Docs you add to as you go

| File | Add an entry when… |
|---|---|
| [docs/decisions.md](docs/decisions.md) | You choose between two real options. Write down the one you rejected and why |
| [docs/glossary.md](docs/glossary.md) | Someone has to ask what a word means |
| [docs/manual-tests.md](docs/manual-tests.md) | A feature can be clicked through in the browser |

Used an AI tool? Keep your own short note the same day: the date, the tool and
version, what you asked, and what you kept. The team collects these notes.

---

## 9. Definition of done

A task is done when **all** of these are true:

- [ ] Its "done when" test in [docs/build-plan.md](docs/build-plan.md) passes
- [ ] Tests and lint are green
- [ ] It was reviewed out loud and merged into `dev`
- [ ] It works on a second person's laptop
- [ ] The README status table is still true
