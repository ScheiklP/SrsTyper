import random
import pprint
import pickle
from pathlib import Path
from typing import List, Tuple, Union
from collections import Counter

from numpy.random import default_rng
import numpy as np

from utils.data import DatabaseEntry

from typing import List, Tuple, Dict
from dataclasses import dataclass, field


@dataclass
class SRSBin:
    ngrams: List[str] = field(default_factory=list)


@dataclass
class SRSDataBase:
    bins: Dict[int, SRSBin] = field(default_factory=dict)

    def move_ngram_down(self, ngram: str, current_bin_num: int) -> None:
        """Move the ngram to the next lower bin. If it is already in the lowest bin, it stays there."""
        # if the ngram is already in the first bin it should stay there
        if current_bin_num == 0:
            return

        # remove the ngram from the current bin
        self.bins[current_bin_num].ngrams.remove(ngram)

        # add the ngram to the bin below
        assert current_bin_num - 1 >= 0, f"Database was asked to move ngram into bin {current_bin_num - 1}. Only positive bins including 0 are valid."
        assert current_bin_num - 1 in self.bins, f"Did not find bin number {current_bin_num - 1}. That should not happen, because ngrams always have to go through bins in ascending order."
        self.bins[current_bin_num - 1].ngrams.append(ngram)

    def move_ngram_up(self, ngram: str, current_bin_num: int) -> None:
        """Move the ngram to the next higher bin. If the bin does not exist yet, it will be created."""
        # remove the ngram from the current bin
        self.bins[current_bin_num].ngrams.remove(ngram)

        # create bin, if necessary
        if not current_bin_num + 1 in self.bins:
            self.bins[current_bin_num + 1] = SRSBin()

        # add the ngram to the bin above
        self.bins[current_bin_num + 1].ngrams.append(ngram)

    def add_new_ngram(self, ngram: str) -> None:
        """Add a new ngram to the first bin."""
        # create bin, if necessary
        if not 0 in self.bins:
            self.bins[0] = SRSBin()

        # add the ngram to the first bin
        self.bins[0].ngrams.append(ngram)

    def find_ngram(self, ngram: str) -> Tuple[bool, int]:
        """Check if and where an ngram is in the database."""
        ngram_is_in_database = False
        ngram_bin_num = -1

        for srs_bin_num, srs_bin in self.bins.items():
            if ngram in srs_bin.ngrams:
                ngram_is_in_database = True
                ngram_bin_num = srs_bin_num
                break

        return ngram_is_in_database, ngram_bin_num

    def check_integrity(self) -> bool:
        """Ngrams should only occur once in the complete database."""
        ngrams = []
        for _, srs_bin in self.bins.items():
            ngrams.extend(srs_bin.ngrams)
        ngram_counter = Counter(ngrams)

        return sum(ngram_counter.values()) == len(ngram_counter.values())

    def get_max_bin_num(self) -> int:
        return max(self.bins.keys())


def update_srs_database_with_ngrams(
    srs_database: SRSDataBase,
    correct_ngrams: List[str],
    typo_ngrams: List[str],
) -> None:
    """Updates the SRSDataBase with the information on passed correct and typo ngrams.

        three possible cases for ngram -> only typo, only correct, both

        correct and not in database -> do nothing
        correct and in database -> move up one bin
        typo and not in database -> add
        typo and in database -> move down one bin
        both and not in database -> add
        both and in database -> random decision based on occurences
    """

    all_ngrams = list(set(typo_ngrams + correct_ngrams))

    # go through all ngrams
    for ngram in all_ngrams:
        # check if the ngram is already in the database
        ngram_is_in_database, ngram_bin_num = srs_database.find_ngram(ngram)
        if ngram_is_in_database:
            assert ngram_bin_num >= 0, f"Bin number {ngram_bin_num} is invalid. Only bin numbers >=0 make sense."

        # correct
        if ngram not in typo_ngrams:
            if ngram_is_in_database:
                srs_database.move_ngram_up(ngram, current_bin_num=ngram_bin_num)
            else:
                pass

        # typo
        elif ngram not in correct_ngrams:
            if ngram_is_in_database:
                srs_database.move_ngram_down(ngram, current_bin_num=ngram_bin_num)
            else:
                srs_database.add_new_ngram(ngram)

        # both
        else:
            if ngram_is_in_database:
                # move the ngram down with a probability of typos/(typos + correct)
                correct_occurrences = correct_ngrams.count(ngram)
                typo_occurences = typo_ngrams.count(ngram)
                if random.random() < typo_occurences / (typo_occurences +
                                                        correct_occurrences):
                    srs_database.move_ngram_down(ngram, current_bin_num=ngram_bin_num)
                else:
                    pass
            else:
                srs_database.add_new_ngram(ngram)


def read_database(database_path: Path) -> List[DatabaseEntry]:
    """Read the database and return the entries."""
    with open(str(database_path.absolute()), "rb") as database_file:
        return pickle.load(database_file)


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


def sample_ngrams_from_srs_database(srs_database: SRSDataBase, num_ngrams: int, p: float = 0.5) -> List[str]:
    """Select num_ngrams from the SRSDataBase. Distribution of ngrams over bins is sampled from a geometric disribution with success probability of p.

       If the number of samples from a selected bin is greater than the number of ngrams in the bin, less ngrams will be returned than requested by the function.
       This will happen mainly when the database is still small.
       Samples from the geometric function that exceed the number of bins will be clipped to the highest available bin.

    """

    rng = default_rng()

    max_bin_num = srs_database.get_max_bin_num()
    selected_bins = np.clip(rng.geometric(p=p, size=num_ngrams) - 1, 0, max_bin_num)

    bin_counter = Counter(selected_bins)

    selected_ngrams = []
    for bin_num, ngram_num in bin_counter.items():
        bin_ngrams = srs_database.bins[bin_num].ngrams
        selected_ngrams.extend(
                rng.choice(
                    bin_ngrams,
                    size=min(ngram_num, len(bin_ngrams)),
                    replace=False,
                    ),
                )

    return selected_ngrams


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    database_path = Path("database.pkl")
    assert database_path.is_file(), f"Cannot find {database_path.absolute()}."

    database = read_database(database_path)

    database_entries_with_typo = [
        database_entry for database_entry in database
        if not database_entry.correct
    ]
    database_entries_without_typo = [
        database_entry for database_entry in database if database_entry.correct
    ]

    typo_ngrams = []
    correct_ngrams = []

    for entry in database_entries_with_typo:
        ngrams = create_ngrams(entry.word, entry.location_in_word, n=(2, 3))

        # only extend the list if ngrams were actually created.
        if len(ngrams) > 0:
            typo_ngrams.extend(ngrams)

    for entry in database_entries_without_typo:
        ngrams = create_ngrams(entry.word, entry.location_in_word, n=(2, 3))

        # only extend the list if ngrams were actually created.
        if len(ngrams) > 0:
            correct_ngrams.extend(ngrams)


    srs_database = SRSDataBase()

    update_srs_database_with_ngrams(srs_database, correct_ngrams, typo_ngrams)

    # duplicate bins to test selection
    bin = srs_database.bins[0]
    for i in range(1, 6):
        srs_database.bins[i] = bin

    sampled_ngrams = sample_ngrams_from_srs_database(srs_database, 100)
    print(sampled_ngrams)


    word_file_path = Path("/usr/share/dict/words")
    assert word_file_path.is_file(), f"Cannot find {word_file_path.absolute()}."

    with open(str(word_file_path.absolute()), "r") as word_file:
        WORDS = word_file.read().splitlines()

    relevant_words = get_words_with_ngrams(sampled_ngrams, WORDS)

    pp.pprint(relevant_words)
    print(len(relevant_words))
