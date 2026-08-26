"""Validasi recon/*.json terhadap docs/SCHEMA.md 1 + DoD P2."""
import json, sys
from pathlib import Path

REQ = ["target","base_url","recon_at","robots","sitemap","render_mode","api","selectors",
       "pagination","auth","protection","schema","sample","recommended_engine",
       "engine_rationale","ethics_gate","expected_volume"]
RENDER = {"json_api","embedded_json","server_html","js_required"}
ENGINE = {"httpx+json","httpx+selectolax","playwright","mcp_browser"}

fails, rows = [], []
for t in ["books","quotes","seo","driftlab"]:
    p = Path("recon")/f"{t}.json"
    if not p.exists():
        fails.append(f"{t}: file tidak ada"); continue
    d = json.loads(p.read_text())
    miss = [k for k in REQ if k not in d]
    if miss: fails.append(f"{t}: field wajib hilang {miss}")
    if d.get("render_mode") not in RENDER: fails.append(f"{t}: render_mode tidak sah: {d.get('render_mode')}")
    if d.get("recommended_engine") not in ENGINE: fails.append(f"{t}: engine tidak sah: {d.get('recommended_engine')}")
    if d.get("ethics_gate",{}).get("passed") is not True: fails.append(f"{t}: ethics_gate.passed != true")
    if not isinstance(d.get("expected_volume"), int) or d["expected_volume"] <= 0: fails.append(f"{t}: expected_volume tidak sah")
    s = d.get("sample",[])
    if len(s) != 3: fails.append(f"{t}: sample harus 3 record, ada {len(s)}")
    for i,r in enumerate(s):
        if not isinstance(r,dict) or not r: fails.append(f"{t}: sample[{i}] kosong")
        for k,v in r.items():
            if isinstance(v,str) and v.strip().lower() in ("","todo","tbd","placeholder","..."):
                fails.append(f"{t}: sample[{i}].{k} placeholder")
    keyf = [f["field"] for f in d["schema"] if f.get("key_field")]
    if len(keyf) != 1: fails.append(f"{t}: harus tepat 1 key_field, ada {keyf}")
    if len(d.get("engine_rationale","")) < 80: fails.append(f"{t}: engine_rationale terlalu pendek")
    if "browser" not in d.get("engine_rationale","").lower() and "Browser" not in d.get("engine_rationale",""):
        fails.append(f"{t}: engine_rationale tidak menyebut browser (SCHEMA 1)")
    req = sum(1 for f in d["schema"] if f.get("required"))
    rows.append((t, d["render_mode"], d["recommended_engine"], d["expected_volume"], len(d["schema"]), req, keyf[0] if keyf else "-", len(s)))

print(f'{"target":10}{"render_mode":15}{"engine":20}{"volume":>8}{"field":>7}{"req":>5}  {"key_field":14}sample')
for r in rows:
    print(f'{r[0]:10}{r[1]:15}{r[2]:20}{r[3]:>8}{r[4]:>7}{r[5]:>5}  {r[6]:14}{r[7]}')
print()
if fails:
    print("GAGAL:"); [print("  -",f) for f in fails]; sys.exit(1)
print(f"VALIDASI LOLOS: {len(rows)}/4 recon sah terhadap docs/SCHEMA.md 1")
