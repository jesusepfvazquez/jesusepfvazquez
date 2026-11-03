# Hand-Made Simulations: bookdown source (handoff notes)

Notes for the person or Claude agent who compiles this book into the website. Read this file first.

## What this is

A bookdown book (gitbook style, like https://stefvanbuuren.name/fimd/) by Jesus E. Vazquez on teaching statistics with physical activities plus computer simulation. Chapter 1 of the project is the pebble-jar capture-recapture activity (binomial distribution), first taught at the University of Maryland on Oct 28, 2026. Future activities become new modules with the same structure.

## Files

| File | Content |
|---|---|
| `index.Rmd` | Title, author, preface. Holds the YAML (`site: bookdown::bookdown_site`). |
| `01-idea.Rmd` | The idea, learning goals, five-step chapter structure. |
| `02-binomial.Rmd` | Binomial basics on a clinic flu-testing example. |
| `03-jar.Rmd` | Materials, protocol, binomial mapping, Lincoln-Petersen and Chapman estimators. |
| `04-simulating.Rmd` | R simulation of the jar (N = 126, M = 21, n = 21 and 60). |
| `05-home.Rmd` | 28 real home runs and the comparison with the simulation. |
| `06-clinics.Rmd` | HD application: two clinic lists, four failure scenarios, Mexico migration. |
| `07-teaching.Rmd` | Instructor notes: timing, classroom lessons, Q&A, future chapters. |
| `08-appendix.Rmd` | Home data (the 28 runs, same as `jar-runs.csv`). |
| `_bookdown.yml` | Chapter order (`rmd_files`) and output file name. |
| `_output.yml` | gitbook settings; uses `style.css`. |
| `style.css` | Small style additions (`.callout` box, responsive `.video` box). |
| `publish.R` | Clean build, then copy `_book/` to `../site/teaching/handmade-simulations/`. |
| `_module-template.Rmd` | Starting file for a new chapter; the build ignores the file. |
| `images/` | All figures (PNG/JPG), pre-rendered. |
| `jar-runs.csv` | Home data: 28 runs, n = pebbles + cubes in the circle. |

## How to build and publish

```r
install.packages("bookdown")
bookdown::render_book("index.Rmd")   # preview only; output goes to _book/
source("publish.R")                  # clean build, then copy to ../site/teaching/handmade-simulations/
```

After `publish.R`, commit the changed files under `site/teaching/handmade-simulations/`. The `_book/` folder is not committed. The script deletes `_book/` first, so pages from removed chapters do not linger.

## Conventions to keep

- Every code chunk is `eval = FALSE`: the numbers in the text were computed once with `set.seed(2026)` and 1,000 repetitions. If you switch chunks to `eval = TRUE`, check that the printed numbers still match the prose (jar median 147, middle 90% 74 to 441; n = 60 middle 90% 84 to 210; home median 147, pooled 155, Chapman 115; clinic medians 181, 100, 150, 340).
- Figures are static images in `images/`. The scripts that made them are in the UMD teaching-demo folder (`jar-figures.R`, `home-vs-sim.py`, `clinic-scenarios.py`); an option is to replace the images with R chunks that draw them.
- Writing style: plain, direct prose; no em-dashes; name the thing instead of writing "this" or "it"; refer to estimators as "the Lincoln-Petersen estimator", "the Chapman estimator". Use association language, not causal language.
- HD clinic numbers are illustrative and labeled as such.
- `images/migration-toy.png` comes from the `toy-flow` chunk in `06-clinics.Rmd` (invented counts, base R). Wrap the chunk in `png("images/migration-toy.png", width = 1800, height = 1000, res = 200, type = "cairo")` and `dev.off()` to redraw. The real-cohort figure `images/migration-chord.png` is static.

## Adding a new module (activity)

1. Copy `_module-template.Rmd` to `NN-short-name.Rmd`. The template holds the five steps: the physical activity (materials, protocol), the model, the real data, the computer simulation, and the gap between real and simulated, plus a short student task.
2. Put images in `images/` and data next to the Rmd files.
3. Add the file to `rmd_files` in `_bookdown.yml`, before `07-teaching.Rmd`. A chapter joins the book only when listed there, so unfinished files can sit in this folder without being published.
4. Run `source("publish.R")` and look at the preview before committing.

## Planned modules

Starting points, to be edited as the chapters take shape.

| Module | Possible hook | Builds on |
|---|---|---|
| Weighting | Cubes and pebbles have different chances of landing in the circle; estimate the ratio of the chances and weight each object by the inverse of its chance. | The home runs in Chapter 5: cubes were 14% of the circle and 17% of the jar. |
| Hypergeometric | The jar is drawn without replacement; compare exact hypergeometric probabilities with the binomial as the second toss grows relative to the jar. | Question 1 in Chapter 7. |
| Poisson | Count rare events per toss and compare Poisson and binomial probabilities. | The binomial chapters (2 and 3). |
| Student redesign | Students change the protocol (mixing, toss height, circle size), predict the direction of the error, then test with data and simulation. | The scenario table in Chapter 6. |
| Selection bias | Students pick which objects to mark or count by a rule, then watch the estimate move. | The hard-to-reach group in Chapter 6. |

Other candidates: sampling distributions (drawing from a bag), regression to the mean, confidence-interval coverage, permutation tests (shuffling cards), and missing data (hiding cards by a rule).

## Preview

`../hand-made-simulations.html` is a single-file preview built with pandoc (no R). The bookdown build replaces it.
