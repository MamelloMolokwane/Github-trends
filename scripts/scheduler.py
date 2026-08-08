from apscheduler.schedulers.blocking import BlockingScheduler
from pipeline import main
import datetime

schedule = BlockingScheduler()
retry_count = 0
Max_retries = 3

def run_etl():
    global retry_count
    try:
        main()
        retry_count = 0
        print("Pipeline completed succesfully")
    except Exception as error:
        retry_count += 1
        print(f"Pipeline failed: {error}") 

        if retry_count > Max_retries: 
            print("Maximum retries reached. Pipeline will run again tomorrow.") 
            return
        print(f"Retry attempt: {retry_count}/{Max_retries}")

        delay_hours = 2 ** retry_count
        print(f"Retrying in {delay_hours} hours.")

        schedule.add_job(
            retry_etl,
            "date",
            run_date=datetime.datetime.now() + datetime.timedelta(hours=delay_hours),
            id=f"Retry_pipeline_{retry_count}"
        )

def retry_etl():
    print("Retrying job...")
    run_etl()


schedule.add_job(
    run_etl,
    "cron",
    hour=2,
    id="GitHub_etl"
)

schedule.start()