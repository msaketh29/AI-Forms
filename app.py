import logging
from flask import Flask, request, jsonify, render_template, session
import json
from openai import OpenAI
from db_example import (
    init_db, save_schema_to_db, DB_NAME,
    get_all_forms, get_form_fields, get_submissions,
    save_submission, update_submission, delete_submission, delete_form,
    register_user, login_user
)

app = Flask(__name__)
app.secret_key = "ai_form_secret_key_change_in_prod"

# Hide per-request logs (GET /api/forms 200 etc) but keep startup URL visible
class NoRequestLogs(logging.Filter):
    def filter(self, record):
        return '127.0.0.1' not in record.getMessage()

log = logging.getLogger('werkzeug')
log.addFilter(NoRequestLogs())

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You generate JSON schemas for dynamic forms.
Return ONLY valid JSON in this structure:
{
 "reply": "short description",
 "json_schema": {
   "type": "object",
   "title": "Form Title Here",
   "properties": {},
   "required": []
 },
 "ui_schema": {}
}
Rules:
1. Include ALL relevant fields — never skip any logical field.
2. Only essential fields in "required".
3. Always include "title" in json_schema.
4. Use "enum" arrays for dropdowns.
5. Use format:"date" for dates, format:"email" for email.
6. IMPORTANT: If a form has any start/joining/from date, ALWAYS include an endDate field too. Order: joiningDate or startDate first, then endDate last.
7. For onboarding forms always include: employeeName, email, team, designation, joiningDate, endDate.
Return ONLY JSON.
"""

def load_examples():
    try:
        with open("examples.txt", "r") as f:
            return f.read()
    except:
        return ""

@app.route("/")
def index():
    return render_template("index.html")

# ── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route("/auth/register", methods=["POST"])
def auth_register():
    d = request.json
    name = d.get("name","").strip()
    email = d.get("email","").strip().lower()
    password = d.get("password","")
    if not name or not email or not password:
        return jsonify({"error": "All fields required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    user = register_user(name, email, password)
    if not user:
        return jsonify({"error": "Email already registered"}), 409
    session["user"] = user
    return jsonify({"status": "success", "user": user})

@app.route("/auth/login", methods=["POST"])
def auth_login():
    d = request.json
    email = d.get("email","").strip().lower()
    password = d.get("password","")
    user = login_user(email, password)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    session["user"] = user
    return jsonify({"status": "success", "user": user})

@app.route("/auth/logout", methods=["POST"])
def auth_logout():
    session.pop("user", None)
    return jsonify({"status": "success"})

@app.route("/auth/me")
def auth_me():
    user = session.get("user")
    if user:
        return jsonify({"user": user})
    return jsonify({"user": None})

# ── FORM ROUTES ──────────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    user = session.get("user")
    msg = request.json.get("message", "").strip()
    if not msg:
        return jsonify({"error": "Empty message"}), 400

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": load_examples()},
            {"role": "user",   "content": msg}
        ],
        response_format={"type": "json_object"}
    )
    resp = json.loads(completion.choices[0].message.content)
    form_name = msg.lower().replace(" ", "_")[:80]
    user_id = user["user_id"] if user else None

    form_spec_id = save_schema_to_db(
        form_spec_name=form_name,
        title=resp["reply"],
        json_schema=resp["json_schema"],
        user_id=user_id
    )

    return jsonify({
        "json_schema":  resp["json_schema"],
        "form_name":    form_name,
        "form_spec_id": form_spec_id
    })

@app.route("/submit_form/<int:form_spec_id>", methods=["POST"])
def submit_form(form_spec_id):
    try:
        save_submission(form_spec_id, request.json)
        return jsonify({"status": "Form submitted successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/forms")
def api_forms():
    user = session.get("user")
    user_id = user["user_id"] if user else None
    return jsonify(get_all_forms(user_id=user_id))

@app.route("/api/forms/<int:fid>/fields")
def api_fields(fid):
    return jsonify(get_form_fields(fid))

@app.route("/api/submissions")
def api_subs():
    user = session.get("user")
    user_id = user["user_id"] if user else None
    fid = request.args.get("form_id")
    return jsonify(get_submissions(form_spec_id=fid, user_id=user_id))

@app.route("/api/submissions/<int:sid>", methods=["PUT"])
def api_update(sid):
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    update_submission(sid, request.json)
    return jsonify({"success": True})

@app.route("/api/submissions/<int:sid>", methods=["DELETE"])
def api_del_sub(sid):
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    delete_submission(sid)
    return jsonify({"success": True})

@app.route("/api/forms/<int:fid>", methods=["DELETE"])
def api_del_form(fid):
    user = session.get("user")
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    delete_form(fid)
    return jsonify({"success": True})

if __name__ == "__main__":
    init_db()
    print("* Running on http://127.0.0.1:5000  (Press CTRL+C to quit)")
    app.run(debug=False, use_reloader=False)
