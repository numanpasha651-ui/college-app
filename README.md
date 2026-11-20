# 📅 College Timetable App

A web app for managing college class timetables and keeping students and teachers updated about changes in real time. Built with **Flask** and **PostgreSQL**, with role-based dashboards for **Students**, **Teachers**, and **Admin**, and installable as a **PWA**.

---

## ✨ Features

### 👨‍🎓 Student
- Register and wait for admin approval
- View the timetable for their own section
- Receive notifications (class cancelled, room changed, teacher absent, etc.)
- Mark notifications as read / unread, mark all as read
- Delete notifications from their own view

### 👩‍🏫 Teacher
- Register and wait for admin approval
- View own timetable and notifications
- Send notifications to a class (absence, cancellation, room/time change, substitute, etc.)
- Request a timetable change with a reason and track its status
- Cancel or delete own requests
- Read admin announcements

### 🛠️ Admin
- Approve or delete students and teachers
- Add teachers directly
- Add, edit and delete timetable entries
- Review (approve/reject) teacher timetable change requests
- Post announcements to students and teachers
- Delete notifications and announcements
- Database information / backup note download

### 📱 General
- Session-based login (7-day session)
- Hashed passwords (Werkzeug)
- Progressive Web App support via service worker
- Ready to deploy on Render

---

## 🧰 Tech Stack

| Layer      | Technology                    |
|------------|-------------------------------|
| Backend    | Python 3.13, Flask            |
| Database   | PostgreSQL (`psycopg` 3)      |
| Server     | Gunicorn                      |
| Config     | python-dotenv                 |
| Frontend   | HTML templates (Jinja2), CSS  |
| Deployment | Render                        |

---

## 📚 Academic Setup

- **Sections:** `BCA1B1`, `BCA1B2`, `BCA1B3`, `BCA1B4`, `BCA1B5`
- **Subjects:** C-Programming, PPL, COLD, English, Hindi, Kannada, CV, and the C-Programming / PPL / COLD Labs
- **Days:** Monday – Saturday

These lists are defined at the top of `app.py` (`SECTIONS`, `SUBJECTS`, `DAYS`) and can be edited for your own college.

---

## 📁 Project Structure

```
.
├── app.py                 # Main Flask application (routes, DB setup, logic)
├── requirements.txt       # Python dependencies
├── .python-version        # Python version
├── .gitignore
├── .env                   # Local environment variables (NOT committed)
├── templates/             # HTML templates
├── static/                # CSS, JS, icons
├── service-worker.js      # PWA service worker
├── database.py            # Legacy SQLite setup (old version)
└── convert_passwords.py   # Legacy SQLite password-hash script (old version)
```

> `database.py` and `convert_passwords.py` belong to the earlier SQLite version of the project. The current app uses PostgreSQL and creates its tables automatically on startup.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL

Create a PostgreSQL database (locally, or a free one on Render) and copy its connection URL.

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-long-random-secret-key
DATABASE_URL=postgresql://user:password@host:5432/dbname

ADMIN_LOGIN_ID=admin
ADMIN_PASSWORD=your-admin-password

TEACHER_LOGIN_ID=your-teacher-login-id
TEACHER_PASSWORD=your-teacher-password

STUDENT_LOGIN_ID=Student
STUDENT_PASSWORD=your-student-password
```

| Variable         | Description                                      |
|------------------|--------------------------------------------------|
| `SECRET_KEY`     | Flask session secret (use a long random string)  |
| `DATABASE_URL`   | PostgreSQL connection string                     |
| `ADMIN_LOGIN_ID` / `ADMIN_PASSWORD` | Admin credentials             |
| `TEACHER_LOGIN_ID` / `TEACHER_PASSWORD` | Teacher login settings    |
| `STUDENT_LOGIN_ID` / `STUDENT_PASSWORD` | Student login settings    |

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

### 6. Run the app

```bash
python app.py
```

Open **http://localhost:5000** in your browser. Database tables are created automatically on first run.

---

## ☁️ Deploying on Render

1. Create a **PostgreSQL** database on Render and copy its **Internal Database URL**.
2. Create a new **Web Service** and connect this GitHub repo.
3. Set the following:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Add the environment variables from the table above (including `DATABASE_URL` and `SECRET_KEY`) under **Environment**.
5. Deploy 🎉

---

## 🔄 How It Works

1. A student or teacher registers → status is **pending**.
2. The admin approves the account → user can log in.
3. The admin builds the timetable for each section.
4. Teachers send class notifications or request timetable changes.
5. Students get notified instantly on their dashboard.

---

## 🔐 Security Notes

- Passwords are stored as hashes, never as plain text.
- Secrets are loaded from environment variables.
- Use a strong `SECRET_KEY` and strong admin credentials in production.
- Turn off `debug=True` in `app.py` before running in production (Gunicorn on Render does not use it).

---

## 🛣️ Future Improvements

- Email / push notifications
- Attendance tracking
- Support for more courses and semesters
- Export timetable as PDF

---

## 🤝 Contributing

Contributions are welcome! Fork the repo, create a feature branch, and open a pull request.

---

## 📄 License

This project is licensed under the MIT License. Add a `LICENSE` file to the repo if you want to use it.

---

## 👤 Author

**Your Name**
GitHub: [@your-username](https://github.com/your-username)
