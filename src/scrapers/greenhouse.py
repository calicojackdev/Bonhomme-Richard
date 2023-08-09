import time
import uuid
from bs4 import BeautifulSoup
from psycopg2.errors import UniqueViolation

from utils.helpers import (
    log_error,
    log_run_begin,
    log_run_end,
    get_url,
    examine_current_job_list,
)

from utils.queries import (
    get_company_by_ats,
    insert_job,
    update_inactive_jobs,
    update_job,
)

from utils.models import Job


# TODO: add custom site parsing
# TODO: add tests, prints -> logging

ATS_TO_SCRAPE = "Greenhouse"
ATS_BASE_URL = "https://boards.greenhouse.io"


def parse_url_for_job_id(url: str) -> str:
    split_url = url.split("jobs/")
    if len(split_url) == 2:
        job_id = str(uuid.uuid5(namespace=uuid.NAMESPACE_URL, name=split_url[1]))
        return job_id
    else:
        raise ValueError(f"Unable to parse url {url} for job_id")


def parse_job_description(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser", from_encoding="utf-8")
    content = soup.find(id="content")
    if content:
        return content.get_text()
    else:
        raise ValueError("Unable to parse job description")


def get_job_description(job_url: str) -> bytes | None:
    try:
        response_content = get_url(job_url)
        if response_content:
            job_description = parse_job_description(response_content)
            return job_description
        else:
            return None
    except ValueError as error:
        log_error(scrape_run_id, error)
        return None


def parse_response_for_job_list(content: bytes) -> list[Job]:
    soup = BeautifulSoup(content, "html.parser", from_encoding="utf-8")
    job_list = []
    posting_titles = soup.select(".opening")
    if posting_titles:
        for posting_title in posting_titles:
            try:
                job = Job()
                job.title = posting_title.find("a").text
                job.url = ATS_BASE_URL + posting_title.find("a")["href"]
                job.location = posting_title.select_one(".location").text
                if job.location.lower() == "remote":
                    job.remote = True
                job.id = parse_url_for_job_id(job.url)
                job_list.append(job)
            except ValueError as error:
                log_error(scrape_run_id, error)
        return job_list
    else:
        raise ValueError("Unable to parse response for job list")


def get_current_job_list(career_site_url: str) -> list[Job]:
    try:
        response_content = get_url(career_site_url)
        if response_content:
            job_list = parse_response_for_job_list(response_content)
            return job_list
        else:
            return []
    except ValueError as error:
        log_error(scrape_run_id, error)
        return []


def scrape_jobs() -> None:
    company_queryset = get_company_by_ats(ATS_TO_SCRAPE)
    for result in company_queryset:
        career_site_url = result[2]
        if (career_site_url).startswith(ATS_BASE_URL):
            print(f"Standard {ATS_TO_SCRAPE} URL found, proceeding...")
            time.sleep(1)
            print(f"{scrape_run_id} | {result[1]} | {career_site_url}")
            current_job_list = get_current_job_list(career_site_url)
            if current_job_list:
                ids_to_add, ids_to_deactivate = examine_current_job_list(
                    current_job_list, result[0]
                )
                if ids_to_add:
                    print(f"{len(ids_to_add)} jobs found to add")
                    for job in current_job_list:
                        if job.id in list(ids_to_add):
                            time.sleep(5)
                            job.description = get_job_description(job.url)
                            job.company_id = result[0]
                            job.scrape_run_id = scrape_run_id
                            job.active = True
                            job.new = True
                            try:
                                insert_job(job)
                            except UniqueViolation:
                                print(f"{job.id} already exists, attempting to update")
                                update_job(job)
                else:
                    print(f"No new jobs found for {career_site_url}")
                if ids_to_deactivate:
                    print(f"{len(ids_to_deactivate)} jobs found to deactivate")
                    update_inactive_jobs(list(ids_to_deactivate), scrape_run_id)
            else:
                print(f"No jobs found for {career_site_url}")
        else:
            print(f"Custom URL found: {career_site_url}")
    return


if __name__ == "__main__":
    scrape_run_id, run_time = log_run_begin(ATS_TO_SCRAPE)
    scrape_jobs()
    log_run_end(scrape_run_id, ATS_TO_SCRAPE)
