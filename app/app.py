from flask import Flask, redirect, url_for, render_template, request, flash
from datetime import timedelta
import os
from dotenv import load_dotenv
import uuid
from urllib.parse import urlparse, parse_qs
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'devkey'
app.permanent_session_lifetime = timedelta(minutes=5)

user_credentials = {
    "admin": os.getenv("ADMIN_PASSWORD", "supersecret"),
    "user": "userpass"
}

session_store = {}

@app.route("/")
def home():
    session_id = request.cookies.get("session_id")
    username = session_store.get(session_id)
    return render_template("index.html", username=username or "guest")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        session_id = request.form.get("session_id")

        if not username or not password or not session_id:
            flash("Все поля обязательны.")
            return redirect(url_for("login"))

        if session_store.get(session_id) == username:
            resp = redirect(url_for("dashboard"))
            resp.set_cookie("session_id", session_id, max_age=300, httponly=True)
            return resp

        if username in user_credentials and user_credentials[username] == password:
            session_store[session_id] = username
            resp = redirect(url_for("dashboard"))
            resp.set_cookie("session_id", session_id, max_age=300, httponly=True)
            return resp
        else:
            flash("Неверный логин или пароль.")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    session_id = request.cookies.get("session_id")
    username = session_store.get(session_id, "guest")
    flag = ""
    if username == "admin":
        flag = os.environ.get("FLAG", "FLAG_NOT_SET")
    return render_template("dashboard.html", username=username, flag=flag)

@app.route("/generate_session")
def generate():
    session_id = str(uuid.uuid4())
    return render_template("generate_session.html", session_id=session_id)

@app.route("/send_to_admin")
def send():
    url = request.args.get("url")
    if not url:
        return render_template("send_to_admin.html", error="URL обязателен")

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if (parsed.scheme != "http" or parsed.hostname != "localhost" or
            parsed.port != 5000 or parsed.path != "/login" or
            query.get("username") != ["admin"]):
        return render_template("send_to_admin.html", error="Неверная ссылка")

    session_id = query.get("session_id", [None])[0]
    if not session_id:
        return render_template("send_to_admin.html", error="Нет session_id в ссылке")

    try:

        requests.post("http://localhost:5000/login", data={
            "username": "admin",
            "password": os.getenv("ADMIN_PASSWORD", "supersecret"),
            "session_id": session_id
        })
        return render_template("send_to_admin.html", success="Ссылка отправлена админу, сессия привязана")
    except Exception as e:
        return render_template("send_to_admin.html", error=f"Ошибка при отправке: {e}")


if __name__ == "__main__":
    app.run(debug=False, threaded=True)
