from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify
from datetime import timedelta, datetime
import os
from dotenv import load_dotenv
import uuid
from urllib.parse import urlparse, parse_qs
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=5)

session_store = {}


@app.route("/")
def home():
    """Домашняя страница"""
    session_id = request.cookies.get("session_id")
    username = session_store.get(session_id, "guest")
    return render_template("index.html", username=username)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        session_id = request.form.get("session_id")

        if not username or not session_id:
            flash("Missing username or session_id")
            return redirect(url_for("login"))

        if session_id in session_store:
            if session_store[session_id] != username:
                flash("Неверный session_id или username")
                return redirect(url_for("login"))
        else:
            session_store[session_id] = username

        resp = redirect(url_for("dashboard"))
        resp.set_cookie("session_id", session_id, max_age=300, httponly=True)
        return resp

    username = request.args.get("username")
    session_id = request.args.get("session_id")
    if username and session_id:
        session_store[session_id] = username

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    """Дублирует домашнюю"""
    session_id = request.cookies.get("session_id")
    username = session_store.get(session_id, "guest")
    flag = ""

    if username == "admin":
        flag = os.environ.get("FLAG", "FLAG_NOT_SET")

    return render_template("dashboard.html", username=username, flag=flag)


@app.route("/generate_session")
def generate():
    """Генерирует UUID и показывает пользователю"""
    session_id = str(uuid.uuid4())
    return render_template("generate_session.html", session_id=session_id)


@app.route("/send_to_admin")
def send():
    """Отправляет "ссылку" админу"""
    url = request.args.get("url")

    if not url:
        return render_template("send_to_admin.html", error="URL is required")

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if (parsed.scheme != "http" or
            parsed.hostname != "localhost" or
            parsed.port != 5000 or
            parsed.path != "/login" or
            query.get("username") != ["admin"]):
        return render_template("send_to_admin.html", error="Invalid admin URL")

    try:
        requests.get(url)
        return render_template("send_to_admin.html", success="The link has been sent")
    except Exception as e:
        return render_template("send_to_admin.html", error=f"Request failed: {e}")

if __name__ == "__main__":
    app.run(debug=False)