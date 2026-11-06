# Women in INK

The site at womeninink.com: a map of women owned tattoo shops (US and UK), made by InINK.

## How it's built
- `data/shops.json` holds the public map fields for every shop. A shop shows when its `status` is `live`.
- `build.py` reads that file and writes the finished site into `site/`.
- `templates/` holds the page templates and styles.
- `site/` is what Netlify publishes (see `netlify.toml`). There is no build step on Netlify.

## Update the site
1. Edit `data/shops.json` (the weekly sweep keeps it in step with the HQ prospect records).
2. Run `python3 build.py` (needs Jinja2).
3. Commit and push. Netlify deploys `site/` on its own.

`tools/` has the helper that makes a preview copy for claude.ai.
