#!/usr/bin/env python3
"""Render LeetCode card matching the profile banner theme. Dark + light SVGs."""
import json, sys, os, math, html, datetime

W, H = 1180, 300
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

THEMES = {
 "dark":  dict(BG="#0D1117", PANEL="#0A101F", STROKE="rgba(34,211,238,0.28)",
               CYAN="#22D3EE", VIOLET="#A78BFA", VIOLET2="#7C3AED", EMERALD="#10B981",
               TEXT="#F8FAFC", MUTED="#94A3B8", DIM="#475569", BARBG="rgba(148,163,184,0.16)",
               CELL0="#161B22"),
 "light": dict(BG="#FFFFFF", PANEL="#F8FAFC", STROKE="rgba(8,145,178,0.30)",
               CYAN="#0891B2", VIOLET="#7C3AED", VIOLET2="#5B21B6", EMERALD="#059669",
               TEXT="#0F172A", MUTED="#475569", DIM="#94A3B8", BARBG="rgba(100,116,139,0.18)",
               CELL0="#E9EDF2"),
}

def esc(s): return html.escape(str(s), quote=True)

def mix(hex_a, hex_b, t):
    a = tuple(int(hex_a[i:i+2], 16) for i in (1, 3, 5))
    b = tuple(int(hex_b[i:i+2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))

def build(d, theme):
    T = THEMES[theme]
    s = []; a = s.append
    a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
      f'font-family="{FONT}" role="img" aria-label="LeetCode stats">')
    a(f'<defs><linearGradient id="acc{theme}" x1="0" y1="0" x2="1" y2="0">'
      f'<stop offset="0" stop-color="{T["VIOLET2"]}"><animate attributeName="stop-color" '
      f'values="{T["VIOLET2"]};{T["CYAN"]};{T["EMERALD"]};{T["VIOLET2"]}" dur="10s" repeatCount="indefinite"/></stop>'
      f'<stop offset="1" stop-color="{T["EMERALD"]}"><animate attributeName="stop-color" '
      f'values="{T["EMERALD"]};{T["VIOLET2"]};{T["CYAN"]};{T["EMERALD"]}" dur="10s" repeatCount="indefinite"/></stop>'
      f'</linearGradient></defs>')
    a(f'<rect width="{W}" height="{H}" fill="{T["BG"]}"/>')

    # header — same language as PROJECTS.LIST
    a(f'<text x="6" y="18" font-size="11" letter-spacing="2" fill="{T["CYAN"]}">LEETCODE.STATS</text>')
    a(f'<text x="136" y="18" font-size="10" fill="{T["DIM"]}">./solve.sh --summary</text>')
    rank = d.get("ranking")
    if rank:
        a(f'<text x="{W-6}" y="18" text-anchor="end" font-size="10" fill="{T["DIM"]}">'
          f'rank <tspan fill="{T["TEXT"]}">#{rank:,}</tspan></text>')
    a(f'<line x1="0" y1="28" x2="{W}" y2="28" stroke="url(#acc{theme})" stroke-width="1.5" opacity="0.7"/>')

    sv, tt = d["solved"], d["totals"]
    total_all = tt.get("All") or 1

    # left: big number + difficulty bars
    a(f'<text x="6" y="86" font-size="44" font-weight="700" fill="{T["TEXT"]}">{sv.get("All",0)}</text>')
    a(f'<text x="6" y="106" font-size="11" letter-spacing="1" fill="{T["MUTED"]}">PROBLEMS SOLVED</text>')
    a(f'<text x="6" y="126" font-size="10" fill="{T["DIM"]}">of {total_all:,} total</text>')

    bx, bw = 210, 300
    rows = [("Easy", T["EMERALD"]), ("Medium", T["CYAN"]), ("Hard", T["VIOLET"])]
    for i, (name, col) in enumerate(rows):
        y = 60 + i*30
        got, tot = sv.get(name, 0), tt.get(name, 0) or 1
        frac = min(got/tot, 1.0)
        a(f'<text x="{bx}" y="{y+4}" font-size="12" fill="{T["MUTED"]}">{name}</text>')
        a(f'<rect x="{bx+68}" y="{y-7}" width="{bw}" height="9" rx="4.5" fill="{T["BARBG"]}"/>')
        a(f'<rect x="{bx+68}" y="{y-7}" width="0" height="9" rx="4.5" fill="{col}">'
          f'<animate attributeName="width" from="0" to="{bw*frac:.1f}" dur="1.1s" '
          f'begin="{0.2+i*0.15:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.16 1 0.3 1"/></rect>')
        a(f'<text x="{bx+68+bw+12}" y="{y+4}" font-size="12" fill="{T["TEXT"]}">{got}'
          f'<tspan fill="{T["DIM"]}">/{tot}</tspan></text>')

    # streak + active days
    a(f'<text x="6" y="168" font-size="12" fill="{T["MUTED"]}">Max streak '
      f'<tspan fill="{T["TEXT"]}" font-weight="700">{d.get("streak",0)}</tspan>'
      f'<tspan fill="{T["DIM"]}" dx="16">Active days </tspan>'
      f'<tspan fill="{T["TEXT"]}" font-weight="700">{d.get("active_days",0)}</tspan></text>')

    # heatmap — 53 weeks
    cal = {int(k): v for k, v in d.get("calendar", {}).items()}
    today = datetime.datetime.now(datetime.timezone.utc).date()
    start = today - datetime.timedelta(days=364)
    start -= datetime.timedelta(days=(start.weekday()+1) % 7)   # back to Sunday
    by_day = {}
    for ts, n in cal.items():
        day = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).date()
        by_day[day] = by_day.get(day, 0) + n
    peak = max(by_day.values()) if by_day else 1
    CS, GAP = 15, 4
    hx, hy = 6, 196
    a(f'<text x="{hx}" y="{hy-8}" font-size="10" letter-spacing="2" fill="{T["DIM"]}">LAST 52 WEEKS</text>')
    weeks = 53
    for w in range(weeks):
        for dow in range(7):
            day = start + datetime.timedelta(days=w*7+dow)
            if day > today: continue
            n = by_day.get(day, 0)
            if n <= 0:
                fill = T["CELL0"]
            else:
                t = min(math.log1p(n)/math.log1p(peak), 1.0)
                fill = mix(T["VIOLET2"], T["CYAN"], t) if t > 0.5 else mix(T["CELL0"], T["VIOLET2"], t*2)
            x = hx + w*(CS+GAP); y = hy + dow*(CS+GAP)
            op = '' if n <= 0 else (f'<animate attributeName="opacity" values="0;1" dur="0.4s" '
                                    f'begin="{0.4 + w*0.012:.2f}s" fill="freeze"/>')
            init = '' if n <= 0 else ' opacity="0"'
            a(f'<rect x="{x}" y="{y}" width="{CS}" height="{CS}" rx="3" fill="{fill}"{init}>{op}</rect>')
    a('</svg>')
    return "".join(s)

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "leetcode.json"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(outdir, exist_ok=True)
    d = json.load(open(src))
    for theme, name in (("dark", "leetcode-dark.svg"), ("light", "leetcode-light.svg")):
        p = os.path.join(outdir, name)
        open(p, "w").write(build(d, theme))
        print("wrote", p)
