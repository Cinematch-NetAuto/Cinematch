# Recommender evaluation

How well does CineMatch find films that a user likes? This page measures that offline
using the three demo users. It also records the effect of one weight change.

## How to run it

Run these commands from `backend/` while the database is running and the demo data is
loaded:

```bash
python -m scripts.seed_data     # only if the demo users or films are missing
python -m scripts.evaluate
```

It took 4.6 seconds on our PC, with the TMDB answers already in the cache. Without
cached answers, the script needs TMDB.

## Method: leave one out

- The three demo users in `backend/scripts/seed_data.py` have 8 likes in total. Ava
  has 3, Ben has 3, and Cleo has 2.
- The test hides each like once, which makes 8 trials. In each trial, a temporary
  stand-in user gets a copy of the demo user's starter genres, likes, dislikes, and
  watch history. The hidden film is left out of that copy.
- The real recommender (`backend/app/services/recommend.py`) picks 20 films for the
  stand-in. A hit means the hidden film appears in the top 10.
- Precision@10 is the number of hits in the top 10, divided by 10, and averaged over
  the 8 trials. Because each trial has one hidden film, the best possible value is
  0.10. That makes the hit count easier to read.
- Each stand-in is deleted right after its trial. The demo users never change.

## Results (20 October 2026)

| Weights (taste, quality) | Hidden films found in the top 10 | Precision@10 |
|---|---|---|
| 0.7, 0.3 (what CineMatch uses) | 4 of 8 | 0.050 |
| 0.5, 0.5 (the one change) | 4 of 8 | 0.050 |

Here is each trial using the weights that CineMatch uses:

| User | Hidden film | Result |
|---|---|---|
| Ava | Inception | Rank 4 |
| Ava | The Matrix | Not among the 20 |
| Ava | The Dark Knight | Rank 2 |
| Ben | Forrest Gump | Rank 2 |
| Ben | The Shawshank Redemption | Not among the 20 |
| Ben | Titanic | Not among the 20 |
| Cleo | Spirited Away | Rank 3 |
| Cleo | Toy Story | Not among the 20 |

## What the weight change did

Both runs found the same 4 films. Because of that, the two summary numbers are equal.
Only one rank changed. Spirited Away moved from rank 3 to rank 2.

## Why: the misses happen before the scoring

The recommender first builds a shortlist of the 60 highest-rated films in the user's
top 3 genres. It scores the films only after building that shortlist. A one-off check
of the four missed films showed the following:

- Titanic and Toy Story did not make the shortlist. The shortlisted films had ratings
  from 8.1 to 9.1. In the demo data, Titanic and Toy Story are rated 7.9 and 7.99.
- The Matrix and The Shawshank Redemption made the shortlist. However, each film
  shares only one of its two genres with the stand-in's top 3 genres. Because of
  this, both films scored below the top 20. Hiding The Matrix also drops Science
  Fiction out of Ava's top 3 genres. Action, Thriller, and Crime remain as her top 3
  genres.

The weights only change the order of the shortlist. Every film on the shortlist is
rated between 8.1 and 9.1. Because those ratings are so close, the quality score
barely separates the films. Changing the quality weight therefore changes very
little. To find more hidden films, the next thing to change is the shortlist, not the
weights. For example, the shortlist could include more pages, or it could include
popular films alongside top-rated ones.

## Limits

- A test with 3 users and 8 trials is small. One extra hit changes the hit count by 1
  of 8.
- The team wrote the demo users' likes. Real users did not create them.
- TMDB ratings and lists change over time. Because of this, a later run can give
  different numbers.
