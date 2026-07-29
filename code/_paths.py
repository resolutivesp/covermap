"""Locate the project root from wherever this code happens to live.

Every script used to carry BASE="/home/claude/snakebite" — the absolute path of the machine the
project was developed on. That works exactly once, for one person. Anyone cloning the repository
got FileNotFoundError on the first line of every script, while the README invited them to
"clone it and reproduce the numbers".

Resolution order:
  1. $COVERMAP_BASE, if set — for running against data held outside the checkout
  2. the parent of this file's directory, when the code sits in `code/` (the repo layout)
  3. this file's own directory otherwise (the flat development layout)

SRC always points at the directory holding the scripts, so suites that read another script's
source to check what it declares find it in either layout.
"""
import os

SRC = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("COVERMAP_BASE") or (
    os.path.dirname(SRC) if os.path.basename(SRC) == "code" else SRC
)
