
for vid, spec in dossiers.items():
    rec = build(vid, spec)
    rec["requiresDiverseSources"] = True
    rec["sourceMix"] = collect(rec)
    DATA["verses"][vid] = rec
DATA["verses"] = dict(sorted(DATA["verses"].items(), key=lambda kv: tuple(int(x) if x.isdigit() else 0 for x in kv[0].split(':'))))
PATH.write_text(json.dumps(DATA, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("records:", len(DATA["verses"]))
