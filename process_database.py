import pprint
from pathlib import Path
from utils.data import read_database

from utils.srs import update_srs_database_from_latest_session


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    update_srs_database_from_latest_session()
    srs_database = read_database(Path("data") / "srs_database.pkl")
    pp.pprint(srs_database)
