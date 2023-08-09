import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from utils.helpers import (
    log_error,
    log_run_begin,
    log_run_end,
    create_driver,
    examine_current_job_list,
    normalize_career_site_url,
    parse_url_for_uuid,
)

from utils.queries import (
    get_company_by_ats,
    insert_job,
    update_inactive_jobs,
)

from utils.models import Job


# TODO: add tests, prints -> logging


ATS_TO_SCRAPE = "Ashby"
ATS_BASE_URL = "https://jobs.ashbyhq.com"


def get_job_details(job: Job) -> Job | None:
    driver = create_driver()
    try:
        driver.get(job.url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ashby-job-posting-left-pane")
            )
        )
        details = driver.find_elements(
            By.CSS_SELECTOR, ".ashby-job-posting-left-pane > div"
        )
        for detail in details:
            if detail.find_element(By.CSS_SELECTOR, "h2").text == "Location":
                job.location = detail.find_element(By.CSS_SELECTOR, "p").text
                if job.location.lower() == "remote":
                    job.remote = True
            if detail.find_element(By.CSS_SELECTOR, "h2").text == "Compensation":
                job.salary = detail.find_element(By.CSS_SELECTOR, "ul > li > span").text
        job.description = driver.find_element(By.ID, "overview").text
    except TimeoutException:
        log_error(scrape_run_id, f"Timed out on {job.url}")
    except NoSuchElementException as error:
        log_error(scrape_run_id, error)
    driver.close()
    return job


def get_current_job_list(career_site_url: str) -> list[Job]:
    job_list = []
    driver = create_driver()
    try:
        driver.get(career_site_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".ashby-job-posting-brief-list")
            )
        )
        postings = driver.find_elements(
            By.CSS_SELECTOR, ".ashby-job-posting-brief-list > a"
        )
        for posting in postings:
            try:
                job = Job()
                job.title = posting.find_element(By.CSS_SELECTOR, "h3").text
                job.url = posting.get_attribute("href")
                job.id = parse_url_for_uuid(job.url, career_site_url)
                job_list.append(job)
            except ValueError as error:
                log_error(scrape_run_id, error)
    except TimeoutException:
        log_error(scrape_run_id, f"Timed out on {career_site_url}")
    except NoSuchElementException as error:
        log_error(scrape_run_id, error)
    driver.close()
    return job_list


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
                        job = get_job_details(job)
                        job.company_id = result[0]
                        job.active = True
                        job.new = True
                        job.scrape_run_id = scrape_run_id
                        insert_job(job)
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
