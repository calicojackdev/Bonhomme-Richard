import datetime
import requests
import uuid
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils.models import Job


def get_utc_now_string() -> str:
    return (datetime.datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S")


def log_run_begin(ats_to_scrape: str):
    run_id = str(uuid.uuid4())
    run_time = get_utc_now_string()
    print(f"{ats_to_scrape} scrape run {run_id} beginning at {run_time} UTC")
    return run_id, run_time


def log_run_end(run_id: str, ats_to_scrape: str) -> None:
    exit_time = get_utc_now_string()
    print(f"{ats_to_scrape} scrape run {run_id} ending at {exit_time} UTC")
    return


def log_error(run_id: str, error: str) -> None:
    print(f"{run_id} | {error}")
    return


def get_url(url: str) -> bytes | None:
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    elif response.status_code == 404:
        print(f"Received a 404 from {url}")
        return None
    else:
        raise ValueError(f"Did not receive an expected status code from {url}")


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def examine_current_job_list(job_list: list[Job], company_id: str) -> set:
    from utils.queries import get_active_job_ids_by_company_id

    job_list_ids = set([job.id for job in job_list])
    active_company_job_ids_results = get_active_job_ids_by_company_id(company_id)
    active_company_job_ids = set(
        [result[0] for result in active_company_job_ids_results]
    )
    ids_to_add = job_list_ids.difference(active_company_job_ids)
    ids_to_deactivate = active_company_job_ids.difference(job_list_ids)
    return ids_to_add, ids_to_deactivate


def normalize_career_site_url(career_site_url: str) -> str:
    if not (career_site_url).endswith("/"):
        career_site_url = career_site_url + "/"
    return career_site_url


def validate_uuid(uuid: str) -> bool:
    if re.search(
        "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", uuid
    ):
        return True
    else:
        return False


def parse_url_for_uuid(url: str, career_site_url: str) -> str:
    split_url = url.split(career_site_url)
    if len(split_url) == 2:
        job_id = split_url[1]
        if validate_uuid(job_id):
            return job_id
        else:
            raise ValueError(
                f"Parsed job_id does not appear to be a valid uuid: {job_id}"
            )
    else:
        raise ValueError(
            f"Unable to parse url {url} with career_site_url {career_site_url} for job_id"
        )
