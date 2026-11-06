#!/usr/bin/env python3
"""Writes validation_report.txt: the full cases.xlsx must PASS; every valid test case must PASS; every broken
copy must be REJECTED with the expected rule code.  
 usage: uv run python lifeline/validator/build_report.py lifeline/cases.xlsx"""
import os
import sys
from validate import validate, report_lines

here = os.path.dirname(os.path.abspath(__file__))
tests = os.path.join(here, "tests")
out, ok = [], True
lines, good = report_lines(validate(sys.argv[1]), False)
out += [f"== {sys.argv[1]} (full check, 50 cases) =="] + lines + [""]
ok &= good
out.append("== valid test cases (must PASS) ==")
for f in sorted(x for x in os.listdir(tests) if x.startswith("valid_")):
    l, g = report_lines(validate(os.path.join(tests, f), True), True)
    out.append(f"{f}: {'PASS' if g else 'UNEXPECTED FAIL'}")
    ok &= g
out += ["", "== broken copies (must be REJECTED with the expected rule) =="]
rej = tot = 0
for f in sorted(x for x in os.listdir(tests) if x.startswith("broken_")):
    exp = f.rsplit("__", 1)[1].split(".")[0]
    res = validate(os.path.join(tests, f), True)
    found = {c for k, v in res.items() for c, _ in (v if k != "global" else v)}
    msgs = [m for k, v in res.items() for c, m in v if c == exp][:1]
    tot += 1
    if exp in found:
        rej += 1
        out.append(f"{f}: REJECTED  [{exp}] {msgs[0] if msgs else ''}")
    else:
        ok = False
        out.append(f"{f}: NOT REJECTED as {exp} (rules hit: {sorted(found) or 'none'})  <-- validator gap")
out += ["", f"broken copies rejected: {rej}/{tot}", "OVERALL: " + ("PASS" if ok else "FAIL")]
open(os.path.join(here, "..", "validation_report.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out[-(tot + 6):]))
sys.exit(0 if ok else 1)
