import re, sqlite3, getpass
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
admins = conn.execute("SELECT id, username FROM teachers WHERE is_admin = 1").fetchall()
if not admins:
    print("No admin account found. Nothing was changed.")
    raise SystemExit

if len(admins) == 1:
    admin = admins[0]
else:
    for a in admins:
        print(a[0], "-", a[1])
    wanted = input("Type the number of the admin to change: ").strip()
    admin = next((a for a in admins if str(a[0]) == wanted), None)
    if not admin:
        print("Not found. Nothing was changed.")
        raise SystemExit

print("Current admin username:", admin[1])
new_name = input("New username (3 to 30 letters, numbers, _ . -): ").strip()

if not re.fullmatch(r"[A-Za-z0-9_.\-]{3,30}", new_name):
    print("That username is not allowed. Nothing was changed.")
    raise SystemExit
taken = conn.execute("SELECT 1 FROM teachers WHERE lower(username) = lower(?) AND id != ?", (new_name, admin[0])).fetchone()
if taken:
    print("That username is already used by another teacher. Nothing was changed.")
    raise SystemExit

print("(When you type the password, nothing shows on the screen. That is normal.)")
pw1 = getpass.getpass("New password (at least 12 characters): ")
pw2 = getpass.getpass("Type it again: ")
if pw1 != pw2:
    print("The two passwords are different. Nothing was changed.")
    raise SystemExit
if len(pw1) < 12:
    print("Too short. Use at least 12 characters. Nothing was changed.")
    raise SystemExit

conn.execute("UPDATE teachers SET username = ?, password_hash = ? WHERE id = ?",
             (new_name, generate_password_hash(pw1), admin[0]))
conn.commit()
conn.close()

print()
print("DONE. Your admin username is now:", new_name)
print()
print("IMPORTANT - one more step, or the old admin comes back:")
print("Open the .env file and change the two lines to:")
print("   ADMIN_USERNAME=" + new_name)
print("   ADMIN_PASSWORD=(your new password)")
