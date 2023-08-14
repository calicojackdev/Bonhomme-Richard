# NOTE: used to build location tables from geonames csvs

import pandas as pd
from psycopg2.errors import UniqueViolation

from utils.queries import (
    get_countries,
    get_country_divisions,
    insert_countries,
    insert_country_divisions,
    insert_cities,
    insert_locations_countries,
    insert_locations_country_divisions,
    insert_locations_cities,
)


COUNTRIES_PATH = "src/transformations/utils/data/countryInfo.csv"
DIVISION_PATH = "src/transformations/utils/data/admin1CodesASCII.csv"
CITIES_PATH = "src/transformations/utils/data/cities1000.csv"


def add_countries(countries_path: str) -> None:
    print(f"Adding countries from: {countries_path}")
    co_df = pd.read_csv(
        countries_path,
        usecols=["ISO2", "COUNTRY"],
        dtype={"ISO2": "string", "COUNTRY": "string"},
        na_filter=False,
    )
    co_df = co_df.rename(columns={"ISO2": "code", "COUNTRY": "name"})
    countries = [tuple(co) for co in co_df.to_numpy()]
    try:
        insert_countries(countries)
    except UniqueViolation as error:
        print(error)
    return


def add_country_divisions(division_path: str) -> None:
    print(f"Adding country divisions from: {division_path}")
    co_df = pd.DataFrame(get_countries())
    cd_df = pd.read_csv(
        division_path,
        usecols=["ID", "ASCIINAME"],
        dtype={"ID": "string", "ASCIINAME": "string"},
    )
    cd_df = cd_df.rename(columns={"ASCIINAME": "name"})
    cd_df["country_code"] = cd_df["ID"].str.split(".", expand=True)[0]
    cd_df["code"] = cd_df["ID"].str.split(".", expand=True)[1]
    cd_df = cd_df.merge(co_df, how="inner", on="country_code")
    cd_df = cd_df[["country_id", "name", "code"]].copy()
    country_divisions = [tuple(cd) for cd in cd_df.to_numpy()]
    try:
        insert_country_divisions(country_divisions)
    except UniqueViolation as error:
        print(error)
    return


def add_cities(cities_path: str) -> None:
    print(f"Adding cities from: {cities_path}")
    co_df = pd.DataFrame(get_countries())
    cd_df = pd.DataFrame(get_country_divisions())
    cocd_df = cd_df.merge(co_df, how="inner", on="country_id")
    cocd_df["cocd_id"] = (
        cocd_df["country_code"] + "." + cocd_df["country_division_code"]
    )
    c_df = pd.read_csv(
        cities_path,
        usecols=[
            "ASCIINAME",
            "COUNTRY_CODE",
            "ADMIN1",
            "LAT",
            "LNG",
            "POPULATION",
            "TZ",
        ],
        dtype={
            "ASCIINAME": "string",
            "COUNTRY_CODE": "string",
            "ADMIN1": "string",
            "LAT": "string",
            "LNG": "string",
            "POPULATION": "int64",
            "TZ": "string",
        },
    )
    c_df = c_df.rename(
        columns={
            "ASCIINAME": "name",
            "COUNTRY_CODE": "country_code",
            "ADMIN1": "country_division_code",
            "LAT": "latitude",
            "LNG": "longitude",
            "POPULATION": "population",
            "TZ": "timezone",
        }
    )
    c_df["cocd_id"] = c_df["country_code"] + "." + c_df["country_division_code"]
    usc_df = c_df[c_df["country_code"] == "US"]
    usc_df = usc_df[usc_df["population"] > 15000]
    gc_df = c_df[c_df["country_code"] != "US"]
    gc_df = gc_df[gc_df["population"] > 500000]
    c_df = pd.concat([usc_df, gc_df])
    c_df = c_df.merge(cocd_df, how="inner", on="cocd_id")
    c_df = c_df[
        [
            "country_id",
            "country_division_id",
            "name",
            "latitude",
            "longitude",
            "timezone",
            "population",
        ]
    ].copy()
    cities = [tuple(c) for c in c_df.to_numpy()]
    try:
        insert_cities(cities)
    except UniqueViolation as error:
        print(error)
    return


def add_locations() -> None:
    insert_locations_countries()
    insert_locations_country_divisions()
    insert_locations_cities()
    return


if __name__ == "__main__":
    add_countries(COUNTRIES_PATH)
    add_country_divisions(DIVISION_PATH)
    add_cities(CITIES_PATH)
    add_locations()
