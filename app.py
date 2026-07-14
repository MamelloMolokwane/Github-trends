import os
import datetime
from flask import Flask
import scripts.pipeline as etl

app = Flask(__name__)

@app.route("/")
def execute_etl_pipeline():
    bronze_layer = f"./data/bronze/raw_repo_{datetime.date.today().isoformat()}.json"
    silver_layer = f"./data/silver/cleaned_repo_{datetime.date.today()}.csv"
    gold_layer = "./data/gold/github-trends.db"
    os.makedirs(os.path.dirname(bronze_layer), exist_ok=True)
    os.makedirs(os.path.dirname(silver_layer), exist_ok=True)
    os.makedirs(os.path.dirname(gold_layer), exist_ok=True)

    etl.extract(bronze_layer)
    etl.transform(bronze_layer, silver_layer)
    etl.load_dimensions(silver_layer, gold_layer)
    etl.load_facts(silver_layer, gold_layer)

    etl.table_check(gold_layer)

    return "Pipeline finished👍🏾"