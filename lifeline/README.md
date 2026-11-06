# LIFELINE: Algorithmic Relief-Command Engine

Design and Analysis of Algorithms project, FAST-NUCES Islamabad (DS-B), **Group 84**.

| Member | Roll no. |
|---|---|
| Wania Khalid | 24i2608 |
| Eshaal Hussain | 24i2509 |
| Hasnain Afkar | 24i2557 |

This README covers **Iteration 1**: the data generator, the validator, and the documents.
Every command below is run **from the main folder**, the one that contains `generator/`, `validator/` and `pyproject.toml`.

---

## 1. Folder structure

```
lifeline/                      <- main folder: run every command from here
|-- generator/
|   |-- common.py              shared constants: alphabet, tier ranges, random streams
|   |-- crates.py              crates, capacity, traps 46 and 47
|   |-- network.py             locations, roads, closure waves, targets, trap 48
|   |-- radio.py               radio log, six patterns, reports, trap 49
|   |-- windows.py             rescue windows and the alarm stream
|   |-- tour.py                relief sites and the planted tour
|   |-- planning.py            pipeline, drum, sensors, safety rules, rations, tier-S claims
|   |-- generate.py            builds the 50 cases and writes cases.xlsx   <- run this
|   `-- README.md              the one command that reproduces cases.xlsx
|-- validator/
|   |-- validate.py            checks cases.xlsx against rules V1 to V8   <- run this
|   |-- make_tests.py          builds validator/tests/ (valid and broken copies)
|   |-- build_report.py        writes validator/validation_report.txt
|   |-- tests/                 valid test cases and broken copies (made by make_tests.py)
|   `-- validation_report.txt  validator output: PASS, and every broken copy rejected
|-- cases.xlsx                 the 50-case workbook (made by generate.py, never edited by hand)
|-- approach.pdf               approach note (2 pages)
|-- proposal.pdf               algorithm-selection report (2 pages)
|-- members.txt                names, roll numbers, section, group number
|-- pyproject.toml             project and dependencies (used by uv)
|-- .python-version            Python version used by uv
`-- README.md                  this file
```

---

## 2. One-time setup (uv)

You need [uv](https://docs.astral.sh/uv/). Check if it is installed:

```
uv --version
```

If it is not installed, install it with either command:

```
pip install uv
```
```
winget install --id=astral-sh.uv -e
```

Then, from the main folder:

```
uv sync
```

This creates the `.venv` folder and installs the dependencies in `pyproject.toml`.
The only library the project needs is **openpyxl** (it reads and writes the Excel file).
If `uv sync` does not install it, or you see `No module named 'openpyxl'`, run this once:

```
uv add openpyxl
```

You never need to activate `.venv` yourself. Put `uv run` in front of every command.

---

## 3. Run everything, in this order

All four commands run from the main folder. Group seed = **84**.

### Step 1: Generate the data

```
uv run python generator/generate.py --seed 84 --out cases.xlsx
```

It prints `case 00 ok ...` up to `case 49 ok ...`, then `wrote cases.xlsx`. It takes about 10 seconds.

- The same seed always gives exactly the same file. This is why anyone can reproduce it.
- All randomness comes from the seed and the case number. Nothing is typed by hand.
- Never edit `cases.xlsx` by hand. If a rule is wrong, fix the generator and run it again.

### Step 2: Validate the data

```
uv run python validator/validate.py cases.xlsx
```

It prints `PASS` or the broken rules for every case. The last line must be:

```
OVERALL: PASS
```

If a case fails, the lines under it show the rule code (V1 to V8) and the reason.

### Step 3: Build the broken test copies

```
uv run python validator/make_tests.py cases.xlsx
```

This fills `validator/tests/` with 3 valid single-case files (cases 05, 22 and 47) and 61 broken copies. Each broken copy has one defect. The expected rule code is at the end of the file name, for example `broken_84-05_wrong_claim__V5.xlsx`.

### Step 4: Write the validation report

```
uv run python validator/build_report.py cases.xlsx
```

This checks the full workbook, then all valid and broken copies, and writes `validator/validation_report.txt`.
The last lines must be:

```
broken copies rejected: 61/61
OVERALL: PASS
```

This step can take a minute or two. Submit this report file.

---

## 4. What the validator checks

| Code | What it checks |
|---|---|
| V1 | The 20 sheets and exact headers, text/integer cell types, sorted rows, case id format, correct tier and scenario |
| V2 | Every size and value is inside its range |
| V3 | Ids are unique and consecutive; every reference (road ends, targets, waves, cover nodes) exists |
| V4 | The map is connected; waves are disjoint and within the size limit |
| V5 | Pattern counts, `edit_bound`, log parts, tier-S claims (recomputed) |
| V6 | Planted objects: tour and its length, cover, safety assignment, ration selection |
| V7 | Signature rules of the six case studies, and the four variety rules |
| V8 | The trap rules of cases 46 to 49 |

The validator does not trust any field. It recomputes everything itself and imports nothing from the generator.
To check only some cases (for example one test file), add `--partial`:

```
uv run python validator/validate.py validator/tests/valid_84-05.xlsx --partial
```

---

## 5. Using another seed

```
uv run python generator/generate.py --seed 17 --out cases_seed17.xlsx
uv run python validator/validate.py cases_seed17.xlsx
```

Use a different output name so you do not overwrite the submitted `cases.xlsx`.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `No module named 'openpyxl'` | Run `uv add openpyxl`, then try again |
| `No module named 'lifeline'` or `attempted relative import` | The files in `generator/` are flat, so their imports must be flat too: `from common import ...`, `import crates as cr` (no `lifeline.` and no leading dot) |
| `uv` is not recognised | Close and reopen the terminal, or run `pip install uv` |
| `FileNotFoundError: cases.xlsx` | Run Step 1 first, and run the command from the main folder |
| Validator says `FAIL` after you changed a generator file | Run Step 1 again, then Step 2, and read the rule code |
| Git wants to upload `.venv` | Make sure `.gitignore` contains `.venv/` and `__pycache__/` |

---

## 7. Submission ZIP (Iteration 1)

Name it `24I-2608-B_24I-2509-B_24I-2557-B.zip`. It contains:
`cases.xlsx`, `generator/` (with its README), `validator/` (with `tests/` and `validation_report.txt`), the approach note, `proposal.pdf`, `repository.txt` (the GitHub link) and `members.txt`.
Leave out `.venv/` and `__pycache__/`.