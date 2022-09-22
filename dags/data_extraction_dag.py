#import python modules
from datetime import timedelta
from airflow import DAG 
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime as dt
import pandas as pd
from sqlalchemy import Numeric
from airflow.utils.dates import datetime
from airflow.utils.dates import timedelta
from airflow.utils.dates import days_ago


# Specifing the default_args
default_args = {
    'owner': 'Yohans',
    'depends_on_past': False,
    'email': ['yohanssamuel2014@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'retries': 1,
    'start_date': dt(2022, 9, 21),
    'retry_delay': timedelta(minutes=5)
}
 
def split_into_chunks(arr, n):
    return [arr[i : i + n] for i in range(0, len(arr), n)]

def read_data():
    data_df = pd.read_csv('../data/20181024_d1_0900_0930.csv', 
                          skiprows=1,
                          header=None,
                          delimiter="\n",
                        )
    series = data_df[0].str.split(";")
    pd_lines = []

    for line in series:
        old_line = [item.strip() for item in line]
        info_index = 4
        info = old_line[:info_index]
        remaining = old_line[info_index:-1]
        chunks = split_into_chunks(remaining, 6)
        for chunk in chunks:
            record = info + chunk
            pd_lines.append(record)

    new_data_df = pd.DataFrame(
        pd_lines,
        columns=[
            "track_id",
            "type",
            "traveled_d",
            "avg_speed",
            "lat",
            "lon",
            "speed",
            "lon_acc",
            "lat_acc",
            "time",
        ],
    )
    return new_data_df

def data_shape():
    df = read_data()
    return df.shape


# Inserting the data into the our postgres table
def insert_data(): 
    pg_hook = PostgresHook(
    postgres_conn_id="pg_server")
    conn = pg_hook.get_sqlalchemy_engine()
    data_df = read_data()

    data_df.to_sql("traffic",
        con=conn,
        if_exists="replace",
        index=True,
        index_label="id",
        dtype={
            "track_id": Numeric(),
            "traveled_d": Numeric(),
            "avg_speed": Numeric(),
            "lat": Numeric(),
            "lon": Numeric(),
            "speed": Numeric(),
            "lon_acc": Numeric(),
            "lat_acc": Numeric(),
            "time": Numeric(),
        },
    )

####################################################
#          Airflow DAG configurations              #
####################################################

with DAG(
    dag_id='ELT_dag',
    default_args=default_args,
    description='Upload data from CSV to Postgres and Transform it with dbt',
    schedule_interval='@daily',
    start_date=days_ago(1),
    dagrun_timeout=timedelta(minutes=60),
) as pg_dag:
 

 table_creator = PostgresOperator(
    dag= pg_dag,
    task_id="create_table", 
    postgres_conn_id="pg_server",
    sql = '''
        CREATE TABLE  IF NOT EXISTS traffic( 
            id serial primary key,
            track_id numeric, 
            type text not null, 
            traveled_d double precision DEFAULT NULL,
            avg_speed double precision DEFAULT NULL, 
            lat double precision DEFAULT NULL, 
            lon double precision DEFAULT NULL, 
            speed double precision DEFAULT NULL,    
            lon_acc double precision DEFAULT NULL, 
            lat_acc double precision DEFAULT NULL, 
            time double precision DEFAULT NULL
        );
    '''
    )

 data_loader = PythonOperator(
    task_id="load_data",
    python_callable=insert_data
 )

####################################################
#          dbt Transformation                      #
####################################################

 DBT_PROJECT_DIR = "/opt/airflow/dbt"
 dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command=f"dbt run --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt",
 )

dbt_test = BashOperator(
    task_id="dbt_test",
    bash_command=f"dbt test --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt",
 )

dbt_doc_generate = BashOperator(
    task_id="dbt_doc_generate", 
    bash_command="dbt docs generate --profiles-dir /opt/airflow/dbt --project-dir "
                    "/opt/airflow/dbt"
 )

    ####################################################
    #          Task dependencies                       #
    ####################################################

table_creator >> data_loader  >> dbt_run >> dbt_test >> dbt_doc_generate