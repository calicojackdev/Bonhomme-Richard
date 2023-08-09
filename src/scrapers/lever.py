import time
from bs4 import BeautifulSoup
from psycopg2.errors import UniqueViolation

from utils.helpers import (
    log_error,
    log_run_begin,
    log_run_end,
    get_url,
    examine_current_job_list,
    normalize_career_site_url,
    parse_url_for_uuid,
)

from utils.queries import (
    get_company_by_ats,
    insert_job,
    update_inactive_jobs,
    update_job,
)

from utils.models import Job


# TODO: add tests, prints -> logging

ATS_TO_SCRAPE = "Lever"


def parse_job_description(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser", from_encoding="utf-8")
    content = soup.select(".section-wrapper.page-full-width div")
    if content:
        job_description = []
        for detail in content:
            job_description.append(detail.text)
        return " ".join(job_description)
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


def parse_response_for_job_list(content: bytes, career_site_url: str) -> list[Job]:
    soup = BeautifulSoup(content, "html.parser", from_encoding="utf-8")
    job_list = []
    posting_titles = soup.select(".posting-title")
    if posting_titles:
        for posting_title in posting_titles:
            try:
                job = Job()
                job.title = posting_title.find("h5").text
                job.url = posting_title["href"]
                job.id = parse_url_for_uuid(job.url, career_site_url)
                location = posting_title.select_one(
                    ".posting-categories > span.location"
                )
                if location:
                    job.location = location.text
                workplace = posting_title.select_one(
                    ".posting-categories > span.workplaceTypes"
                )
                if workplace:
                    if workplace.text.lower() == "remote":
                        job.remote = True
                    elif workplace.text.lower() == "on-site":
                        job.remote = False
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
            job_list = parse_response_for_job_list(response_content, career_site_url)
            return job_list
        else:
            return []
    except ValueError as error:
        log_error(scrape_run_id, error)
        return []


def scrape_jobs() -> None:
    company_queryset = get_company_by_ats(ATS_TO_SCRAPE)
    for result in company_queryset:
        time.sleep(1)
        career_site_url = normalize_career_site_url(result[2])
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
    return


if __name__ == "__main__":
    scrape_run_id, run_time = log_run_begin(ATS_TO_SCRAPE)
    scrape_jobs()
    log_run_end(scrape_run_id, ATS_TO_SCRAPE)
