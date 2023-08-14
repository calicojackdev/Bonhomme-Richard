import uuid
import pandas as pd
from numpy import nan
from psycopg2.errors import UniqueViolation

from utils.queries import insert_companies

COMPANIES_PATH = "src/setup/data/companies.csv"


def generate_company_id(company: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, company))


def add_companies(companies_path: str) -> None:
    print(f"Adding companies from: {companies_path}")
    companies_df = pd.read_csv(companies_path)
    companies_df["id"] = companies_df["company"].apply(generate_company_id)
    companies_df = companies_df[["id", "company", "ats", "career_site"]].copy()
    companies_df = companies_df.replace(nan, None)
    companies = [tuple(c) for c in companies_df.to_numpy()]
    try:
        insert_companies(companies)
    except UniqueViolation as error:
        print(error)
    return


if __name__ == "__main__":
    add_companies(COMPANIES_PATH)
