import re, pathlib
SITE = pathlib.Path('/home/claude/wii/site'); OUT = pathlib.Path('/home/claude/wii/preview'); OUT.mkdir(exist_ok=True)
BAR = '<div class="pv-bar">Preview of womeninink.com. Forms don\'t send from here, and the real site has a full street map. Both work once it\'s on Netlify.</div>\n'
CSS = '#map { position: relative; } #map canvas { display: block; } .pv-note { position: absolute; left: 10px; bottom: 6px; margin: 0; font-size: 12px; background: rgba(247,242,236,.9); padding: 2px 8px; border-radius: 4px; }\n.pv-bar { background: #443473; color: #F7F2EC; font-size: 14px; padding: 8px max(16px, env(safe-area-inset-left, 0px)); text-align: center; }\n'
CANVAS = open('/home/claude/wii/preview_canvas.js').read()
def links(t):
    t = re.sub(r'href="/#', 'href="index.html#', t)
    t = t.replace('href="/"', 'href="index.html"')
    t = re.sub(r'href="/(uk|about|flash-days)\.html', r'href="\1.html', t)
    return t
def page(name, main=False, title=None):
    t = (SITE / name).read_text()
    t = re.sub(r'<link href="https://unpkg.com/maplibre[^>]*>\n?', '', t)
    t = re.sub(r'<script src="https://unpkg.com/maplibre[^>]*></script>\n?', '', t)
    if 'new maplibregl.Map(' in t:
        s = t.index('try {\n  map = new maplibregl.Map(')
        e = t.index('}\n', t.index('The map could not load')) + 2
        t = t[:s] + CANVAS + t[e:]
    t = t.replace('</style>', CSS + '</style>', 1)
    t = t.replace('<div class="wrap">', BAR + '<div class="wrap">', 1)
    t = links(t)
    if main:
        t = re.sub(r'<!doctype html>\s*<html[^>]*>\s*<head>\s*', '', t, flags=re.I)
        t = t.replace('</head>', '').replace('</html>', '')
        t = re.sub(r'<body[^>]*>', '', t).replace('</body>', '')
        t = t.replace('<meta charset="utf-8">', '').replace('<meta name="viewport" content="width=device-width, initial-scale=1">', '')
        t = re.sub(r'<title>[^<]*</title>', '<title>Women in INK</title>', t, count=1)
    (OUT / name.replace('index.html', 'women-in-ink.html')).write_text(t)
page('index.html', main=True)
for n in ['uk.html', 'about.html', 'flash-days.html']:
    page(n)
print('ok')
