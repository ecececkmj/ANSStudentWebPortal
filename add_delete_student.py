import ast, shutil

APP_FILE = "app.py"
MARKER = "admin_delete_student_permanently"

BLOCK = '''# --- ADMIN ONLY: delete a student permanently (school list + account + everything they did) ---
@app.route('/admin/delete_student_permanently', methods=['POST'])
def admin_delete_student_permanently():
    if 'teacher_id' not in session:
        return 'Please log in.', 401

    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    try:
        me = conn.execute('SELECT is_admin FROM teachers WHERE id = ?', (session['teacher_id'],)).fetchone()
        if not me or me['is_admin'] != 1:
            return 'Access Denied: Master Admins Only', 403

        lrn = request.form.get('lrn', '').strip()
        if not (lrn.isascii() and lrn.isdigit() and len(lrn) == 12):
            return 'Invalid LRN', 400

        account = conn.execute('SELECT id FROM students WHERE lrn = ?', (lrn,)).fetchone()
        if account:
            student_id = account['id']
            # exam answers first (they belong to the student's attempts)
            conn.execute('DELETE FROM student_answers WHERE attempt_id IN (SELECT id FROM quiz_attempts WHERE student_id = ?)', (student_id,))
            # then every other table that stores this student's work (attempts, submissions, enrollments, reactions, comments...)
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
            for table in tables:
                if table == 'students':
                    continue
                columns = [c[1] for c in conn.execute('PRAGMA table_info("' + table + '")')]
                if 'student_id' in columns:
                    conn.execute('DELETE FROM "' + table + '" WHERE student_id = ?', (student_id,))
            conn.execute('DELETE FROM students WHERE id = ?', (student_id,))

        # remove them from the school list too, so they cannot sign up again
        try:
            conn.execute('DELETE FROM allowed_lrns WHERE lrn = ?', (lrn,))
        except sqlite3.OperationalError:
            pass   # no school list imported yet

        conn.commit()
        return 'OK', 200
    finally:
        conn.close()
'''

with open(APP_FILE, encoding="utf-8", newline="") as f:
    original = f.read()

if MARKER in original:
    print("This feature is already installed in app.py. Nothing was changed.")
    raise SystemExit

newline = "\r\n" if "\r\n" in original else "\n"
text = original.replace("\r\n", "\n")
block = BLOCK.replace("\r\n", "\n")

spot = text.rfind("if __name__ == '__main__':")
if spot == -1:
    spot = text.rfind('if __name__ == "__main__":')
if spot == -1:
    new_text = text.rstrip("\n") + "\n\n\n" + block
else:
    new_text = text[:spot].rstrip("\n") + "\n\n\n" + block + "\n\n" + text[spot:]

try:
    ast.parse(new_text)
except SyntaxError as e:
    print("Something looks wrong, so app.py was NOT changed. (" + str(e) + ")")
    raise SystemExit

shutil.copy(APP_FILE, "app_backup_before_delete_feature.py")
with open(APP_FILE, "w", encoding="utf-8", newline="") as f:
    f.write(new_text.replace("\n", newline))

print("DONE. The delete-permanently feature was added to app.py.")
print("A backup of your old app.py was saved as: app_backup_before_delete_feature.py")
