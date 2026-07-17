import os
import sqlite3
import datetime
from flask import Flask, jsonify, render_template
import scripts.pipeline as etl

app = Flask(__name__)

bronze_layer = f"./data/bronze/raw_repo_{datetime.date.today().isoformat()}.json"
silver_layer = f"./data/silver/cleaned_repo_{datetime.date.today()}.csv"
gold_layer = "./data/gold/github-trends.db"
os.makedirs(os.path.dirname(bronze_layer), exist_ok=True)
os.makedirs(os.path.dirname(silver_layer), exist_ok=True)
os.makedirs(os.path.dirname(gold_layer), exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/etl/run")
def execute_etl_pipeline(): # Change this into a function that just executes the pipeline.
    etl.extract(bronze_layer)
    etl.transform(bronze_layer, silver_layer)
    etl.load_dimensions(silver_layer, gold_layer)
    etl.load_facts(silver_layer, gold_layer)

    etl.table_check(gold_layer)

    conn = sqlite3.connect(gold_layer)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fact_repo_snapshot")
    fact_data = [dict(row) for row in cursor.fetchall()]
    
    return jsonify(fact_data)

@app.route("/languages")
def languages_data():
    conn = sqlite3.connect(gold_layer)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        l.language_name,
        SUM(f.stars) AS total_stars
    FROM fact_repo_snapshot f
    JOIN dim_language l
    ON f.language_key=l.language_key
    GROUP BY l.language_name
    ORDER BY total_stars DESC;
    """)

    languages_data = [dict(row) for row in cursor.fetchall()]

    conn.close()
    
    return jsonify(languages_data)

@app.route("/repos")
def load_repos():
    conn = sqlite3.connect(gold_layer)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        l.repo_name,
        SUM(f.stars) AS total_stars
    FROM fact_repo_snapshot f
    JOIN dim_repository l
    ON f.repo_key=l.repo_key
    GROUP BY l.repo_name
    ORDER BY total_stars DESC
    LIMIT 10;
    """)

    repo_data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(repo_data)




if __name__ == "__main__":
    app.run(debug=True)