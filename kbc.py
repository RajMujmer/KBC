#!/usr/bin/env python3
"""Kaun Banega Crorepati: terminal edition.

Run:  python kbc.py
Needs only the Python standard library (3.7+) and questions.csv (or questions.json) beside it.
Questions you have already seen are remembered in ~/.kbc_seen.json,
so replays never repeat questions until a level's bank is used up.
"""
import csv
import json
import os
import random
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
os.system("")  # enables ANSI colours on Windows terminals

# ---------- look and feel ----------
GOLD, GREEN, RED, ORANGE = "\033[93m", "\033[92m", "\033[91m", "\033[38;5;208m"
BLUE, DIM, BOLD, END = "\033[94m", "\033[2m", "\033[1m", "\033[0m"

PRIZES = [1000, 2000, 3000, 5000, 10000, 20000, 40000, 80000, 160000,
          320000, 640000, 1250000, 2500000, 5000000, 10000000]
CHECKPOINTS = {4, 9}  # index of the ₹10,000 and ₹3,20,000 questions
LIFELINES = {"1": ("f", "50:50"), "2": ("a", "Audience Poll"),
             "3": ("p", "Phone a Friend"), "4": ("x", "Flip the Question")}
SEEN_FILE = os.path.join(os.path.expanduser("~"), ".kbc_seen.json")


def inr(n):
    if n >= 10**7:
        return "₹1 Crore"
    s = str(n)
    if len(s) <= 3:
        return "₹" + s
    rest, last3, parts = s[:-3], s[-3:], []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return "₹" + ",".join(parts + [last3])


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def typewriter(text, delay=0.03):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def pause(msg="Press Enter to continue..."):
    input(DIM + msg + END)


# ---------- question bank (questions.csv or questions.json) ----------
# Usage: python kbc.py [path/to/questions.csv|questions.json]
HERE = os.path.dirname(os.path.abspath(__file__))


def default_file():
    for name in ("questions.csv", "questions.json"):
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            return path
    return os.path.join(HERE, "questions.csv")


QUESTIONS_FILE = sys.argv[1] if len(sys.argv) > 1 else default_file()


def read_rows(path):
    """Return (level 1-15, question, [4 options], answer letter) rows from a .csv or .json file."""
    try:
        if path.lower().endswith(".json"):
            with open(path, encoding="utf-8-sig") as f:
                levels = json.load(f)["levels"]
            return [(n, it["q"], it["options"], it["answer"])
                    for n, lvl in enumerate(levels, 1) for it in lvl]
        rows = []
        with open(path, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
                if not any(r.values()):
                    continue  # skip blank lines
                rows.append((int(r["level"]), r["question"],
                             [r["option_a"], r["option_b"], r["option_c"], r["option_d"]],
                             r["answer"]))
        return rows
    except FileNotFoundError:
        sys.exit(f"Question file not found: {path}\nPut questions.csv next to kbc.py or pass a path.")
    except (ValueError, KeyError, TypeError) as e:
        sys.exit(f"Could not read {path}: {e!r}\n"
                 "CSV needs columns: level, question, option_a, option_b, option_c, option_d, answer.")


def load_bank(path):
    """Validate rows and group them into 15 levels of (text, options, answer_index)."""
    bank = [[] for _ in range(15)]
    for n, text, opts, ans in read_rows(path):
        letter = str(ans).strip().upper()
        if not (1 <= n <= 15 and text and len(opts) == 4 and all(opts)
                and len(letter) == 1 and letter in "ABCD"):
            sys.exit(f"Bad question (level {n}): {text!r}\n"
                     "Needs level 1-15, a question, 4 non-empty options and answer A-D.")
        bank[n - 1].append((text, list(opts), "ABCD".index(letter)))
    for n, items in enumerate(bank, 1):
        if not items:
            sys.exit(f"Level {n} has no questions in {path}.")
    return bank


BANK = load_bank(QUESTIONS_FILE)

# ---------- remembering seen questions ----------
try:
    with open(SEEN_FILE, encoding="utf-8") as f:
        SEEN = set(json.load(f))
except Exception:
    SEEN = set()


def save_seen():
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(SEEN), f)
    except OSError:
        pass


def pick_question(level, exclude=None):
    """Random unseen question for a level; shuffles option order."""
    pool = [q for q in BANK[level] if q[0] != exclude] or BANK[level]
    fresh = [q for q in pool if q[0] not in SEEN]
    if not fresh:                       # level bank used up: start it over
        for q in BANK[level]:
            SEEN.discard(q[0])
        fresh = pool
    text, opts, ans = random.choice(fresh)
    SEEN.add(text)
    save_seen()
    order = list(range(4))
    random.shuffle(order)
    return {"text": text, "opts": [opts[i] for i in order], "ans": order.index(ans)}


# ---------- screens ----------
def show_ladder(level):
    print(f"\n{GOLD}{BOLD}   MONEY LADDER{END}")
    for i in range(14, -1, -1):
        tag = " [SAFE]" if i in CHECKPOINTS else ""
        line = f"   {i + 1:>2}  {inr(PRIZES[i]):>12}{tag}"
        if i == level:
            print(f"{GOLD}{BOLD}>>{line[2:]}  <<{END}")
        elif i < level:
            print(f"{GREEN}{line}{END}")
        else:
            print(f"{BLUE if i in CHECKPOINTS else DIM}{line}{END}")


def show_question(state, note=""):
    clear()
    lvl = state["level"]
    print(f"{GOLD}{BOLD}{'=' * 64}\n   KAUN BANEGA CROREPATI\n{'=' * 64}{END}")
    lifes = "  ".join(
        (f"{DIM}[{k}] {name} (used){END}" if state["used"].get(code)
         else f"{GREEN}[{k}]{END} {name}")
        for k, (code, name) in LIFELINES.items())
    print(f"\n  Lifelines: {lifes}   {RED}[Q]{END} Quit")
    show_ladder(lvl)
    q = state["q"]
    print(f"\n{BOLD}Question {lvl + 1} for {GOLD}{inr(PRIZES[lvl])}{END}"
          + (f"  {BLUE}(Safe checkpoint!){END}" if lvl in CHECKPOINTS else ""))
    print(f"\n  {BOLD}{q['text']}{END}\n")
    for i, opt in enumerate(q["opts"]):
        letter = "ABCD"[i]
        if i in state["gone"]:
            print(f"   {DIM}{letter}: ---{END}")
        else:
            print(f"   {GOLD}{letter}:{END} {opt}")
    if note:
        print(f"\n{ORANGE}{note}{END}")


def reveal(q, chosen):
    """Suspense, then show right/wrong colours."""
    sys.stdout.write(f"\n{ORANGE}{BOLD}  Lock kiya gaya")
    for _ in range(5):
        time.sleep(0.6)
        sys.stdout.write(" .")
        sys.stdout.flush()
    print(END)
    time.sleep(0.5)
    print()
    for i, opt in enumerate(q["opts"]):
        letter = "ABCD"[i]
        if i == q["ans"]:
            print(f"   {GREEN}{BOLD}{letter}: {opt}   <- sahi jawab{END}")
        elif i == chosen:
            print(f"   {RED}{BOLD}{letter}: {opt}   <- aapka jawab{END}")
        else:
            print(f"   {DIM}{letter}: {opt}{END}")
    time.sleep(0.8)
    return chosen == q["ans"]


# ---------- lifelines ----------
def fifty_fifty(state):
    q = state["q"]
    wrong = [i for i in range(4) if i != q["ans"] and i not in state["gone"]]
    state["gone"] += random.sample(wrong, 2)
    return "Computer ji ne do galat jawab hata diye."


def audience_poll(state):
    q, lvl = state["q"], state["level"]
    live = [i for i in range(4) if i not in state["gone"]]
    p_right = max(0.4, 0.9 - 0.035 * lvl) + random.uniform(-0.05, 0.05)
    weights = {i: random.uniform(0.3, 1.3) for i in live if i != q["ans"]}
    total = sum(weights.values())
    pct = {i: round(p_right * 100) if i == q["ans"] else round((1 - p_right) * 100 * weights[i] / total)
           for i in live}
    print(f"\n{GOLD}{BOLD}  Audience, apna jawab lock kijiye...{END}\n")
    time.sleep(1)
    for i in range(4):
        val = pct.get(i, 0)
        sys.stdout.write(f"   {GOLD}{'ABCD'[i]}{END} ")
        for _ in range(int(val / 2.5)):
            sys.stdout.write(f"{GREEN if val == max(pct.values()) else BLUE}█{END}")
            sys.stdout.flush()
            time.sleep(0.03)
        print(f" {val}%")
    return "Audience ne vote kar diya. Dhyaan rahe, audience hamesha sahi nahin hoti."


def phone_friend(state):
    q, lvl = state["q"], state["level"]
    live = [i for i in range(4) if i not in state["gone"]]
    name = random.choice(["Rohan", "Meera", "Arjun", "Priya", "Kabir"])
    correct = random.random() < max(0.55, 0.97 - 0.03 * lvl)
    guess = q["ans"] if correct else random.choice([i for i in live if i != q["ans"]])
    conf = ("Mujhe pakka yaad hai" if lvl < 8 else "Mujhe lagbhag yakeen hai") if correct \
        else "Mujhe zyada pakka nahin hai, par mera andaza hai"
    print(f"\n{GOLD}{BOLD}  Calling {name}...{END}")
    for _ in range(2):
        time.sleep(0.9)
        print(f"{DIM}  ring ring...{END}")
    time.sleep(0.8)
    typewriter(f'  {name}: "Haan ji! Sawaal sun liya. {conf}... jawab hoga '
               f'{"ABCD"[guess]}: {q["opts"][guess]}. Best of luck!"')
    return "Call disconnect ho gaya."


def flip(state):
    state["q"] = pick_question(state["level"], exclude=state["q"]["text"])
    state["gone"] = []
    return "Sawaal badal diya gaya. Inaam wahi hai."


ACTIONS = {"f": fifty_fifty, "a": audience_poll, "p": phone_friend, "x": flip}


# ---------- game loop ----------
def ask_yes(prompt):
    return input(f"{BOLD}{prompt} (Y/N) > {END}").strip().upper().startswith("Y")


def play():
    state = {"level": 0, "used": {}, "gone": [], "q": pick_question(0)}
    note = "Option chuniye (A-D), ya koi lifeline number dabaiye."
    while state["level"] < 15:
        lvl = state["level"]
        show_question(state, note)
        note = ""
        cmd = input(f"\n{BOLD}Aapka jawab > {END}").strip().upper()

        if cmd in LIFELINES:
            code, name = LIFELINES[cmd]
            if state["used"].get(code):
                note = f"{name} pehle hi istemaal ho chuka hai."
                continue
            state["used"][code] = True
            note = ACTIONS[code](state)
            if code in ("a", "p"):
                pause("\nPress Enter to return to the question...")
            continue

        if cmd == "Q":
            won = PRIZES[lvl - 1] if lvl else 0
            if ask_yes(f"Quit and take home {inr(won)}?"):
                return "quit", won, lvl, state
            continue

        if cmd in ("A", "B", "C", "D"):
            idx = "ABCD".index(cmd)
            if idx in state["gone"]:
                note = "Yeh option hata diya gaya hai."
                continue
            q = state["q"]
            if not ask_yes(f"Aapne {cmd}: {q['opts'][idx]} chuna. Lock kiya jaye?"):
                continue
            if reveal(q, idx):
                if lvl == 14:
                    return "win", PRIZES[14], 15, state
                msg = (f"Sahi jawab! {inr(PRIZES[lvl])} ab pakka aapka hai." if lvl in CHECKPOINTS
                       else f"Sahi jawab! Aapne {inr(PRIZES[lvl])} jeet liye.")
                print(f"\n{GREEN}{BOLD}  {msg}{END}")
                pause()
                state["level"] += 1
                state["gone"] = []
                state["q"] = pick_question(state["level"])
                note = ""
            else:
                safe = PRIZES[9] if lvl > 9 else PRIZES[4] if lvl > 4 else 0
                print(f"\n{RED}{BOLD}  Galat jawab!{END}")
                pause()
                return "wrong", safe, lvl, state
            continue

        note = "Kripya A, B, C, D, lifeline number (1-4), ya Q dabaiye."
    return "win", PRIZES[14], 15, state


def finish(how, amount, cleared, state):
    clear()
    title = {"win": "BADHAI HO! AAP CROREPATI HAIN!",
             "quit": "Aapne khel chhoda. Samajhdari ka faisla!",
             "wrong": "Galat jawab, lekin khel acha tha!"}[how]
    print(f"\n{GOLD}{BOLD}{'=' * 64}\n   {title}\n{'=' * 64}{END}")
    print(f"\n   Aap ghar le ja rahe hain:  {GOLD}{BOLD}{inr(amount) if amount else '₹0'}{END}")
    print(f"   Sawaal paar kiye:          {cleared} of 15")
    print(f"   Lifelines istemaal:        {len(state['used'])} of 4\n")


def main():
    clear()
    print(f"{GOLD}{BOLD}{'=' * 64}\n   KAUN BANEGA CROREPATI\n{'=' * 64}{END}")
    print("\n   15 sawaal. 4 lifelines. Safe checkpoints at "
          f"{inr(10000)} and {inr(320000)}.")
    print("   Answer all 15 to win ₹1 Crore.\n")
    pause("Press Enter to take the hot seat...")
    while True:
        finish(*play())
        if not ask_yes("Phir se khelein?"):
            print(f"\n{GOLD}  Dhanyavaad! Phir milenge. Namaskar!{END}\n")
            break


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(f"\n{GOLD}  Khel beech mein band hua. Namaskar!{END}\n")
