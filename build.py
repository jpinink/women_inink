"""Build the Women in INK static site from data/listings.json into site/."""
import json, re, math, datetime, pathlib, collections
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "site"
import os
HQ_DIR = pathlib.Path(os.environ.get("HQ_DIR", str(ROOT / "hq" / "prospects")))
STATES = [("CT", "Connecticut"), ("ME", "Maine"), ("MA", "Massachusetts"),
          ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NY", "New York"),
          ("RI", "Rhode Island"), ("VT", "Vermont"),
          ("ENG", "England"), ("SCT", "Scotland"), ("WLS", "Wales"), ("NIR", "Northern Ireland")]
UK_CODES = {"ENG", "SCT", "WLS", "NIR"}
REGIONS = [
    {"key": "us", "tab": "Northeast US", "href": "/", "path": "/", "file": "index.html", "lang": "en",
     "title": "Women Owned Tattoo Shops in the Northeast | Women in INK",
     "h1": "Women owned tattoo shops in the Northeast",
     "lede": "Find a women owned tattoo shop near you in New England, New York and New Jersey. See their work, catch their flash days and book your next tattoo.",
     "area_long": "the Northeast (New England, New York and New Jersey)",
     "filter_label": "Filter by state", "unit": "state", "town_label": "Town and state", "town_eg": "Portland, ME",
     "bounds": "[[-79.8, 38.9], [-66.9, 47.5]]", "country": "US"},
    {"key": "uk", "tab": "UK", "href": "/uk.html", "path": "/uk.html", "file": "uk.html", "lang": "en-GB",
     "title": "Women Owned Tattoo Shops in the UK | Women in INK",
     "h1": "Women owned tattoo shops in the UK",
     "lede": "Find a women owned tattoo shop near you in England, Scotland, Wales and Northern Ireland. See their work, catch their flash days and book your next tattoo.",
     "area_long": "the UK (England, Scotland, Wales and Northern Ireland)",
     "filter_label": "Filter by country", "unit": "country", "town_label": "Town or city", "town_eg": "Leeds",
     "bounds": "[[-8.3, 49.9], [1.9, 58.8]]", "country": "UK"},
]
SOURCE_LABEL = {"website": "website", "press": "interview", "directory": "listing page",
                "linktree": "link page", "instagram": "Instagram", "yelp": "Yelp listing", "inink": "InINK page", "google": "Google listing"}
BOOKING_TEXT = {"dm": "Books by DM", "form": "Books by form",
                "phone": "Books by phone", "email": "Books by email",
                "walk ins": "Walk ins welcome", "online": "Books online"}
# consumer friendly tags: key, label, group, hint. Research tags (HQ) map onto these keys.
TAGS = [
    ("fine", "Delicate lines", "look", "Thin, soft linework. Light and subtle."),
    ("bold", "Bold black", "look", "Solid black ink and strong shapes."),
    ("color", "Full color", "look", "Bright, saturated color."),
    ("bng", "Black and grey shading", "look", "Soft shading in black and grey, no color."),
    ("water", "Watercolor look", "look", "Soft color that looks painted on."),
    ("classic", "Classic old school", "style", "Bold outlines, bright colors: roses, swallows, daggers."),
    ("modern", "Modern old school", "style", "Old school with more detail, depth and color."),
    ("photo", "Looks like a photo", "style", "Realistic portraits, animals and objects."),
    ("drawn", "Drawn, like an illustration", "style", "Looks like a drawing or a storybook picture."),
    ("japanese", "Japanese style", "style", "Koi, dragons, waves and flowers in the Japanese tradition."),
    ("patterns", "Patterns and shapes", "style", "Mandalas, dots, lines and geometric designs."),
    ("tiny", "Tiny tattoos", "want", "Small, simple pieces. Great for a first tattoo."),
    ("plants", "Flowers and plants", "want", "Florals, leaves and botanical designs."),
    ("words", "Words and script", "want", "Names, dates, quotes and lettering."),
    ("cover", "Covers old tattoos", "want", "Turns an old tattoo into something new."),
    ("handpoke", "Hand poked, no machine", "want", "Done by hand, dot by dot. Quiet and gentle."),
]
TAG_FROM = {"Fine line": "fine", "Blackwork": "bold", "Color": "color", "Black and grey": "bng",
            "Watercolor": "water", "Traditional": "classic", "Neo traditional": "modern",
            "Realism": "photo", "Illustrative": "drawn", "Japanese": "japanese", "Ornamental": "patterns",
            "Geometric": "patterns", "Micro": "tiny", "Botanical": "plants", "Lettering": "words",
            "Cover ups": "cover", "Handpoke": "handpoke"}
TOP_TAGS = ["fine", "tiny", "plants", "bold", "color", "classic"]
GROUPS = [("look", "The look"), ("style", "The style"), ("want", "What you want")]
SPECIALTIES = ["Fine line", "Blackwork", "Black and grey", "Color", "Traditional", "Neo traditional",
               "Realism", "Illustrative", "Japanese", "Watercolor", "Botanical", "Lettering",
               "Ornamental", "Geometric", "Micro", "Handpoke", "Cover ups"]


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def fmt_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime("%b %-d, %Y")


HOW_TO_BOOK = {"walk in": "Walk in on the day", "dm": "DM them to claim a piece",
               "form": "Sign up through their form", "inink": "Book a piece on InINK",
               "link": "Book through their link", "email": "Email them to book",
               "phone": "Call or text to book"}


def fd_label(iso_start, iso_end=""):
    d = datetime.date.fromisoformat(iso_start)
    s = d.strftime("%a %b %-d")
    if iso_end and iso_end != iso_start:
        e = datetime.date.fromisoformat(iso_end)
        s += " to " + (e.strftime("%-d") if e.month == d.month else e.strftime("%b %-d"))
    return s


def prep_flash_days(s, today):
    out = []
    for f in s.get("flash_days", []) or []:
        end = f.get("end_date") or f["date"]
        if end < today.isoformat():
            continue
        g = dict(f)
        g["end"] = end
        g["label"] = fd_label(f["date"], f.get("end_date", ""))
        g["how"] = HOW_TO_BOOK.get((f.get("how_to_book") or "").lower(), f.get("how_to_book", ""))
        if (f.get("how_to_book") or "").lower() == "inink" and not g.get("book_url"):
            g["book_url"] = s.get("inink_url", "")
        out.append(g)
    out.sort(key=lambda g: g["date"])
    return out


def booking_text(raw):
    r = (raw or "").lower().strip()
    if not r or r == "unknown":
        return ""
    for k, v in BOOKING_TEXT.items():
        if r.startswith(k):
            return v
    return "Books online" if "online" in r else ""


TODAY = datetime.date.today()


def main():
    # The one source of truth is the HQ prospect database (collection "prospects").
    # Export it first (ArtifactData list with out_dir), then point HQ_DIR at that folder.
    shops = []
    for f in sorted(HQ_DIR.glob("*.json")):
        for rec in json.loads(f.read_text()).get("records", {}).values():
            m = rec.get("map")
            if not m or m.get("status") != "live":
                continue
            s = dict(m)
            s["shop_name"] = m["name"]
            s["flash_days"] = rec.get("flash_days", []) or []
            shops.append(s)
    # spread pins that share a town so they don't sit on top of each other
    by_town = collections.defaultdict(list)
    for s in shops:
        by_town[(s["city"], s["state"])].append(s)
    for group in by_town.values():
        if len(group) > 1:
            for i, s in enumerate(group):
                ang = 2 * math.pi * i / len(group)
                s["lat"] += 0.006 * math.sin(ang)
                s["lng"] += 0.008 * math.cos(ang)
    seen = set()
    for s in shops:
        slug = slugify(s["shop_name"] + "-" + s["city"])
        while slug in seen:
            slug += "-2"
        seen.add(slug)
        s["slug"] = slug
        s["source_label"] = SOURCE_LABEL.get(s.get("source_type", "website"), "website")
        s["checked"] = fmt_date(s["checked_on"])
        tl = ["Women owned", booking_text(s.get("booking_method"))]
        if s.get("books_flash") == "yes":
            tl.append("Has flash")
        s["tagline_rest"] = [t for t in tl[1:] if t]
        keys = {TAG_FROM[x] for x in (s.get("specialties") or []) if x in TAG_FROM}
        s["tags"] = [{"key": k, "label": l, "hint": h} for k, l, g, h in TAGS if k in keys]
        s["specialties"] = [t["label"] for t in s["tags"]]
        s["spec_keys"] = " ".join(t["key"] for t in s["tags"])
        s["search_text"] = " ".join([s["shop_name"], s["city"], s["state"], s.get("place_region", "")] + s["specialties"]).lower()
        s.setdefault("instagram_url", "")
        s.setdefault("website", "")
        s.setdefault("inink_url", "")
        s.setdefault("mom_owned", False)
        s.setdefault("mom_note", "")
        s["fd"] = prep_flash_days(s, TODAY)
        s["country"] = "UK" if s["state"] in UK_CODES else "US"
        s["place_region"] = dict(STATES).get(s["state"], s["state"]) if s["country"] == "UK" else s["state"]
    shops.sort(key=lambda s: (s["state"], s["city"], s["shop_name"].lower()))
    all_shops = shops

    def addr(s):
        uk = s["country"] == "UK"
        return {"@type": "PostalAddress", "addressLocality": s["city"],
                "addressRegion": s["place_region"] if uk else s["state"], "addressCountry": "GB" if uk else "US"}

    def rows_for(shops):
        week_end = (TODAY + datetime.timedelta(days=6)).isoformat()
        month_end = (TODAY + datetime.timedelta(days=45)).isoformat()
        week, upcoming = [], []
        for s in shops:
            for f in s["fd"]:
                row = {"shop": s, "f": f}
                if f["date"] <= month_end:
                    upcoming.append(row)
                if f["date"] <= week_end:
                    week.append(row)
        week.sort(key=lambda r: r["f"]["date"])
        upcoming.sort(key=lambda r: r["f"]["date"])
        return week, upcoming

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]))
    base_css = (ROOT / "templates" / "base.css").read_text()
    OUT.mkdir(exist_ok=True)
    from markupsafe import Markup
    J = lambda o: Markup(json.dumps(o, ensure_ascii=False).replace("</", "<\\/"))
    tabs = [{"key": r["key"], "tab": r["tab"], "href": r["href"]} for r in REGIONS]
    for R in REGIONS:
        shops = [s for s in all_shops if s["country"] == R["country"]]
        present = {s["state"] for s in shops}
        states = [{"code": c, "name": n} for c, n in STATES if c in present]
        items = []
        for i, s in enumerate(shops, 1):
            biz = {"@type": "TattooParlor", "name": s["shop_name"], "address": addr(s)}
            if s["website"]:
                biz["url"] = s["website"]
            if s["instagram_url"]:
                biz["sameAs"] = [s["instagram_url"]]
            items.append({"@type": "ListItem", "position": i, "item": biz})
        jsonld = {"@context": "https://schema.org", "@type": "ItemList",
                  "name": "Women owned tattoo shops in " + R["area_long"], "itemListElement": items}
        week, _ = rows_for(shops)
        public = [dict({k: s[k] for k in ("slug", "shop_name", "city", "state", "lat", "lng")},
                       region=s["place_region"], fd=[[f["date"], f["end"]] for f in s["fd"]]) for s in shops]
        (OUT / R["file"]).write_text(env.get_template("index.html").render(
            R=R, regions=tabs, shops=shops, states=states, count=len(shops), base_css=Markup(base_css),
            any_flash=any(s.get("books_flash") == "yes" for s in shops),
            any_mom=any(s["mom_owned"] for s in shops),
            any_inink=any(s["inink_url"] for s in shops),
            week=week, any_fd=any(s["fd"] for s in shops),
            tag_groups=[{"name": gn, "tags": [{"key": k, "label": l, "hint": h, "top": k in TOP_TAGS}
                          for k, l, g2, h in TAGS if g2 == g and any(k in s["spec_keys"].split() for s in shops)]}
                         for g, gn in GROUPS],
            top_tags=[{"key": k, "label": l, "hint": h} for k, l, g, h in TAGS if k in TOP_TAGS and any(k in s["spec_keys"].split() for s in shops)],
            jsonld=J(jsonld), shops_json=J(public)))
        print(R["file"], len(shops))

    week, upcoming = rows_for(all_shops)
    events = []
    for r in upcoming:
        s, f = r["shop"], r["f"]
        ev = {"@type": "Event", "name": f"{f.get('title') or 'Flash day'} at {s['shop_name']}",
              "startDate": f["date"], "endDate": f["end"],
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "location": {"@type": "Place", "name": s["shop_name"], "address": addr(s)},
              "organizer": {"@type": "Organization", "name": s["shop_name"],
                            "url": s["website"] or s["instagram_url"]}}
        if f.get("offer"):
            ev["description"] = f["offer"]
        if f.get("post_url"):
            ev["url"] = f["post_url"]
        events.append(ev)
    (OUT / "about.html").write_text(env.get_template("about.html").render(
        base_css=Markup(base_css), updated=fmt_date(datetime.date.today().isoformat())))
    (OUT / "flash-days.html").write_text(env.get_template("flash-days.html").render(
        base_css=Markup(base_css), upcoming=upcoming, week_count=len(week),
        updated=fmt_date(TODAY.isoformat()),
        jsonld=J({"@context": "https://schema.org", "@graph": events})))
    (OUT / "_redirects").write_text(
        "https://womeninink.uk/* https://womeninink.com/uk.html 301!\n"
        "https://www.womeninink.uk/* https://womeninink.com/uk.html 301!\n")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://womeninink.com/sitemap.xml\n")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "<url><loc>https://womeninink.com/</loc></url>\n<url><loc>https://womeninink.com/uk.html</loc></url>\n"
        "<url><loc>https://womeninink.com/flash-days.html</loc></url>\n"
        "<url><loc>https://womeninink.com/about.html</loc></url>\n</urlset>\n")
    shops = all_shops
    print(f"built {len(shops)} listings into {OUT}")


if __name__ == "__main__":
    main()
