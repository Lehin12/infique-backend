from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# -------- DATABASE CONNECTION (FIXED + SAFE) --------
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise Exception("❌ DATABASE_URL not found in environment variables")

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    return psycopg2.connect(DATABASE_URL, sslmode='require')


# -------- CREATE TABLE (RUN ON START) --------
try:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT,
        subject TEXT,
        message TEXT
    )
    ''')

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Database connected & table ready")

except Exception as e:
    print("❌ DB INIT ERROR:", e)


# -------- HOME ROUTE --------
@app.route('/')
def home():
    return "Backend is running 🚀"


# -------- GET LEADS --------
@app.route('/leads', methods=['GET'])
def get_leads():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM leads ORDER BY id DESC")
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(rows)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "DB error"}), 500


# -------- EMAIL FUNCTION --------
def send_email(name, email, subject, message):
    try:
        sender = os.environ.get("EMAIL_USER")
        password = os.environ.get("EMAIL_PASS")

        if not sender or not password:
            print("⚠️ Email env vars missing")
            return

        receiver = sender

        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = "New Demo Request - INFIQUE AI"

        body = f"""
New Demo Request:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
        """

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()

        print("✅ Email sent")

    except Exception as e:
        print("Email error:", e)


# -------- SUBMIT ROUTE --------
@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.form

        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO leads (name, email, subject, message) VALUES (%s, %s, %s, %s)",
            (name, email, subject, message)
        )

        conn.commit()
        cursor.close()
        conn.close()

        print(f"✅ New Lead: {name}, {email}")

        send_email(name, email, subject, message)

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ SUBMIT ERROR:", e)
        return jsonify({"status": "error"}), 500


# -------- RUN --------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)