from airflow import DAG
from airflow.decorators import task
from datetime import datetime

with DAG(
        dag_id='tutorial',
        description='A simple tutorial DAG',
        schedule_interval="@daily",
        start_date=datetime(2022,1,1),
        tags=['example'],
    ) as dag:

       @task(task_id="tutorial_task")
       def print_helloworld():
           print('Hellow Wordl')
           return "Hello Wordld!"
        
print_helloworld()
