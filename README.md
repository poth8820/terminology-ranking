# Country ranking for the plant-microbiome vocabulary survey

Every hour, GitHub runs `update_leaderboard.py`. It reads the survey's public statistics page on
LimeSurvey (only the country question is published there), draws the ranking and writes a
thank-you page with the chart into `docs/`. LimeSurvey sends participants to that page when they
submit the survey. Nothing has to be done by hand once it is set up.

## Setup (about 15 minutes, once)

1. **Pick the address.** Create a GitHub account if needed, and a new public repository named
   `terminology-ranking`. The page will live at
   `https://<account>.github.io/terminology-ranking/`.
2. **Upload the files** of this folder (Add file > Upload files). If the hidden folder `.github`
   does not come along, use Add file > Create new file, type the name
   `.github/workflows/leaderboard.yml`, and paste the content of that file.
3. **Tell it where the survey is.** Settings > Secrets and variables > Actions > Variables tab >
   New repository variable:
   - `LIMESURVEY` = `https://limesurvey.zhaw.ch`
   - `SURVEY_ID` = the survey ID LimeSurvey shows after import
4. **Allow it to save the page.** Settings > Actions > General > Workflow permissions >
   "Read and write permissions".
5. **First run.** The survey must be imported and activated first. Then Actions tab >
   "Update country ranking" > Run workflow. After a minute, `docs/` holds `index.html`,
   `leaderboard.png` and `leaderboard.json`.
6. **Publish the page.** Settings > Pages > Build and deployment > Deploy from a branch >
   branch `main`, folder `/docs` > Save. The page appears at the address from step 1 within
   a few minutes.
7. **Point the survey at it.** In `build_survey.py`, set `RANKING_PAGE_URL` to that address and
   rebuild; or, in LimeSurvey, Survey settings > Text elements > End URL.

## Good to know

- The ranking counts participants per country, including people who have started but not
  finished: that is what LimeSurvey's public statistics provide.
- Countries with fewer than 3 participants are left out of the chart (`MIN_PARTICIPANTS`).
  `TOP_N = 5` shows only the top five.
- The statistics page itself is not linked anywhere, but anyone who knows its address can open
  it, and it lists every country, including those with one participant.
- If the first run fails with a connection error, the ZHAW server refuses requests from outside;
  the same script can then run on any ZHAW machine with a scheduler and a place to publish
  `docs/`.
- GitHub pauses hourly jobs in a public repository after 60 days without any change to it. The
  job saves the page whenever the ranking changes, so this only matters after a long quiet spell:
  the Actions tab then offers to switch it back on.
