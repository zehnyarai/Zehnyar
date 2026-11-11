
for vid, spec in dossiers.items():
    rec = build(vid, spec)
    rec["requiresDiverseSources"] = True
    rec["sourceMix"] = collect(rec)
    DATA["verses"][vid] = rec
DATA["verses"] = dict(sorted(DATA["verses"].items(), key=lambda kv: tuple(int(x) if x.isdigit() else 0 for x in kv[0].split(':'))))
_main = dict(DATA); _part = {"verses": {k: v for k, v in DATA["verses"].items() if int(k.split(":")[0]) >= 30}}
_main["verses"] = {k: v for k, v in DATA["verses"].items() if int(k.split(":")[0]) < 30}
PATH.write_text(json.dumps(_main, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
PATH2.write_text(json.dumps(_part, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
print("records:", len(DATA["verses"]))
