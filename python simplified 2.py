"""
EduFund Match - SIMPLE VERSION WITH LOGIN
-----------------------------------------
Works with plain Python 3.8+ (no pip installs).

  1. Login / Create-account page (username + password).
  2. Form: name, age, education, interest, category (caste), family income.
  3. Shows matching scholarships.
  4. Saves each student to 'students.csv' under the logged-in username.
  5. "View my saved records" needs the password again, and shows ONLY that user's data.

Safe-guards: passwords are stored as hashes (never as plain text), bad input is
handled, a locked CSV doesn't crash the app, and if tkinter is missing it falls
back to a text (console) mode.

Run:  python edufund_simple.py
"""

import csv
import getpass
import hashlib
import json
import os
import secrets
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog
    HAS_GUI = True
except ImportError:                      # tkinter missing -> console mode
    HAS_GUI = False

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:                        # __file__ missing in some notebooks
    BASE_DIR = os.getcwd()
CSV_FILE = os.path.join(BASE_DIR, "students.csv")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
CSV_HEADER = ["Username", "Name", "Age", "Education", "Interest", "Category",
              "Family Income", "Matched Scholarships"]

EDU_LEVELS = ["Class 9-10", "Class 11-12", "Diploma", "Undergraduate", "Postgraduate"]
INTERESTS = ["Science", "Engineering", "Medicine", "Commerce", "Arts", "Other"]
CATEGORIES = ["General", "EWS", "OBC", "SC", "ST"]      # social category (caste)

# ---------------------------------------------------------------
# PART 1: Scholarship "database" - copy a block to add a new one
# ---------------------------------------------------------------
SCHOLARSHIPS = [
    {"name": "Post-Matric Scholarship (SC/ST)",
     "levels": ["Class 11-12", "Diploma", "Undergraduate", "Postgraduate"],
     "categories": ["SC", "ST"],
     "max_income": 250000,
     "benefit": "Fee reimbursement + monthly allowance", "apply": "scholarships.gov.in"},
    {"name": "Central Sector Scholarship",
     "levels": ["Undergraduate", "Postgraduate"],
     "max_income": 450000,
     "benefit": "Yearly scholarship for meritorious students", "apply": "scholarships.gov.in"},
    {"name": "AICTE Pragati (Girls in Technical Education)",
     "levels": ["Diploma", "Undergraduate"], "interest": "Engineering",
     "max_income": 800000,
     "benefit": "Yearly financial help for tuition", "apply": "scholarships.gov.in"},
    {"name": "INSPIRE Scholarship (Science)",
     "levels": ["Undergraduate"], "interest": "Science",
     "max_income": 10**9,                # effectively no income limit
     "benefit": "Yearly scholarship + mentorship", "apply": "online-inspire.gov.in"},
    {"name": "PM YASASVI Scholarship (OBC)",
     "levels": ["Class 9-10", "Class 11-12"], "categories": ["OBC"],
     "max_income": 250000,
     "benefit": "Yearly scholarship for school education", "apply": "scholarships.gov.in"},
    {"name": "National Means-cum-Merit Scholarship",
     "levels": ["Class 9-10", "Class 11-12"],
     "max_income": 350000,
     "benefit": "Yearly scholarship to stop school drop-outs", "apply": "scholarships.gov.in"},
]


def find_scholarships(level, interest, income, category):
    """Return every scholarship whose rules the student passes."""
    matches = []
    for s in SCHOLARSHIPS:
        if level not in s["levels"]:
            continue
        if "interest" in s and s["interest"] != interest:
            continue
        if "categories" in s and category not in s["categories"]:
            continue
        if income > s["max_income"]:
            continue
        matches.append(s)
    return matches


# ---------------------------------------------------------------
# PART 2: Accounts (login). We never store the real password -
# only a "hash" (a scrambled version that can't be turned back).
# A random "salt" makes two people with the same password get different hashes.
# ---------------------------------------------------------------
def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000).hex()


def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):        # file missing or damaged -> no users yet
        return {}


def register(username, password):
    """Create an account. Returns (True, '') or (False, reason)."""
    username = username.strip().lower()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not username.replace("_", "").isalnum():
        return False, "Username can only have letters, numbers and underscore."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    users = load_users()
    if username in users:
        return False, "That username is already taken."
    salt = secrets.token_bytes(16)
    users[username] = {"salt": salt.hex(), "hash": hash_password(password, salt)}
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except OSError as e:
        return False, f"Could not save account: {e}"
    return True, ""


def check_login(username, password):
    """True only if the username exists and the password is correct."""
    user = load_users().get(username.strip().lower())
    if user is None:
        return False
    attempt = hash_password(password, bytes.fromhex(user["salt"]))
    return secrets.compare_digest(attempt, user["hash"])


# ---------------------------------------------------------------
# PART 3: Input checking and CSV storage
# ---------------------------------------------------------------
def to_number(text, what):
    """Turn '1,80,000' or 'Rs 200000' into an int, or raise a friendly error."""
    cleaned = str(text).replace(",", "").replace("Rs", "").replace("rs", "").strip()
    if cleaned == "":
        raise ValueError(f"Please enter your {what}.")
    try:
        return int(float(cleaned))
    except ValueError:
        raise ValueError(f"{what.capitalize()} must be a number (you typed '{text}').")


def validate(name, age_text, income_text):
    name = str(name).strip()
    if name == "":
        raise ValueError("Please enter your name.")
    age = to_number(age_text, "age")
    if not 5 <= age <= 80:
        raise ValueError("Age must be between 5 and 80.")
    income = to_number(income_text, "family income")
    if income < 0:
        raise ValueError("Family income cannot be negative.")
    return name, age, income


def make_csv_ready():
    """If an old students.csv has different columns, rename it so nothing is lost."""
    if not os.path.exists(CSV_FILE):
        return
    with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as f:
        first_row = next(csv.reader(f), [])
    if first_row != CSV_HEADER:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.replace(CSV_FILE, os.path.join(BASE_DIR, f"students_old_{stamp}.csv"))


def save_to_csv(username, name, age, level, interest, category, income, matches):
    """Add one row. Returns (True, '') or (False, error message)."""
    try:
        make_csv_ready()
        file_exists = os.path.exists(CSV_FILE)
        with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(CSV_HEADER)
            names = "; ".join(s["name"] for s in matches)
            writer.writerow([username, name, age, level, interest, category, income, names or "None"])
        return True, ""
    except PermissionError:
        return False, "Could not save: 'students.csv' is open in Excel. Close it and try again."
    except OSError as e:
        return False, f"Could not save the file: {e}"


def read_my_records(username):
    """Return ONLY the rows that belong to this username."""
    if not os.path.exists(CSV_FILE):
        return []
    try:
        with open(CSV_FILE, "r", newline="", encoding="utf-8-sig") as f:
            return [row for row in csv.DictReader(f) if row.get("Username") == username]
    except OSError:
        return []


def build_report(name, matches):
    if not matches:
        return (f"Sorry {name}, no matches found right now.\n"
                "Try state government or NGO scholarships too.")
    lines = [f"Hi {name}! You qualify for {len(matches)} scholarship(s):\n"]
    for s in matches:
        lines.append(f"* {s['name']}")
        lines.append(f"    Benefit : {s['benefit']}")
        lines.append(f"    Apply at: {s['apply']}\n")
    lines.append("Note: rules are simplified - verify on the official portal.")
    return "\n".join(lines)


# ---------------------------------------------------------------
# PART 4a: Window (GUI) mode
# ---------------------------------------------------------------
def run_gui():
    window = tk.Tk()
    window.title("EduFund Match")

    def clear_window():
        for widget in window.winfo_children():
            widget.destroy()
        window.unbind("<Return>")

    # ---------------- Login page ----------------
    def show_login():
        clear_window()
        window.geometry("380x330")
        failed = {"count": 0}            # counts wrong passwords

        tk.Label(window, text="EduFund Match", font=("Arial", 18, "bold")).pack(pady=(20, 2))
        tk.Label(window, text="Log in or create an account").pack(pady=(0, 15))
        tk.Label(window, text="Username").pack()
        user_box = tk.Entry(window, width=30)
        user_box.pack(pady=(0, 8))
        tk.Label(window, text="Password").pack()
        pass_box = tk.Entry(window, width=30, show="*")     # show="*" hides typing
        pass_box.pack(pady=(0, 15))

        def do_login():
            username = user_box.get().strip().lower()
            if check_login(username, pass_box.get()):
                show_main(username)
                return
            failed["count"] += 1
            left = 5 - failed["count"]
            pass_box.delete(0, "end")
            if left <= 0:
                messagebox.showerror("Locked", "Too many wrong attempts. Restart the app.")
                window.destroy()
            else:
                messagebox.showerror("Login failed",
                                     f"Wrong username or password. {left} attempt(s) left.")

        def do_register():
            username = user_box.get().strip().lower()
            ok, msg = register(username, pass_box.get())
            if ok:
                messagebox.showinfo("Welcome", "Account created! You are now logged in.")
                show_main(username)
            else:
                messagebox.showwarning("Could not create account", msg)

        tk.Button(window, text="Log in", width=20, command=do_login).pack(pady=3)
        tk.Button(window, text="Create account", width=20, command=do_register).pack(pady=3)
        window.bind("<Return>", lambda event: do_login())
        user_box.focus()

    # ---------------- Main page ----------------
    def show_main(username):
        clear_window()
        window.geometry("720x640")

        top = tk.Frame(window)
        top.grid(row=0, column=0, columnspan=2, sticky="we", pady=8, padx=10)
        tk.Label(top, text="EduFund Match", font=("Arial", 18, "bold")).pack(side="left")
        tk.Button(top, text="Log out", command=show_login).pack(side="right")
        tk.Label(top, text=f"Logged in as: {username}   ").pack(side="right")

        def add_label(text, row):
            tk.Label(window, text=text).grid(row=row, column=0, sticky="e", padx=8, pady=4)

        add_label("Name:", 1)
        name_box = tk.Entry(window, width=32)
        name_box.grid(row=1, column=1, sticky="w")

        add_label("Age:", 2)
        age_box = tk.Entry(window, width=32)
        age_box.grid(row=2, column=1, sticky="w")

        add_label("Education:", 3)
        level_box = ttk.Combobox(window, width=29, state="readonly", values=EDU_LEVELS)
        level_box.current(3)
        level_box.grid(row=3, column=1, sticky="w")

        add_label("Area of interest:", 4)
        interest_box = ttk.Combobox(window, width=29, state="readonly", values=INTERESTS)
        interest_box.current(0)
        interest_box.grid(row=4, column=1, sticky="w")

        add_label("Category (caste):", 5)
        category_box = ttk.Combobox(window, width=29, state="readonly", values=CATEGORIES)
        category_box.current(0)
        category_box.grid(row=5, column=1, sticky="w")

        add_label("Family income per year (Rs):", 6)
        income_box = tk.Entry(window, width=32)
        income_box.grid(row=6, column=1, sticky="w")

        result_box = tk.Text(window, width=82, height=14, state="disabled", wrap="word")
        result_box.grid(row=8, column=0, columnspan=2, padx=10, pady=(0, 10))

        def show(text):
            result_box.config(state="normal")
            result_box.delete("1.0", "end")
            result_box.insert("end", text)
            result_box.config(state="disabled")

        def on_submit():
            try:
                name, age, income = validate(name_box.get(), age_box.get(), income_box.get())
            except ValueError as e:
                messagebox.showwarning("Check your details", str(e))
                return
            level, interest, category = level_box.get(), interest_box.get(), category_box.get()
            try:
                matches = find_scholarships(level, interest, income, category)
                ok, msg = save_to_csv(username, name, age, level, interest, category, income, matches)
                show(build_report(name, matches))
                if not ok:
                    messagebox.showwarning("Not saved", msg)
            except Exception as e:                  # last safety net
                messagebox.showerror("Something went wrong", str(e))

        def view_records():
            # Ask for the password again before showing any saved data
            password = simpledialog.askstring(
                "Password needed", f"Enter the password for '{username}':",
                show="*", parent=window)
            if password is None:                    # user pressed Cancel
                return
            if not check_login(username, password):
                messagebox.showerror("Access denied", "Wrong password.")
                return
            rows = read_my_records(username)
            box = tk.Toplevel(window)
            box.title(f"Saved records - {username}")
            box.geometry("900x320")
            cols = ["Name", "Age", "Education", "Interest", "Category", "Family Income",
                    "Matched Scholarships"]
            table = ttk.Treeview(box, columns=cols, show="headings")
            for c in cols:
                table.heading(c, text=c)
                table.column(c, width=300 if c == "Matched Scholarships" else 100)
            for row in rows:
                table.insert("", "end", values=[row.get(c, "") for c in cols])
            table.pack(fill="both", expand=True, padx=8, pady=8)
            if not rows:
                tk.Label(box, text="You have no saved records yet.").pack()

        buttons = tk.Frame(window)
        buttons.grid(row=7, column=0, columnspan=2, pady=10)
        tk.Button(buttons, text="Find Scholarships", command=on_submit,
                  font=("Arial", 11, "bold"), padx=8).pack(side="left", padx=5)
        tk.Button(buttons, text="View my saved records", command=view_records,
                  padx=8).pack(side="left", padx=5)
        window.bind("<Return>", lambda event: on_submit())

        show("Fill in the form and click 'Find Scholarships'.")
        name_box.focus()

    show_login()
    window.mainloop()


# ---------------------------------------------------------------
# PART 4b: Console mode (used automatically if tkinter is missing)
# ---------------------------------------------------------------
def ask_password(prompt):
    try:
        return getpass.getpass(prompt)
    except Exception:                    # some terminals can't hide typing
        return input(prompt)


def pick(title, options):
    print(f"\n{title}")
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Please type one of the numbers shown.")


def ask(prompt, check):
    while True:
        try:
            return check(input(prompt))
        except ValueError as e:
            print("  -> " + str(e))


def console_login():
    attempts = 0
    while attempts < 5:
        choice = input("\n1. Log in\n2. Create account\nChoose: ").strip()
        username = input("Username: ").strip().lower()
        password = ask_password("Password: ")
        if choice == "2":
            ok, msg = register(username, password)
            if ok:
                return username
            print("  -> " + msg)
        elif check_login(username, password):
            return username
        else:
            attempts += 1
            print(f"  -> Wrong username or password. {5 - attempts} attempt(s) left.")
    print("Too many wrong attempts. Restart the app.")
    return None


def run_console():
    print("=== EduFund Match (console mode) ===")
    try:
        username = console_login()
        if username is None:
            return
        print(f"\nWelcome, {username}!")
        while True:
            choice = input("\n1. Find scholarships\n2. View my saved records\n3. Quit\nChoose: ").strip()
            if choice == "1":
                name = ask("Name: ", lambda t: validate(t, "20", "0")[0])
                age = ask("Age: ", lambda t: validate("x", t, "0")[1])
                level = pick("Education level:", EDU_LEVELS)
                interest = pick("Area of interest:", INTERESTS)
                category = pick("Category (caste):", CATEGORIES)
                income = ask("Family income per year (Rs): ", lambda t: validate("x", "20", t)[2])
                matches = find_scholarships(level, interest, income, category)
                ok, msg = save_to_csv(username, name, age, level, interest, category, income, matches)
                print("\n" + build_report(name, matches))
                print("\nSaved." if ok else "\n" + msg)
            elif choice == "2":
                if not check_login(username, ask_password("Re-enter your password: ")):
                    print("  -> Wrong password.")
                    continue
                rows = read_my_records(username)
                if not rows:
                    print("You have no saved records yet.")
                for r in rows:
                    print(f"- {r['Name']}, {r['Age']}, {r['Education']}, {r['Interest']}, "
                          f"{r['Category']}, Rs {r['Family Income']} -> {r['Matched Scholarships']}")
            elif choice == "3":
                return
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")


# ---------------------------------------------------------------
# PART 5: Start the program
# ---------------------------------------------------------------
if __name__ == "__main__":
    if HAS_GUI:
        try:
            run_gui()
        except tk.TclError:              # e.g. no display available
            print("Window could not open - switching to console mode.\n")
            run_console()
    else:
        print("tkinter not found - switching to console mode.\n")
        run_console()
