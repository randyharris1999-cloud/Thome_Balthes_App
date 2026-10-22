"""Trim data/people.json to the people the Thomä & Balthes app shows.

Run after every build, from the website folder:   python tools/trim_people.py
Safe to run more than once.

In scope (RG): the people the app has pages for. Everyone else in the file is
only there so their name can appear on an in-scope person's page (a child,
a spouse, a parent). For those "named only" people this keeps the name, the
family number and the links the app needs, cuts dates to the year (all the app
ever shows for them), and drops links to their own, out-of-scope relatives.
Empty slots keep their position (the app uses positions as ids) but lose their
family-book number, and Street View links for out-of-scope people are removed.
"""
import json, re, sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'data/people.json')
d = json.loads(path.read_text(encoding='utf-8'))
P, IDS = d['P'], d['IDS']
RG = set(d['RG'][0]) | set(d['RG'][1])
year = lambda s: (re.search(r'\d{4}', s or '') or [''])[0]

# who an in-scope page can mention
fams = {P[i][6] for i in RG if P[i][6]}
keep = set(RG)
for i in RG:
    keep.update(j for j in P[i][4:6] if j >= 0)
for i, p in enumerate(P):
    if p[0] and (p[4] in RG or p[5] in RG or p[6] in fams):
        keep.add(i)

n_dates = n_links = n_blank = 0
for i, p in enumerate(P):
    if i in RG:
        continue
    if i not in keep:
        if p[0] or IDS[i]:
            n_blank += 1
        P[i] = ['', '', '', '', -1, -1, '', '']
        IDS[i] = ''
        continue
    for k in (2, 3):
        y = year(p[k])
        if p[k] != y:
            p[k] = y; n_dates += 1
    a, b = p[4], p[5]
    # keep a parent link only if it shows on an in-scope page:
    # the parent is in scope, or the other parent is (the child is then listed under that couple)
    if a >= 0 and not (a in RG or b in RG):
        p[4] = -1; n_links += 1
    if b >= 0 and not (b in RG or a in RG):
        p[5] = -1; n_links += 1

sv = d.get('SV', {})
n_sv = len(sv)
d['SV'] = {k: v for k, v in sv.items() if int(k) in RG}

path.write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
print(f'{len(RG)} in scope, {len(keep) - len(RG)} named only; '
      f'{n_dates} dates cut to the year, {n_links} outside links dropped, '
      f'{n_blank} people/ids blanked, {n_sv - len(d["SV"])} Street View links removed')
