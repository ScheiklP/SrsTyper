from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class DatabaseEntry:
    input: str
    text: str
    correct: bool
    word: str
    location_in_word: int
    time: float



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
