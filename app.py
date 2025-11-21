from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import requests
from dotenv import load_dotenv

# Load API key from .env (LOCAL)
load_dotenv()

app = Flask(__name__)

# --- UNIQUE VARIABLE NAMES ---
DATABASE_FILE = "queries.db"
GEMINI_KEY = os.getenv("GEMINI_API_KEY")   # (LOCAL)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"
print("DEBUG API KEY:", GEMINI_KEY)



# ---------- DATABASE SETUP ----------
def create_database():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS ai_queries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_question TEXT,
                        ai_answer TEXT
                    )""")
    connection.commit()
    connection.close()


create_database()


# ---------- ROUTES ----------
@app.route("/")
def homepage():
    return render_template("index.html")


@app.route("/ask-ai", methods=["POST"])
def ask_gemini():
    user_question = request.json.get("question")

    if not user_question:
        return jsonify({"error": "No question received"}), 400

    # ---------- CALL GEMINI AI ----------
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_KEY}

    payload = {
        "contents": [
            {"parts": [{"text": user_question}]}
        ]
    }

    response = requests.post(GEMINI_URL, headers=headers, params=params, json=payload)
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    if response.status_code != 200:
        return jsonify({"error": "AI API error", "details": response.text}), 500

    ai_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    # ---------- SAVE TO DATABASE ----------
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO ai_queries (user_question, ai_answer) VALUES (?, ?)",
                   (user_question, ai_reply))
    connection.commit()
    connection.close()

    return jsonify({"answer": ai_reply})


# --------- FOR RENDER DEPLOYMENT ----------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

