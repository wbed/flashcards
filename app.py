import csv
import os
import sqlite3
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
DB_NAME = "flashcards.db"
CSV_NAME = "flashcards.csv"

def init_db():
    """Builds backend table architecture maps if missing."""
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
    """Wipes the database and synchronizes records from flashcards.csv."""
    if not os.path.exists(CSV_NAME):
        print(f"⚠️ Warning: '{CSV_NAME}' not found in the root folder. Database auto-sync skipped.")
        return

    try:
        with open(CSV_NAME, mode="r", encoding="utf-8-sig") as file:
            # Python's native csv engine safely strips away our layout's wrapper double quotes!
            csv_reader = csv.DictReader(file)
            
            if not csv_reader.fieldnames:
                print("❌ Error: The CSV file appears to be completely empty.")
                return
                
            # Clean and normalize header strings to avoid mismatch glitches
            original_headers = csv_reader.fieldnames
            normalized_headers = [name.strip().lower().replace("_", " ") for name in original_headers]
            csv_reader.fieldnames = normalized_headers

            required_columns = ["module code", "lecturer", "topic", "question", "answer"]
            for col in required_columns:
                if col not in csv_reader.fieldnames:
                    print(f"❌ Error: Missing required structural column '{col}'. found headers: {original_headers}")
                    return

            cards_to_insert = []
            for row in csv_reader:
                if not any(row.values()):
                    continue
                cards_to_insert.append((
                    row["module code"].strip() if row["module code"] else "Unknown Module",
                    row["lecturer"].strip() if row["lecturer"] else "Unknown Lecturer",
                    row["topic"].strip() if row["topic"] else "General",
                    row["question"].strip() if row["question"] else "",
                    row["answer"].strip() if row["answer"] else ""
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
                print(f"✅ Data Synchronized! Successfully stored {len(cards_to_insert)} records in {DB_NAME}.")
            else:
                print("⚠️ Warning: CSV file processed, but zero data rows were extracted.")
                
    except Exception as e:
        print(f"❌ Synchronizer runtime collision failure: {str(e)}")

@app.route("/")
def index():
    try:
        return render_template_string(open("index.html", "r", encoding="utf-8").read())
    except FileNotFoundError:
        return "Critical Configuration Error: index.html is missing from the root directory.", 404

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
    # Port configuration bound safely for cloud service access mapping 
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)