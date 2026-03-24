from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# -------- DATABASE SETUP --------
DATABASE_URL = "postgresql://infique_user:YOUR_PASSWORD@dpg-d7012pvafjfc73as6bcg-a.singapore-postgres.render.com/infique"

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

conn = psycopg2.connect(DATABASE_URL)
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
        sender = 'viveksaxenads@gmail.com'
        receiver = 'viveksaxenads@gmail.com'
        password = 'YOUR_APP_PASSWORD'

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

# -------- RUN SERVER --------
if __name__ == '__main__':
    app.run()