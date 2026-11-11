"""Rewrite the "### Units" section at the end of README.md from data/units.json.

Usage: python3 scripts/readme_units.py data/units.json README.md
"""
import json
import math
import sys

UNITS = {"length": "m", "area": "m²", "volume": "L", "mass": "kg", "count": "items"}


def fmt(x):
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    if e < -3 or e >= 7:
        m = f"{x / 10 ** e:.4g}"
        return f"{m} × 10<sup>{e}</sup>"
    s = f"{x:.6g}"
    whole, _, frac = s.partition(".")
    whole = f"{int(whole):,}"
    return whole + ("." + frac if frac else "")


def main(data_path, readme_path):
    units = json.load(open(data_path, encoding="utf-8"))["units"]
    out = ["### Units", "",
           "Pass a unit's ID, name or an alias. Values are in metres, square metres, litres, kilograms or items. "
           "≈ marks values that are not exact by definition.", ""]
    for cat, sym in UNITS.items():
        rows = [u for u in units if u["category"] == cat]
        out += ["<details>", f"<summary>{cat.capitalize()} ({len(rows)})</summary>", "",
                f"| Unit | ID | Also accepts | System | Value ({sym}) |", "|---|---|---|---|---|"]
        for u in rows:
            system = u["system"] + (" (fictional)" if u.get("fictional") else "")
            value = ("" if u["precision"] == "exact" else "≈ ") + fmt(u["si"])
            out.append(f"| {u['name']} | `{u['id']}` | {', '.join(u.get('aliases', []))} | {system} | {value} |")
        out += ["", "</details>", ""]
    text = open(readme_path, encoding="utf-8").read()
    head = text[: text.index("### Units")]
    open(readme_path, "w", encoding="utf-8").write(head + "\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:])
