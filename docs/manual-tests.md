# Manual tests

These are step-by-step checks that you do by clicking through CineMatch. A tester who
did not build a feature should be able to follow them without help. Run these checks
before a release (step 60). Also run them after a big change to the app. Every
expected result below was checked on 20 October 2026.

## Before you start

1. Open the Docker Desktop app. Open a command window in the main project folder (the
   repository root) and run `docker compose up -d db`.
2. Go to the `backend/` folder and run `python -m scripts.seed_data`. The last line
   of the output says `Demo logins: ava@, ben@, cleo@example.com, password
   'demo-password'`. This command also resets the three demo users.
3. Stay in the `backend/` folder and run `uvicorn app.main:app --reload`. Open
   http://127.0.0.1:8000/health in your web browser to check that it shows
   `{"status":"ok"}`.
4. Go to the `frontend/` folder and run `npm run dev`. Then open
   http://localhost:5173 in your web browser.
5. Make up a new email address for your test account, such as `tester-1@example.com`.
   You will use this email in tests 16 to 20.

Write ✓ or ✗ in the last column of the table. For every ✗, write down what you saw on
the screen instead.

## Tests

| # | Do this | You should see | ✓ / ✗ |
|---|---|---|---|
| 1 | Open http://localhost:5173 in your browser. | You see a welcome line and a **Sign up** button. You also see a **Popular now** section with 12 film posters. The bottom of the page says "This product uses the TMDB API but is not endorsed or certified by TMDB." | |
| 2 | Click **Search** in the top bar. Type `inception`. | Wait for a short pause. You see film posters and a count like "12 films found". The web address in your browser ends with `?q=inception`. | |
| 3 | Search for `xqzzqx`. | You see the message "No films found for "xqzzqx"." You also see "Check the spelling or try fewer words." | |
| 4 | Click **Discover**. Pick the genres Science Fiction and Drama. Pick the period **1990s** and the rating **7+**. Then click **Show films**. | You see a sentence like "Showing science fiction or drama films from the 1990s, rated 7 or higher, most popular first." You also see the film posters. The web address shows your chosen filters, such as `genres=878,18`. | |
| 5 | Click **Next**. Then click your browser's Back button. | After you click **Next**, you see "Page 2 of …". After you click Back, you return to page 1. You still see the same filters and the same sentence. | |
| 6 | Click **Clear filters**. | You see the sentence "Showing films of any genre, most popular first." The web address ends with `/discover` again. | |
| 7 | Click a film poster, such as Inception. | The film page opens. It shows the wide background image, the poster, the title, and the year. It shows the running time (2 h 28 min for Inception). It shows "Rated … from … votes", the genres, **Overview**, and **Cast**. Below the title, it says "Log in to like, dislike or mark films as watched." | |
| 8 | Open http://localhost:5173/movie/999999999 in your browser. | You see "We could not find that film." and a **Browse films** button. | |
| 9 | Open http://localhost:5173/no-such-page in your browser. | You see "Page not found" and a **Go to the home page** link. | |
| 10 | Open http://localhost:5173/me/library in your browser. | The app sends you to the **Log in** page. | |
| 11 | Log in with the email `ava@example.com` and a wrong password. | You see the message "Invalid email or password". | |
| 12 | Log in again with the password `demo-password`. | The app sends you back to the library page. You see **Ava** in the top bar. The tabs on the page say **Liked 3**, **Disliked 1**, and **Watched 2**. | |
| 13 | Click **Log out**. | You return to the home page. The top bar shows **Log in** and **Sign up**. There is no **For you** row on the page. | |
| 14 | Click **Sign up**. Leave every box empty and click **Create account**. | You see four messages: "Enter your name.", "Enter an email address like name@example.com.", "Use at least 8 characters.", and "Choose at least 3 genres." | |
| 15 | Type a name, the email `ava@example.com`, and a password with 8 or more characters. Pick 3 genres. Click **Create account**. | You see "That email already has an account." and a **Log in instead** link. | |
| 16 | Change the email to your new test email. Click **Create account**. | The home page opens with your name in the top bar. A **For you** section shows 6 posters above **Popular now**. This can take a few seconds the first time. | |
| 17 | Open a film page and click **Like**. Then refresh the browser page. | The button changes to **Liked**. It still says **Liked** after you refresh the page. | |
| 18 | Click **Mark as watched**. | You see the words "You last watched it on" with today's date. The button now says **Watched it again**. | |
| 19 | Open **Library** and look at the tabs. Click **Remove** under the film you liked. Then refresh the page. | At first, the tabs say **Liked 1** and **Watched 1**. After you click **Remove** and refresh the page, the tab says **Liked 0**. The page also says "Nothing liked yet." | |
| 20 | Open **For you** and write down the first 3 films. Go and like 3 films from a genre you did not pick when you signed up (such as Toy Story, Finding Nemo, and Up). Open **For you** again. | You see a different list of films. The notes on the films name the ones you liked, such as "Because you liked Up". | |
| 21 | Click the browser's address bar. Then press the Tab key on your keyboard again and again. | **Skip to content** shows up first. Next, a gold ring appears around each link, button, and text box as you reach it. | |
| 22 | Make your browser window 375 px wide (you can use the phone view in your browser's developer tools). Open the Home page, the Discover page, a film page, and the Library page. | None of the pages scroll from side to side. | |
| 23 | Stop the backend server (press Ctrl+C in its command window). Then refresh the Discover page. | You see "CineMatch cannot reach its server. Check that it is running, then try again." and a **Try again** button. The top bar might show **Log in** while the server is stopped. | |
| 24 | Start the backend server again. Click **Try again**, and then refresh the page. | The films show up again. You are still logged in. | |

## After you finish

1. Delete your test account. Open a command window in the main project folder (the
   repository root) and run this command with your test email:
   `docker exec cinematch-db psql -U cinematch -d cinematch -c "DELETE FROM users WHERE email = 'tester-1@example.com'"`
2. Reset the demo users. Go to the `backend/` folder and run `python -m
   scripts.seed_data`.

## Not covered yet

Add tests for these features when their steps are finished and added to the project:

- The Preferences page (step 51)
- The language switch (step 52)
- The offline demo with Wi-Fi off (step 53)
