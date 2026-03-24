from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# -------- DATABASE SETUP (FIXED) --------
DATABASE_URL = os.environ.get("DATABASE_URL")

# Debug (check in Render logs)
print("DATABASE_URL:", DATABASE_URL)

if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL not found. Set it in Render Environment!")

# Fix old postgres format (safety)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect with SSL (required for Render)
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

# Create table if not exists
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

# -------- HOME ROUTE --------
@app.route('/')
def home():
    return "Backend is running 🚀"

# -------- GET LEADS --------
@app.route('/leads', methods=['GET'])
def get_leads():
    cursor.execute("SELECT * FROM leads ORDER BY id DESC")
    rows = cursor.fetchall()
    return jsonify(rows)

# -------- EMAIL FUNCTION --------
def send_email(name, email, subject, message):
    try:
        sender = os.environ.get("EMAIL_USER")
        password = os.environ.get("EMAIL_PASS")
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

    except Exception as e:
        print("Email error:", e)

# -------- SUBMIT ROUTE --------
@app.route('/submit', methods=['POST'])
def submit():
    data = request.form

    name = data.get('name')
    email = data.get('email')
    subject = data.get('subject')
    message = data.get('message')

    cursor.execute(
        "INSERT INTO leads (name, email, subject, message) VALUES (%s, %s, %s, %s)",
        (name, email, subject, message)
    )
    conn.commit()

    print(f"New Lead: {name}, {email}")

    send_email(name, email, subject, message)

    return jsonify({"status": "success"})

# -------- RUN --------
if __name__ == '__main__':
    app.run()