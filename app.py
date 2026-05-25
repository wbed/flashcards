import csv
import os
import sqlite3
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
DB_NAME = "flashcards.db"
CSV_NAME = "flashcards.csv"

def init_db():
    """Builds backend table architecture maps."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_code TEXT NOT NULL,
            lecturer TEXT NOT NULL,
            topic TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def load_local_csv():
    """Wipes the database and synchronization matrix from flashcards.csv."""
    if not os.path.exists(CSV_NAME):
        print(f"⚠️ Warning: '{CSV_NAME}' not found. Skipping auto-sync routing.")
        return

    try:
        with open(CSV_NAME, mode="r", encoding="utf-8-sig") as file:
            csv_reader = csv.DictReader(file)
            csv_reader.fieldnames = [name.strip().lower() for name in csv_reader.fieldnames]

            required_columns = ["module code", "lecturer", "topic", "question", "answer"]
            for col in required_columns:
                if col not in csv_reader.fieldnames:
                    print(f"❌ Error: Missing validation field target '{col}' in file header row.")
                    return

            cards_to_insert = []
            for row in csv_reader:
                if not any(row.values()):
                    continue
                cards_to_insert.append((
                    row["module code"].strip(),
                    row["lecturer"].strip(),
                    row["topic"].strip(),
                    row["question"].strip(),
                    row["answer"].strip()
                ))

            if cards_to_insert:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM flashcards")  # Ensures a clean rewrite matrix swap
                cursor.executemany("""
                    INSERT INTO flashcards (module_code, lecturer, topic, question, answer)
                    VALUES (?, ?, ?, ?, ?)
                """, cards_to_insert)
                conn.commit()
                conn.close()
                print(f"✅ Data Synchronized! Successfully stored {len(cards_to_insert)} records.")
    except Exception as e:
        print(f"❌ Synchronizer runtime collision failure: {str(e)}")

@app.route("/")
def index():
    try:
        return render_template_string(open("index.html", "r", encoding="utf-8").read())
    except FileNotFoundError:
        return "Critical Configuration Error: index.html is missing.", 404

@app.route("/api/all_flashcards")
def get_all_flashcards():
    """Dispatches the content layout arrays to render variables inside browser contexts."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT module_code, lecturer, topic, question, answer FROM flashcards")
    rows = cursor.fetchall()
    conn.close()

    payload = [{"m": r[0], "l": r[1], "t": r[2], "q": r[3], "a": r[4]} for r in rows]
    return jsonify(payload)

if __name__ == "__main__":
    init_db()
    load_local_csv()
    app.run(debug=True, port=5000)