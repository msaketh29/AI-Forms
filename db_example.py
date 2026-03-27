import sqlite3, json, uuid, hashlib

DB_NAME = "example.db"

def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_login TEXT
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forms_specs (
        form_spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_id TEXT,
        form_spec_name TEXT,
        title TEXT,
        is_public INTEGER DEFAULT 1,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forms_specs_sections (
        section_spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_spec_id INTEGER,
        section_name TEXT,
        section_order INTEGER DEFAULT 0,
        FOREIGN KEY(form_spec_id) REFERENCES forms_specs(form_spec_id)
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forms_specs_fields (
        field_spec_id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_spec_id INTEGER,
        json_data TEXT,
        processed INTEGER DEFAULT 0,
        FOREIGN KEY(form_spec_id) REFERENCES forms_specs(form_spec_id)
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forms_specs_section_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_spec_id INTEGER,
        field_spec_id INTEGER,
        field_order INTEGER,
        FOREIGN KEY(section_spec_id) REFERENCES forms_specs_sections(section_spec_id),
        FOREIGN KEY(field_spec_id) REFERENCES forms_specs_fields(field_spec_id)
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS form_submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        form_spec_id INTEGER,
        submission_data TEXT,
        submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(form_spec_id) REFERENCES forms_specs(form_spec_id)
    );""")
    try:
        cur.execute("ALTER TABLE forms_specs ADD COLUMN user_id INTEGER")
    except:
        pass
    conn.commit()
    conn.close()

def register_user(name, email, password):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, _hash(password)))
        user_id = cur.lastrowid
        conn.commit()
        cur.execute("SELECT created_at FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return {"user_id": user_id, "name": name, "email": email, "created_at": row[0] if row else None}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT user_id, name, email, created_at FROM users WHERE email=? AND password_hash=?",
                (email, _hash(password)))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE user_id=?", (row[0],))
        conn.commit()
    conn.close()
    if row:
        return {"user_id": row[0], "name": row[1], "email": row[2], "created_at": row[3]}
    return None

def save_schema_to_db(form_spec_name, title, json_schema, user_id=None):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    uid = str(uuid.uuid4())
    cur.execute("INSERT INTO forms_specs (unique_id, form_spec_name, title, is_public, user_id) VALUES (?, ?, ?, ?, ?)",
                (uid, form_spec_name, title, 1, user_id))
    form_spec_id = cur.lastrowid
    cur.execute("INSERT INTO forms_specs_sections (form_spec_id, section_name, section_order) VALUES (?, ?, ?)",
                (form_spec_id, "General Information", 0))
    section_spec_id = cur.lastrowid
    properties = json_schema.get("properties", {})
    required   = json_schema.get("required", [])
    for i, (field_name, info) in enumerate(properties.items()):
        fj = {"formSpecId": form_spec_id, "fieldLabel": field_name,
              "fieldType": info.get("format", info.get("type", "string")),
              "isRequired": field_name in required, "fieldOptions": info.get("enum", None)}
        cur.execute("INSERT INTO forms_specs_fields (form_spec_id, json_data) VALUES (?, ?)",
                    (form_spec_id, json.dumps(fj)))
        field_spec_id = cur.lastrowid
        cur.execute("INSERT INTO forms_specs_section_fields (section_spec_id, field_spec_id, field_order) VALUES (?, ?, ?)",
                    (section_spec_id, field_spec_id, i))
    conn.commit()
    conn.close()
    return form_spec_id

def save_submission(form_spec_id, submission_data):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("INSERT INTO form_submissions (form_spec_id, submission_data) VALUES (?, ?)",
                (form_spec_id, json.dumps(submission_data)))
    conn.commit()
    conn.close()

def get_all_forms(user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if user_id:
        cur.execute("""SELECT fs.form_spec_id, fs.form_spec_name, fs.title,
                       COUNT(sub.submission_id) AS sub_count
                       FROM forms_specs fs
                       LEFT JOIN form_submissions sub ON sub.form_spec_id = fs.form_spec_id
                       WHERE fs.user_id = ?
                       GROUP BY fs.form_spec_id ORDER BY fs.form_spec_id DESC""", (user_id,))
    else:
        cur.execute("""SELECT fs.form_spec_id, fs.form_spec_name, fs.title,
                       COUNT(sub.submission_id) AS sub_count
                       FROM forms_specs fs
                       LEFT JOIN form_submissions sub ON sub.form_spec_id = fs.form_spec_id
                       GROUP BY fs.form_spec_id ORDER BY fs.form_spec_id DESC""")
    rows = cur.fetchall()
    conn.close()
    return [{"form_spec_id": r[0], "form_spec_name": r[1], "title": r[2], "sub_count": r[3]} for r in rows]

def get_form_fields(form_spec_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT json_data FROM forms_specs_fields WHERE form_spec_id = ? ORDER BY field_spec_id", (form_spec_id,))
    rows = cur.fetchall()
    conn.close()
    return [json.loads(r[0]) for r in rows]

def get_submissions(form_spec_id=None, user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    base = """SELECT s.submission_id, f.title, s.submission_data, s.submitted_at, s.form_spec_id
              FROM form_submissions s JOIN forms_specs f ON s.form_spec_id = f.form_spec_id"""
    if form_spec_id and user_id:
        cur.execute(base + " WHERE s.form_spec_id=? AND f.user_id=? ORDER BY s.submitted_at DESC", (form_spec_id, user_id))
    elif form_spec_id:
        cur.execute(base + " WHERE s.form_spec_id=? ORDER BY s.submitted_at DESC", (form_spec_id,))
    elif user_id:
        cur.execute(base + " WHERE f.user_id=? ORDER BY s.submitted_at DESC", (user_id,))
    else:
        cur.execute(base + " ORDER BY s.submitted_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"submission_id": r[0], "form_title": r[1], "data": json.loads(r[2]),
             "submitted_at": r[3], "form_spec_id": r[4]} for r in rows]

def update_submission(submission_id, new_data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE form_submissions SET submission_data=? WHERE submission_id=?",
                (json.dumps(new_data), submission_id))
    conn.commit()
    conn.close()

def delete_submission(submission_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM form_submissions WHERE submission_id=?", (submission_id,))
    conn.commit()
    conn.close()

def delete_form(form_spec_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM form_submissions WHERE form_spec_id=?", (form_spec_id,))
    cur.execute("""DELETE FROM forms_specs_section_fields WHERE section_spec_id IN
                   (SELECT section_spec_id FROM forms_specs_sections WHERE form_spec_id=?)""", (form_spec_id,))
    cur.execute("DELETE FROM forms_specs_sections WHERE form_spec_id=?", (form_spec_id,))
    cur.execute("DELETE FROM forms_specs_fields WHERE form_spec_id=?", (form_spec_id,))
    cur.execute("DELETE FROM forms_specs WHERE form_spec_id=?", (form_spec_id,))
    conn.commit()
    conn.close()
