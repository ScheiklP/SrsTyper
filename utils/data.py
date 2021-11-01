import pickle

from datetime import datetime
from typing import List, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SessionDatabaseEntry:
    input: str
    text: str
    correct: bool
    word: str
    location_in_word: int
    time: float


@dataclass
class SessionDatabase:
    entries: List[SessionDatabaseEntry] = field(default_factory=list)
    date: str = datetime.now().strftime("%Y-%m-%d_%H-%M")


def read_database(database_path: Path):
    """Read and return the database."""
    with open(str(database_path.absolute()), "rb") as database_file:
        return pickle.load(database_file)


def index_text_to_words(text: str) -> Tuple[List[str], List[int]]:
    """Index each position in the text with its corresponding word (text seperated by spaces)"""
    word_list = text.split(" ")
    word_indices = []
    counter = 0
    for char in text:
        word_indices.append(counter)
        if char == " ":
            counter += 1
    return word_list, word_indices
