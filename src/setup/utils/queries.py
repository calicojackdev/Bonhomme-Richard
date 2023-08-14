import os
import psycopg2 as pg
from psycopg2.extras import RealDictCursor, RealDictRow, execute_values


db_name = os.environ["postgres_db_name"]
db_user = os.environ["postgres_user"]
db_pwd = os.environ["postgres_pwd"]


def connect_to_db():
    conn = pg.connect(f"dbname={db_name} user={db_user} password={db_pwd}")
    return conn


def create_tables(create_table_query: str) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(create_table_query)
    conn.commit()
    conn.close()
    return


def insert_companies(companies: list[tuple]) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    execute_values(
        cursor,
        """
        INSERT INTO logistics_jobs.companies(
            id
            , company_name
            , ats
            , career_site_url
        )
        VALUES %s
        """,
        companies,
    )
    conn.commit()
    conn.close()
    return


def get_countries() -> list[RealDictRow]:
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT id as country_id
        , name as country_name
        , code as country_code
        FROM logistics_jobs.countries
        """
    )
    queryset = cursor.fetchall()
    conn.close()
    return queryset


def get_country_divisions() -> list[RealDictRow]:
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT id as country_division_id
        , country_id
        , name as country_division_name
        , code as country_division_code
        FROM logistics_jobs.country_divisions
        """
    )
    queryset = cursor.fetchall()
    conn.close()
    return queryset


def get_cities() -> list[RealDictRow]:
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT id as city_id
        , country_id
        , country_division_id
        , name as city_name
        FROM logistics_jobs.cities
        """
    )
    queryset = cursor.fetchall()
    conn.close()
    return queryset


def insert_countries(countries: list[tuple]) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    execute_values(
        cursor,
        """
        INSERT INTO logistics_jobs.countries(code, name)
        VALUES %s
        """,
        countries,
    )
    conn.commit()
    conn.close()
    return


def insert_country_divisions(country_divisions: list[tuple]) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    execute_values(
        cursor,
        """
        INSERT INTO logistics_jobs.country_divisions(
            country_id
            , name
            , code)
        VALUES %s
        """,
        country_divisions,
    )
    conn.commit()
    conn.close()
    return


def insert_cities(cities: list[tuple]) -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    execute_values(
        cursor,
        """
        INSERT INTO logistics_jobs.cities(
            country_id
            , country_division_id
            , name
            , latitude
            , longitude
            , timezone
            , population)
        VALUES %s
        """,
        cities,
    )
    conn.commit()
    conn.close()
    return


def insert_locations_countries() -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO logistics_jobs.locations(country_id, location)	
        SELECT co.id AS country_id
        , co.name AS location
        FROM logistics_jobs.countries AS co
            LEFT JOIN logistics_jobs.locations AS l
                ON co.id = l.country_id
        WHERE l.country_id IS NULL
        """
    )
    conn.commit()
    conn.close()
    return


def insert_locations_country_divisions() -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO logistics_jobs.locations(
            country_id, country_division_id, location
        )	
        SELECT cd.country_id
        , cd.id AS country_division_id
        , cd.name || ', ' || co.name AS location
        FROM logistics_jobs.country_divisions AS cd
            INNER JOIN logistics_jobs.countries AS co
                ON cd.country_id = co.id
            LEFT JOIN logistics_jobs.locations AS l
                ON cd.id = l.country_division_id
        WHERE l.country_division_id IS NULL
        """
    )
    conn.commit()
    conn.close()
    return


def insert_locations_cities() -> None:
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO logistics_jobs.locations(
            country_id, country_division_id, city_id, location
        )	
        SELECT c.country_id
        , c.country_division_id
        , c.id AS city_id
        , c.name || ', ' || cd.name || ', ' || co.name AS location
        FROM logistics_jobs.cities AS c
            INNER JOIN logistics_jobs.country_divisions AS cd
                ON c.country_division_id = cd.id
            INNER JOIN logistics_jobs.countries AS co
                ON c.country_id = co.id
            LEFT JOIN logistics_jobs.locations AS l
                ON c.id = l.city_id
        WHERE l.city_id IS NULL
        """
    )
    conn.commit()
    conn.close()
    return
