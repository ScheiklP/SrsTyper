import random
import pickle
import numpy as np

from typing import List, Tuple, Dict
from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path

from utils.data import read_database
from utils.ngram import ngrams_from_session


@dataclass
class SRSBin:
    ngrams: List[str] = field(default_factory=list)


@dataclass
class SRSDataBase:
    bins: Dict[int, SRSBin] = field(default_factory=dict)
    sessions: List[str] = field(default_factory=list)

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
    session_name: str,
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

    if session_name in srs_database.sessions:
        print(f"[WARING] update_srs_database_with_ngrams: Session {session_name} is already in the database.")
        return

    srs_database.sessions.append(session_name)

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


def geometric_pmf(k: np.ndarray, p: float):
    return np.multiply(np.power(1 - p, k - 1), p)


def sample_ngrams_from_srs_database(srs_database: SRSDataBase, num_ngrams: int, p: float = 0.5) -> List[str]:
    """Select num_ngrams from the SRSDataBase. Distribution of ngrams over bins is sampled from a geometric disribution with success probability of p.

       At least one ngram per bin will be sampled into a list, that is shuffled and reduced to num_ngrams items, before being returned.

       If the number of samples from a selected bin is greater than the number of ngrams in the bin, less ngrams will be returned than requested by the function.
       This will happen mainly when the database is still small.
       Samples from the geometric function that exceed the number of bins will be clipped to the highest available bin.


    """

    rng = np.random.default_rng()

    max_bin_num = srs_database.get_max_bin_num()
    selected_bins = np.clip(rng.geometric(p=p, size=num_ngrams) - 1, 0, max_bin_num)


    bin_counter = Counter(selected_bins)

    for bin_num in range(max_bin_num + 1):
        if not bin_num in bin_counter.keys():
            bin_counter[bin_num] = 1

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

    np.random.shuffle(selected_ngrams)

    return selected_ngrams[:num_ngrams]


def write_srs_database(srs_database: SRSDataBase, database_save_path: Path = Path("data") / "srs_database.pkl") -> None:
    """Save the database to disk."""
    with open(str(database_save_path), "wb") as output_file:
        pickle.dump(srs_database, output_file)


def update_srs_database_from_latest_session(data_dir: Path = Path("data"), srs_database_name: str = "srs_database.pkl") -> None:
    """Look for the latest session database and update the SRSDataBase with the data from that session."""

    assert data_dir.is_dir()

    # get data from latest session
    session_database_paths = [database_path for database_path in data_dir.iterdir() if "session" in database_path.name]
    assert len(session_database_paths) > 0
    session_database_paths.sort()
    correct_ngrams, typo_ngrams = ngrams_from_session(session_database_paths[-1])

    # get srs data
    srs_database_path = data_dir / srs_database_name
    if not srs_database_path.is_file():
        srs_database = SRSDataBase()
    else:
        srs_database= read_database(srs_database_path)

    # update the srs database
    update_srs_database_with_ngrams(srs_database, correct_ngrams, typo_ngrams, session_name=session_database_paths[-1].name)
    write_srs_database(srs_database)
