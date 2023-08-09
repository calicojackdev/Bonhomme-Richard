import time
import uuid

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
)

from utils.queries import (
    get_company_by_ats,
    insert_job,
    update_inactive_jobs,
)

from utils.models import Job


# TODO: add tests, prints -> logging


ATS_TO_SCRAPE = "Workable"
ATS_BASE_URL = "https://apply.workable.com"


def parse_url_for_job_id(url: str) -> str:
    split_url = url.split("j/")
    if len(split_url) == 2:
        ats_job_id = split_url[1].strip("/")
        job_id = str(uuid.uuid5(namespace=uuid.NAMESPACE_URL, name=ats_job_id))
        return job_id, ats_job_id
    else:
        raise ValueError(f"Unable to parse url {url} for job_id")


def get_job_details(job: Job) -> Job | None:
    driver = create_driver()
    try:
        main_selector = "main[role='main']"
        driver.get(job.url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, main_selector))
        )
        job.description = driver.find_element(By.CSS_SELECTOR, main_selector).text
        job.location = driver.find_element(
            By.CSS_SELECTOR, "span[data-ui='job-location']"
        ).text
        try:
            remote_pill = driver.find_element(
                By.CSS_SELECTOR, "span[data-ui='job-remote']"
            ).text
            if remote_pill.lower() == "remote":
                job.remote = True
        except NoSuchElementException:
            job.remote = False
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
        posting_selector = "li[role='listitem']"
        driver.get(career_site_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "app")))
        driver.implicitly_wait(10)  # added for shippo
        postings = driver.find_elements(By.CSS_SELECTOR, posting_selector)
        if len(postings) == 10:
            show_more = True
            button_selector = "button[data-ui='load-more-button']"
            while show_more is True:
                try:
                    current_postings_len = len(postings)
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, button_selector)
                        )
                    )
                    driver.find_element(By.CSS_SELECTOR, button_selector).click()
                    WebDriverWait(driver, 5).until(
                        lambda driver: len(
                            driver.find_elements(By.CSS_SELECTOR, posting_selector)
                        )
                        > current_postings_len
                    )
                    postings = driver.find_elements(By.CSS_SELECTOR, posting_selector)
                    try:
                        driver.find_element(By.CSS_SELECTOR, button_selector)
                    except NoSuchElementException:
                        show_more = False
                except TimeoutException:
                    show_more = False
        for posting in postings:
            try:
                job = Job()
                job.url = posting.find_element(By.TAG_NAME, "a").get_attribute("href")
                job.id, ats_job_id = parse_url_for_job_id(job.url)
                job.title = posting.find_element(By.ID, f"{ats_job_id}_title").text
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
