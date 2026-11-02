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
| `style.css` | Small style additions (`.callout` box). |
| `images/` | All figures (PNG/JPG), pre-rendered. |
| `jar-runs.csv` | Home data: 28 runs, n = pebbles + cubes in the circle. |

## How to build

```r
install.packages("bookdown")
bookdown::render_book("index.Rmd")   # output goes to _book/
```

Then copy `_book/` into the website folder (for example `talks/handmade-simulations/`) or point the site's build at this folder.

## Conventions to keep

- Every code chunk is `eval = FALSE`: the numbers in the text were computed once with `set.seed(2026)` and 1,000 repetitions. If you switch chunks to `eval = TRUE`, check that the printed numbers still match the prose (jar median 147, middle 90% 74 to 441; n = 60 middle 90% 84 to 210; home median 147, pooled 155, Chapman 115; clinic medians 181, 100, 150, 340).
- Figures are static images in `images/`. The scripts that made them are in the UMD teaching-demo folder (`jar-figures.R`, `home-vs-sim.py`, `clinic-scenarios.py`); an option is to replace the images with R chunks that draw them.
- Writing style: plain, direct prose; no em-dashes; name the thing instead of writing "this" or "it"; refer to estimators as "the Lincoln-Petersen estimator", "the Chapman estimator". Use association language, not causal language.
- HD clinic numbers are illustrative and labeled as such.
- `images/migration-toy.png` comes from the `toy-flow` chunk in `06-clinics.Rmd` (invented counts, base R). Wrap the chunk in `png("images/migration-toy.png", width = 1800, height = 1000, res = 200, type = "cairo")` and `dev.off()` to redraw. The real-cohort figure `images/migration-chord.png` is static.

## Adding a new module (activity)

1. Create `NN-short-name.Rmd` starting with `# Title {#label}`.
2. Follow the five steps: the physical activity (materials, protocol), the model, the real data, the computer simulation, the gap between real and simulated.
3. Put images in `images/` and data next to the Rmd files.
4. Add the file to `rmd_files` in `_bookdown.yml`, before `08-appendix.Rmd`.

Candidate modules: sampling distributions (drawing from a bag), regression to the mean, confidence-interval coverage, permutation tests (shuffling cards), missing data (hiding cards by a rule).

## Preview

`../hand-made-simulations.html` is a single-file preview built with pandoc (no R). The bookdown build replaces it.
