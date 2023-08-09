import os
import psycopg2 as pg

from utils.helpers import get_utc_now_string
from utils.models import Job

db_name = os.environ["postgres_db_name"]
db_user = os.environ["postgres_user"]
db_pwd = os.environ["postgres_pwd"]


def connect_to_db():
    conn = pg.connect(f"dbname={db_name} user={db_user} password={db_pwd}")
    return conn


def get_company_by_ats(ats: str) -> list[tuple]:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        , company_name
        , career_site_url 
        FROM logistics_jobs.companies
        WHERE ats = %s""",
        [ats],
    )
    queryset = cursor.fetchall()
    conn.close()
    return queryset


def get_active_job_ids_by_company_id(company_id: str) -> list[tuple]:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id 
        FROM logistics_jobs.jobs 
        WHERE company_id = %s 
            AND active = true
        """,
        [company_id],
    )
    queryset = cursor.fetchall()
    conn.close()
    return queryset


def insert_job(job: Job) -> None:
    # TODO: called as n+1 in scraper
    conn = connect_to_db()
    cursor = conn.cursor()
    print(f"Inserting : {job.id} | {job.title} | {job.url}")
    job.insert_timestamp = get_utc_now_string()
    cursor.execute(
        """
        INSERT INTO logistics_jobs.jobs(
            id
            , company_id
            , title
            , url
            , description
            , salary
            , location
            , active
            , new
            , remote
            , insert_timestamp
            , scrape_insert_run_id
            ) 
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        [
            job.id,
            job.company_id,
            job.title,
            job.url,
            job.description,
            job.salary,
            job.location,
            job.active,
            job.new,
            job.remote,
            job.insert_timestamp,
            job.scrape_run_id,
        ],
    )
    conn.commit()
    conn.close()
    return


def update_inactive_jobs(id_list: list, run_id: str) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    print(f"Deactivating IDs: {id_list}")
    for id in id_list:
        # TODO: n+1 query
        cursor.execute(
            """
            UPDATE logistics_jobs.jobs
            SET active = false
                , scrape_inactive_run_id = %s
            WHERE id = %s
        """,
            [run_id, id],
        )
        conn.commit()
    conn.close()
    return


def update_job(job: Job) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    print(f"Updating ID: {job.id}")
    job.insert_timestamp = get_utc_now_string()
    cursor.execute(
        """
        UPDATE logistics_jobs.jobs
        SET title = %s
            , url = %s
            , description = %s
            , salary = %s
            , location = %s
            , active = %s
            , new = %s
            , remote = %s
            , insert_timestamp = %s
            , scrape_insert_run_id = %s
            , scrape_inactive_run_id = NULL
        WHERE id = %s
    """,
        [
            job.title,
            job.url,
            job.description,
            job.salary,
            job.location,
            job.active,
            job.new,
            job.remote,
            job.insert_timestamp,
            job.scrape_run_id,
            job.id,
        ],
    )
    conn.commit()
    conn.close()
    return
