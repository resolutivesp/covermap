#!/usr/bin/env python3
"""
publish.py — sync generated artefacts into the published site at the repo root.

WHY THIS EXISTS
---------------
The repo root serves GitHub Pages, but every artefact is *generated* into out2/,
out_ng/ and out_in/. Until now the copy from build output to repo root was done by
hand. That drifts: the site ended up shipping figures from one build alongside
scripts from another, and a stale hand-typed number survived three rounds of
corrections because nobody diffed the published file against the generated one.

Copying is not syncing. This script diffs first, reports exactly what changed and
by how much, and refuses to fail silently.

USAGE
    python3 code/publish.py            # show what would change, change nothing
    python3 code/publish.py --write    # actually publish
    python3 code/publish.py --write --audit   # also regenerate parameter-audit.txt

Run the four verification suites AFTER publishing, not before.
"""
import os, sys, shutil, hashlib, subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# generated file  ->  published name at repo root
MAP = {
    "out2/ghana_prepositioning_brief_v2.html": "ghana.html",
    "out2/covermap_planner.html":              "ghana-planner.html",
    "out2/pre_positioning_plan.csv":           "ghana-plan.csv",
    "out_ng/nigeria_prepositioning_brief.html": "nigeria.html",
    "out_ng/covermap_planner_nigeria.html":     "nigeria-planner.html",
    "out_ng/pre_positioning_plan_ng.csv":       "nigeria-plan.csv",
    "out_in/india_coverage_gap_brief.html":     "india.html",
    "out_in/priority_districts_in.csv":         "india-priority-districts.csv",
    "out_ke/kenya_brief_rc2.html":              "kenya.html",
    "out_ke/pre_positioning_plan_ke.csv":       "kenya-plan.csv",
}

def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    write = "--write" in sys.argv
    do_audit = "--audit" in sys.argv

    missing, changed, same = [], [], []
    for src, dst in MAP.items():
        s, d = os.path.join(BASE, src), os.path.join(BASE, dst)
        if not os.path.exists(s):
            missing.append(src); continue
        if not os.path.exists(d) or sha(s) != sha(d):
            ds = os.path.getsize(d) if os.path.exists(d) else 0
            changed.append((src, dst, os.path.getsize(s), ds))
        else:
            same.append(dst)

    if missing:
        print("!! MISSING BUILD OUTPUT — run the build scripts first:")
        for m in missing:
            print("   ", m)
        print("   Nothing was published.")
        return 1

    print(f"unchanged: {len(same)}")
    if not changed:
        print("Published site already matches the build output.")
    for src, dst, ns, os_ in changed:
        delta = ns - os_
        print(f"  {'PUBLISH' if write else 'WOULD PUBLISH'}  {dst:<32} {os_:>9,} -> {ns:>9,}  ({delta:+,} bytes)  from {src}")
        if write:
            shutil.copy2(os.path.join(BASE, src), os.path.join(BASE, dst))

    if do_audit:
        out = subprocess.run([sys.executable, os.path.join(BASE, "code", "audit_parameters.py")],
                             capture_output=True, text=True)
        if out.returncode != 0:
            print("!! audit_parameters.py failed — parameter-audit.txt NOT written")
            print(out.stderr[-800:])
            return 1
        tgt = os.path.join(BASE, "parameter-audit.txt")
        new = out.stdout
        old = open(tgt).read() if os.path.exists(tgt) else ""
        if new != old:
            print(f"  {'PUBLISH' if write else 'WOULD PUBLISH'}  parameter-audit.txt              "
                  f"{len(old):>9,} -> {len(new):>9,}  ({len(new)-len(old):+,} bytes)")
            if write:
                open(tgt, "w").write(new)
        else:
            print("unchanged: parameter-audit.txt")

    if not write:
        print("\nDry run. Nothing written. Re-run with --write to publish.")
    else:
        print("\nPublished. Now run the four verification suites.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
