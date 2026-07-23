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
LAST_RUN_FILE = "last_run.txt"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/etl/run")
def execute_etl_pipeline():
    today = datetime.date.today().isoformat()
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE) as file:
            if file.read().strip() == today:
                return jsonify({
                    "status": "blocked",
                    "message": "Pipeline already ran today."
                }), 403
            
    etl.extract(bronze_layer)
    etl.transform(bronze_layer, silver_layer)
    etl.load_dimensions(silver_layer)
    etl.load_facts(silver_layer)

    return jsonify({
        "status": "success",
        "message": "Pipeline completed."
    })

def query(sql):
    conn = sqlite3.connect(gold_layer)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(sql)
    rows = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return rows

@app.route("/languages")
def languages_data():
    sql = """
    SELECT
        l.language_name,
        SUM(f.stars) AS total_stars
    FROM fact_repo_snapshot f
    JOIN dim_language l
        ON f.language_key=l.language_key
    GROUP BY l.language_name
    ORDER BY total_stars DESC
    LIMIT 10;
    """
    
    return jsonify(query(sql))

@app.route("/repos")
def load_repos():
    sql = """
    SELECT
        l.repo_name,
        SUM(f.stars) AS total_stars
    FROM fact_repo_snapshot f
    JOIN dim_repository l
        ON f.repo_key=l.repo_key
    GROUP BY l.repo_name
    ORDER BY total_stars DESC
    LIMIT 10;
    """
    
    return jsonify(query(sql))

@app.route("/owners")
def load_owners():
    sql = """
    SELECT
        o.owner_name,
        SUM(f.stars) AS total_stars
    FROM fact_repo_snapshot f
    JOIN dim_owner o
        ON f.owner_key = o.owner_key
    GROUP BY o.owner_name
    ORDER BY total_stars DESC
    LIMIT 10;
    """
                   
    return jsonify(query(sql))

@app.route("/forked_repositories")
def most_forked_repositories():
    sql = """
    SELECT 
    r.repo_name,
    SUM(f.forks) AS total_forks
    FROM fact_repo_snapshot f
    JOIN dim_repository r
        ON r.repo_key = f.repo_key
    GROUP BY r.repo_name
    ORDER BY total_forks DESC
    LIMIT 10;
    """
                   
    return jsonify(query(sql))

@app.route("/watchers")
def most_watcher():
    sql = """
    SELECT 
        r.repo_name,
        SUM(f.watchers) AS total_watchers
    FROM fact_repo_snapshot f
    JOIN dim_repository r
        ON f.repo_key = r.repo_key
    GROUP BY r.repo_name
    ORDER BY total_watchers DESC
    LIMIT 10;
    """
                   
    return jsonify(query(sql))

if __name__ == "__main__":
    app.run(debug=True)