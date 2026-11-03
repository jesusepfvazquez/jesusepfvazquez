# Build the book from a clean folder and publish the result to the website.
# Run from the handmade-sims/ folder:  source("publish.R")
# Then commit the changed files under ../site/teaching/handmade-simulations/.
# The _book/ folder stays out of git; the copy under site/ is what Netlify serves.

unlink("_book", recursive = TRUE)              # remove pages from deleted chapters
bookdown::render_book("index.Rmd")

dest <- file.path("..", "site", "teaching", "handmade-simulations")
unlink(dest, recursive = TRUE)
dir.create(dest, recursive = TRUE)
file.copy(list.files("_book", full.names = TRUE), dest, recursive = TRUE)
message("Published ", length(list.files(dest, recursive = TRUE)), " files to ", normalizePath(dest))
