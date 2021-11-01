import random

from pathlib import Path
from typing import List, Tuple, Union

from utils.data import read_database


def create_ngrams(
    word: str,
    location_in_word: int,
    n: Union[int, Tuple[int, ...]],
) -> List[str]:
    "Creates all possible ngrams around a location in a word."
    ngrams = []

    if isinstance(n, int):
        n = (n, )
    elif not isinstance(n, tuple):
        raise ValueError(
            f"Expected an integer or tuple of integers but received {type(n)}."
        )
    else:
        pass

    for current_n in n:
        for i in range(current_n):
            ngram = word[location_in_word + i - current_n +
                         1:location_in_word + i + 1]
            if len(ngram) == current_n:
                ngrams.append(ngram)

    return ngrams


def get_words_with_ngrams(
    ngrams: List[str],
    word_list: List[str],
    shuffle_words: bool = True,
) -> List[str]:
    """Filters a list of words based on whether any ngram is contained in the word."""
    relevant_words = []

    # remove duplicate ngrams
    ngrams = list(set(ngrams))

    for word in word_list:
        for ngram in ngrams:
            if ngram in word:
                relevant_words.append(word)

    # remove duplicate words
    relevant_words = list(set(relevant_words))

    if shuffle_words:
        random.shuffle(relevant_words)

    return relevant_words


def ngrams_from_session(database_path: Path, n: Union[int, Tuple[int, ...]] = (2, 3)) -> Tuple[List[str], List[str]]:
    """Read a SessionDatabase from a Path and return all ngrams, correct and with typo."""
    assert database_path.is_file(), f"Cannot find {database_path.absolute()}."

    database = read_database(database_path)

    database_entries_with_typo = [
        database_entry for database_entry in database.entries
        if not database_entry.correct
    ]

    database_entries_without_typo = [
        database_entry for database_entry in database.entries if database_entry.correct
    ]

    typo_ngrams = []
    correct_ngrams = []

    for entry in database_entries_with_typo:
        ngrams = create_ngrams(entry.word, entry.location_in_word, n=n)

        # only extend the list if ngrams were actually created.
        if len(ngrams) > 0:
            typo_ngrams.extend(ngrams)

    for entry in database_entries_without_typo:
        ngrams = create_ngrams(entry.word, entry.location_in_word, n=n)

        # only extend the list if ngrams were actually created.
        if len(ngrams) > 0:
            correct_ngrams.extend(ngrams)

    return correct_ngrams, typo_ngrams
