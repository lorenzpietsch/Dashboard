"""
Generate a synthetic project-portfolio dataset that reproduces the aggregates
shown in the reference dashboard.

Target aggregates (read from the reference screenshot):

  Total projects / PIs ............ 119

  Business Organisation (count)     Project Classification (count)
    DOZ ......... 25                  Building ...... 33
    Site MA ..... 17                  Equipment ..... 31
    DOM ......... 11                  Infrastr. ..... 30
    DOS .........  7                  Other ......... 25
    DOB .........  5                ---------------------- = 119
    Site Pz ..... 34
    Pharma ...... 20
  ----------------------- = 119

  Phase (count)                     Capex split (Approved Budget, mEUR ~2939)
    IDEA ......  5                     DOZ ...... 45 %
    PI ....... 15                      Site Pz .. 28 %
    CD .......  9                      Site MA ..  9 %
    BD .......  9                      DOM ......  7 %
    DD .......  4                      DOS ......  5 %
    CC ....... 53                      (DOB + Pharma share the remainder)
    CO ....... 21
    Completed   3
  ---------------- = 119

Run:  python data_generator.py   ->  writes portfolio_data.csv
"""

import numpy as np
import pandas as pd

SEED = 7  # changed seed -> different draws from the reference
rng = np.random.default_rng(SEED)

# ----------------------------------------------------------------------------- 
# Target distributions
# -----------------------------------------------------------------------------
ORG_COUNTS = {
    "DOZ": 25,
    "Site MA": 17,
    "DOM": 11,
    "DOS": 7,
    "DOB": 5,
    "Site Pz": 34,
    "Pharma": 20,
}

PHASE_COUNTS = {
    "IDEA": 5,
    "PI": 15,
    "CD": 9,
    "BD": 9,
    "DD": 4,
    "CC": 53,
    "CO": 21,
    "Completed": 3,
}

CLASS_COUNTS = {
    "Building": 33,
    "Equipment": 31,
    "Infrastr.": 30,
    "Other": 25,
}

# Capex volume in mEUR and the share each organisation owns of the total.
# Values intentionally differ from any reference so the dataset reads as
# synthetic rather than real reporting figures.
CAPEX_TOTAL_MEUR = 3517
ORG_CAPEX_SHARE = {
    "DOZ": 0.38,
    "Site Pz": 0.24,
    "Site MA": 0.12,
    "DOM": 0.10,
    "DOS": 0.06,
    "DOB": 0.05,
    "Pharma": 0.05,
}

N = sum(ORG_COUNTS.values())  # 119

# ----------------------------------------------------------------------------- 
# Name pools
# -----------------------------------------------------------------------------
# Synthetic name components. Names are assembled procedurally from these
# pools so every person in the dataset is clearly fictional and unrelated to
# any real organisation.
SYL_START = [
    "Bel", "Cor", "Dan", "Fen", "Gar", "Hal", "Jor", "Kel", "Lor", "Mar",
    "Nor", "Pel", "Quen", "Ral", "Sor", "Tav", "Vor", "Wen", "Yar", "Zel",
    "Bran", "Cael", "Dris", "Elor", "Fyn", "Gwen", "Hes", "Ira", "Jun", "Kira",
]
SYL_END = [
    "an", "ek", "is", "or", "us", "yn", "el", "ar", "en", "ix",
    "ona", "eth", "ira", "ius", "wyn", "ael", "ora", "een", "ash", "old",
]
SURNAME_A = [
    "Ash", "Black", "Bright", "Cole", "Dale", "East", "Frost", "Gold", "Grey",
    "Hart", "Iron", "North", "Oak", "Pine", "Quill", "River", "Stone", "Vale",
    "West", "Wood", "Sharp", "Swift", "Thorn", "Wells", "Marsh", "Crane",
]
SURNAME_B = [
    "berg", "borne", "brook", "field", "ford", "gate", "hall", "haven", "hill",
    "lake", "land", "ley", "mont", "ridge", "shaw", "stead", "ton", "wick",
    "wood", "worth", "dale", "fall", "well", "stone",
]


def _first():
    return rng.choice(SYL_START) + rng.choice(SYL_END)


def _surname():
    return rng.choice(SURNAME_A) + rng.choice(SURNAME_B)


def _name():
    return f"{_first()} {_surname()}"


# Build fixed pools of fictional people for the controls / external columns so
# the same names recur across rows (as in a real portfolio) but stay synthetic.
_CONTROLS_POOL = sorted({_name() for _ in range(12)})
_PCE_POOL = sorted({_name() for _ in range(10)}) + ["Not staffed", "", "", ""]
CONTROLS = _CONTROLS_POOL
PCE_EXTERN = _PCE_POOL


# ----------------------------------------------------------------------------- 
# Build the categorical backbone (exact counts, then shuffled)
# -----------------------------------------------------------------------------
def _expand(counts):
    out = []
    for key, n in counts.items():
        out.extend([key] * n)
    return out


orgs = _expand(ORG_COUNTS)
phases = _expand(PHASE_COUNTS)
classes = _expand(CLASS_COUNTS)

rng.shuffle(orgs)
rng.shuffle(phases)
rng.shuffle(classes)

# ----------------------------------------------------------------------------- 
# Project codes
# -----------------------------------------------------------------------------
def _gen_codes(n):
    codes, seen = [], set()
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    suffixes = ["", "", "", "-P", "/1", "M"]
    while len(codes) < n:
        body = "".join(rng.choice(list(letters)) for _ in range(rng.integers(3, 6)))
        code = body + str(rng.choice(suffixes))
        if code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


codes = _gen_codes(N)

# ----------------------------------------------------------------------------- 
# Buildings
# -----------------------------------------------------------------------------
def _building():
    if rng.random() < 0.35:
        return ""  # many rows have no building in the reference
    prefix = rng.choice(["MA", "PZ", "DO"])
    num = rng.integers(40, 499)
    sub = rng.integers(1, 9)
    base = f"{prefix}-{num}/{sub}"
    if rng.random() < 0.25:  # occasional multi-building entries
        base += f", {prefix}-{rng.integers(40, 499)}/{rng.integers(1, 9)}"
    return base


# ----------------------------------------------------------------------------- 
# Budgets / actuals, scaled so each organisation hits its capex target
# -----------------------------------------------------------------------------
# Phase governs how far a project has progressed -> drives actuals vs budget.
PHASE_PROGRESS = {
    "IDEA": 0.02, "PI": 0.08, "CD": 0.18, "BD": 0.30,
    "DD": 0.45, "CC": 0.70, "CO": 0.95, "Completed": 1.0,
}

# Raw (pre-scaling) budget draw per project, then scaled per organisation.
raw_budget = rng.lognormal(mean=1.2, sigma=1.3, size=N)  # wider mEUR spread

budget = np.zeros(N)
for org, share in ORG_CAPEX_SHARE.items():
    idx = [i for i, o in enumerate(orgs) if o == org]
    target = CAPEX_TOTAL_MEUR * share
    raw_sum = raw_budget[idx].sum()
    if raw_sum == 0:
        raw_sum = 1.0
    scale = target / raw_sum
    for i in idx:
        budget[i] = max(0.0, raw_budget[i] * scale)

# Actuals depend on phase progress (+ noise). FFC = forecast final cost.
actuals = np.zeros(N)
ffc = np.zeros(N)
act_cy = np.zeros(N)
fc_cy = np.zeros(N)

for i in range(N):
    prog = PHASE_PROGRESS[phases[i]]
    noise = rng.normal(1.0, 0.12)
    actuals[i] = max(0.0, budget[i] * prog * noise)
    # FFC: usually close to budget, sometimes an over/under-run
    overrun = rng.normal(1.02, 0.10)
    ffc[i] = max(actuals[i], budget[i] * overrun)
    # Current-year actuals / forecast: a slice of remaining spend
    remaining = max(0.0, ffc[i] - actuals[i])
    fc_cy[i] = remaining * rng.uniform(0.05, 0.35) if prog < 1.0 else 0.0
    act_cy[i] = budget[i] * rng.uniform(0.0, 0.06)


# ----------------------------------------------------------------------------- 
# PMR (RAG) status
# -----------------------------------------------------------------------------
def _rag(weights=(0.70, 0.20, 0.10)):
    return rng.choice(["Green", "Amber", "Red"], p=weights)


pmr_schedule, pmr_cost, pmr_overall = [], [], []
order = {"Green": 0, "Amber": 1, "Red": 2}
names = ["Green", "Amber", "Red"]
for i in range(N):
    s = _rag()
    c = _rag()
    # Overall = worst of schedule / cost most of the time
    worst = names[max(order[s], order[c])]
    o = worst if rng.random() < 0.85 else _rag()
    # IDEA / PI projects often have no rating yet
    if phases[i] in ("IDEA", "PI") and rng.random() < 0.5:
        s = c = o = ""
    pmr_schedule.append(s)
    pmr_cost.append(c)
    pmr_overall.append(o)


# ----------------------------------------------------------------------------- 
# Finish dates
# -----------------------------------------------------------------------------
def _finish_date(phase):
    if phase == "Completed":
        start = pd.Timestamp("2024-06-01")
        end = pd.Timestamp("2026-06-01")
    else:
        # later phases finish sooner, early phases finish further out
        base_year = {
            "CO": 2026, "CC": 2027, "DD": 2028, "BD": 2028,
            "CD": 2029, "PI": 2029, "IDEA": 2030,
        }.get(phase, 2028)
        start = pd.Timestamp(f"{base_year}-01-01")
        end = pd.Timestamp(f"{base_year + 1}-12-31")
    span = (end - start).days
    return (start + pd.Timedelta(days=int(rng.integers(0, span)))).strftime("%d.%m.%Y")


finish_dates = [_finish_date(p) for p in phases]

# ----------------------------------------------------------------------------- 
# Assemble dataframe
# -----------------------------------------------------------------------------
df = pd.DataFrame(
    {
        "Project Code": codes,
        "Phase": phases,
        "Business Organisation": orgs,
        "Building": [_building() for _ in range(N)],
        "Project Manager": [_name() if rng.random() < 0.9 else "" for _ in range(N)],
        "Project Controls": [str(rng.choice(CONTROLS)) for _ in range(N)],
        "PCE Extern": [str(rng.choice(PCE_EXTERN)) for _ in range(N)],
        "PMR Overall": pmr_overall,
        "PMR Schedule": pmr_schedule,
        "PMR Cost": pmr_cost,
        "Approved Budget": np.round(budget, 2),
        "Total Actuals": np.round(actuals, 2),
        "FFC": np.round(ffc, 2),
        "Finish Date": finish_dates,
        "Project Classification": classes,
        "Actuals Current Year": np.round(act_cy, 2),
        "Forecast Current Year": np.round(fc_cy, 2),
    }
)

# Sort by project code for a stable, table-like presentation
df = df.sort_values("Project Code").reset_index(drop=True)

if __name__ == "__main__":
    df.to_csv("portfolio_data.csv", index=False)
    print(f"Wrote portfolio_data.csv  ({len(df)} rows)")
    print("\nBusiness Organisation counts:")
    print(df["Business Organisation"].value_counts())
    print("\nPhase counts:")
    print(df["Phase"].value_counts())
    print("\nClassification counts:")
    print(df["Project Classification"].value_counts())
    print(f"\nTotal Approved Budget: {df['Approved Budget'].sum():,.0f} mEUR")
    print("\nCapex by organisation (mEUR):")
    print(df.groupby("Business Organisation")["Approved Budget"].sum().round(0))
