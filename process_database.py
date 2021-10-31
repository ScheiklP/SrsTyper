import random
import pprint
import pickle
from pathlib import Path
from typing import List, Tuple, Union

from utils.data import DatabaseEntry


def read_database(database_path: Path) -> List[DatabaseEntry]:
    """Read the database and return the entries."""
    with open(str(database_path.absolute()), "rb") as database_file:
        return pickle.load(database_file)


def eval_data_types(data_rows: List[List[str]], evalable: List[bool]) -> None:
    """Evaluates all entries in the datarows, that are marked as evalable. This converts 'True' (str) to True (bool)."""
    for row_num, data_row in enumerate(data_rows):
        for position, data_entry in enumerate(data_row):
            if evalable[position]:
                data_rows[row_num][position] = eval(data_entry)


def create_ngrams(word: str, location_in_word: int, n: Union[int, Tuple[int, ...]]) -> List[str]:
    "Creates all possible ngrams around a location in a word."
    ngrams = []

    if isinstance(n, int):
        n = (n,)
    elif not isinstance(n, tuple):
        raise ValueError(f"Expected an integer or tuple of integers but received {type(n)}.")
    else:
        pass

    for current_n in n:
        for i in range(current_n):
            ngram = word[location_in_word + i - current_n + 1 : location_in_word + i + 1]
            if len(ngram) == current_n:
                ngrams.append(ngram)

    return ngrams


def get_words_with_ngrams(ngrams: List[str], word_list: List[str], shuffle_words: bool = True) -> List[str]:
    """Filters a list of words based on whether any ngram is contained in the word."""
    relevant_words = []

    for word in word_list:
        for ngram in ngrams:
            if ngram in word:
                relevant_words.append(word)

    # remove duplicate words
    relevant_words = list(set(relevant_words))

    if shuffle_words:
        random.shuffle(relevant_words)

    return relevant_words


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    database_path = Path("database.pkl")
    assert database_path.is_file(), f"Cannot find {database_path.absolute()}."

    database = read_database(database_path)

    database_entries_with_typo = [database_entry for database_entry in database if not database_entry.correct]

    all_ngrams = []

    for entry in database_entries_with_typo:
        ngrams = create_ngrams(entry.word, entry.location_in_word, n=(2, 3))

        # only extend the list if ngrams were actually created.
        if len(ngrams) > 0:
            all_ngrams.extend(ngrams)

    word_file_path = Path("/usr/share/dict/words")
    assert word_file_path.is_file(), f"Cannot find {word_file_path.absolute()}."

    with open(str(word_file_path.absolute()), "r") as word_file:
        WORDS = word_file.read().splitlines()

    relevant_words = get_words_with_ngrams(all_ngrams, WORDS)

    pp.pprint(relevant_words)
    print(len(relevant_words))


