from utils.queries import create_tables

CREATE_TABLES_PATH = "src/setup/utils/create_tables.sql"


def add_tables(query_path: str) -> None:
    with open(query_path, mode="r") as query_file:
        query = query_file.read()
    create_tables(query)


if __name__ == "__main__":
    add_tables(CREATE_TABLES_PATH)
