import pprint
from pathlib import Path
from utils.data import read_database

from utils.srs import update_srs_database_from_latest_session, sample_ngrams_from_srs_database
from utils.ngram import get_words_with_ngrams


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)

    update_srs_database_from_latest_session()
    srs_database = read_database(Path("data") / "srs_database.pkl")


    # duplicate bins to test selection
    bin = srs_database.bins[0]
    for i in range(1, 6):
        srs_database.bins[i] = bin

    sampled_ngrams = sample_ngrams_from_srs_database(srs_database, 100)
    print(sampled_ngrams)
    print(len(sampled_ngrams))


    word_file_path = Path("/usr/share/dict/words")
    assert word_file_path.is_file(), f"Cannot find {word_file_path.absolute()}."

    with open(str(word_file_path.absolute()), "r") as word_file:
        WORDS = word_file.read().splitlines()

    relevant_words = get_words_with_ngrams(sampled_ngrams, WORDS)

    # pp.pprint(relevant_words)
    # print(len(relevant_words))
