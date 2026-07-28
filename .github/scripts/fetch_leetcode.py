#!/usr/bin/env python3
"""Fetch LeetCode stats + 52-week calendar. Writes leetcode.json."""
import json, os, sys, urllib.request, datetime

USER = os.environ.get("LEETCODE_USER", "Sainathek")
URL = "https://leetcode.com/graphql"

Q = """
query($u: String!, $y: Int) {
  matchedUser(username: $u) {
    username
    profile { ranking }
    submitStatsGlobal { acSubmissionNum { difficulty count } }
    userCalendar(year: $y) { submissionCalendar streak totalActiveDays }
  }
  allQuestionsCount { difficulty count }
}
"""

def gql(variables):
    body = json.dumps({"query": Q, "variables": variables}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/json",
        "Referer": f"https://leetcode.com/u/{USER}/",
        "User-Agent": "Mozilla/5.0 (compatible; profile-card/1.0)",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    cal = {}
    solved = {"Easy": 0, "Medium": 0, "Hard": 0, "All": 0}
    totals = {"Easy": 0, "Medium": 0, "Hard": 0, "All": 0}
    ranking = None; streak = 0; active_days = 0
    for year in (now.year - 1, now.year):
        try:
            d = gql({"u": USER, "y": year})["data"]
        except Exception as e:
            print(f"warn: year {year} fetch failed: {e}", file=sys.stderr)
            continue
        mu = d.get("matchedUser")
        if not mu:
            print("error: user not found", file=sys.stderr); break
        for row in mu["submitStatsGlobal"]["acSubmissionNum"]:
            solved[row["difficulty"]] = row["count"]
        for row in d.get("allQuestionsCount") or []:
            totals[row["difficulty"]] = row["count"]
        ranking = (mu.get("profile") or {}).get("ranking")
        uc = mu.get("userCalendar") or {}
        streak = max(streak, uc.get("streak") or 0)
        active_days += uc.get("totalActiveDays") or 0
        raw = uc.get("submissionCalendar")
        if raw:
            for ts, n in json.loads(raw).items():
                cal[int(ts)] = cal.get(int(ts), 0) + int(n)

    out = {"user": USER, "solved": solved, "totals": totals, "ranking": ranking,
           "streak": streak, "active_days": active_days,
           "calendar": {str(k): v for k, v in cal.items()},
           "generated": now.isoformat()}
    with open("leetcode.json", "w") as f:
        json.dump(out, f)
    print(f"solved {solved}  ranking {ranking}  streak {streak}  days {len(cal)}")

if __name__ == "__main__":
    main()
