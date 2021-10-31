import csv
from pathlib import Path
from typing import List, Tuple


def read_csv(database_path: Path) -> Tuple[List[str], List[List[str]]]:
    """Read the database csv and return the header and data in separate lists."""
    with open(str(database_path), "r") as csv_file:
        csv_reader = csv.reader(csv_file)
        data_rows = [row for row in csv_reader]

    header = data_rows[0]
    data_rows.remove(header)

    return header, data_rows

def eval_data_types(data_rows: List[List[str]], evalable: List[bool]) -> None:
    """Evaluates all entries in the datarows, that are marked as evalable. This converts 'True' (str) to True (bool)."""
    for row_num, data_row in enumerate(data_rows):
        for position, data_entry in enumerate(data_row):
            if evalable[position]:
                data_rows[row_num][position] = eval(data_entry)


def create_ngrams(word: str, location_in_word: int, n: int) -> List[str]:
    "Creates all possible ngrams around a location in a word."
    ngrams = []
    for i in range(n):
        ngram = word[location_in_word + i - n + 1 : location_in_word + i + 1]
        if len(ngram) == n:
            ngrams.append(ngram)

    return ngrams


if __name__ == "__main__":
    database_path = Path("database.csv")
    expected_header = ["input", "text", "correct", "word", "location_in_word", "time"]
    evalable = [False, False, True, False, True, True]

    assert database_path.is_file(), f"Cannot find {database_path.absolute()}"

    header, data_rows = read_csv(database_path)

    assert header == expected_header, f"Expected the database to contain colums {expected_header} but found {header}."

    eval_data_types(data_rows, evalable)

    data_rows_with_errors = [data_row for data_row in data_rows if not data_row[2]]

    for row in data_rows_with_errors:
        word = row[3]
        location_in_word = int(row[4])
        bigrams = create_ngrams(word, location_in_word, n=2)
        trigrams = create_ngrams(word, location_in_word, n=3)
