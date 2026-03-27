# ⚡ AI Forms

An AI-powered dynamic form generator built with Flask and OpenAI. Describe any form in plain English and get a fully working, submittable form instantly.

---

## ✨ Features

- **AI Form Generation** — Type a description like *"employee onboarding form"* and get a live form in seconds
- **User Authentication** — Register & login with secure SHA-256 hashed passwords
- **Form Submissions** — Submit, view, edit and delete entries
- **My Forms Dashboard** — All your generated forms saved and manageable
- **Export CSV** — Download all submissions as a CSV file
- **SQLite Database** — Lightweight local database, no setup required
- **Quick Chips** — One-click prompts for common form types

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI | OpenAI GPT-4o Mini |
| Database | SQLite |
| Frontend | HTML, CSS, Vanilla JS |
| Auth | Session-based + SHA-256 |

---

## 📁 Project Structure
```
ai_form_builder/
├── app.py               # Flask routes & OpenAI integration
├── db_example.py        # Database models & queries
├── examples.txt         # Few-shot examples for AI prompt
├── example.db           # SQLite database (auto-created)
├── templates/
│   └── index.html       # Full frontend (single page app)
└── static/
    ├── script.js        # Auth & UI scripts
    └── style.css        # Styles
```

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai-form-builder.git
cd ai-form-builder
```

### 2. Install dependencies
```bash
pip install flask openai
```

### 3. Add your OpenAI API key

Open `app.py` and replace the API key:
```python
client = OpenAI(api_key="your-openai-api-key-here")
```

### 4. Run the app
```bash
python app.py
```

### 5. Open in browser
```
http://127.0.0.1:5000
```

---

## 🗄️ Database Schema

| Table | Description |
|---|---|
| `users` | Stores name, email, hashed password, signup date, last login |
| `forms_specs` | Stores all AI-generated form metadata |
| `forms_specs_fields` | Stores individual field definitions per form |
| `forms_specs_sections` | Groups fields into sections |
| `form_submissions` | Stores all submitted form data as JSON |

---

## 📸 Usage

1. **Sign Up** — Create an account (your details are stored once at signup)
2. **Generate a Form** — Type any form description or click a quick chip
3. **Fill & Submit** — Fill the generated form and hit Submit
4. **View Submissions** — Go to the Submissions tab to manage entries
5. **My Forms** — See all your saved forms, fill them again or delete

---

## 📄 License

MIT License © 2026 Saketh Mattegunta — see [LICENSE](./LICENSE) for details.
