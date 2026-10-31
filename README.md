# Women in INK

The site at womeninink.com: a map of women owned tattoo shops (Northeast US and UK), made by InINK.

## How it's built
- `build.py` reads shop records from the InINK HQ prospect database (exported to `hq/prospects`, not committed) and writes the finished site into `site/`.
- `templates/` holds the page templates and styles.
- `site/` is what Netlify publishes (see `netlify.toml`). There is no build step on Netlify.

## Update the site
1. Export the HQ `prospects` collection to `hq/prospects`.
2. Run `python3 build.py` (needs Jinja2).
3. Commit and push. Netlify deploys `site/` on its own.

`tools/` has the helper that makes a preview copy for claude.ai.
