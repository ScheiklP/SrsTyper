import pickle
import numpy as np
from typing import List
from time import time
from pathlib import Path

from textual.app import App
from textual import events

from widgets.box import TextBox, InfoBox, GutterBox
from utils.data import SessionDatabase, SessionDatabaseEntry, index_text_to_words, read_database
from utils.srs import update_srs_database_from_latest_session, sample_ngrams_from_srs_database
from utils.ngram import get_words_with_ngrams


class SrsTyperApp(App):
    """Terminal application for personalized typing practice based on the Spaced Repetition Sysem (SRS)."""

    def __init__(self, full_text: str, **kwargs):

        # Raw text that is to be typed in the session.
        self.full_text = full_text
        self.text_length = len(full_text)

        super().__init__(**kwargs)


    async def on_load(self, _: events.Load) -> None:
        """Called before entering application mode."""

        self.data_dir = Path("data")
        if not self.data_dir.is_dir():
            self.data_dir.mkdir()

        # Words of the text and indices to map the current location in the text to a word.
        # Both are used to save the word in which typos occur.
        self.word_list, self.word_indices = index_text_to_words(self.full_text)

        # Text on the left side of the curser (already typed), with formatting for rich rendering
        self.formatted_input = ""
        # Full text, with formatting for rich rendering
        self.formatted_text = ""

        # Left and right tags for rich rendering
        self.correct_style = ["[bold green]", "[/bold green]"]
        self.current_style = ["[black on white]", "[/black on white]"]
        self.incorrect_style = ["[bold red]", "[/bold red]"]

        # Current location in the full text
        self.current_location = 0

        # The formatted text will contain information about rendering like [bold green].
        # To correctly remove characters from the formatted text, we have to remember where in the string a new text character starts.
        # To delete more than one character in sequence, we keep a list of these locations, and pop off from the end.
        self.delete_locations = []

        # A class for storing information about what was typed in which context
        self.session_database = SessionDatabase()

        # Counters to calculate the accuracy
        self.hits = 0
        self.misses = 0

        await self.bind("escape", "quit", "Quit")

    async def on_mount(self) -> None:
        """Called when application mode is ready."""

        self.info = InfoBox()
        self.text = TextBox(self.full_text)
        self.gutter = GutterBox()
        grid = await self.view.dock_grid(edge="left", name="left")

        grid.add_column(fraction=1, name="left")
        grid.add_column(fraction=5, name="right")

        grid.add_row(fraction=5, name="top")
        grid.add_row(fraction=1, name="bottom")

        grid.add_areas(
            info_area="left, top-start|bottom-end",
            text_area="right, top",
            gutter_area="right, bottom",
        )

        grid.place(
            info_area=self.info,
            text_area=self.text,
            gutter_area=self.gutter,
        )

    async def on_key(self, event: events.Key) -> None:
        """Called when a key is pressed."""

        current_char = self.full_text[self.current_location]
        current_input = str(event.key)

        # handle special characters
        if current_input == "ctrl+h":
            # backspace
            self.current_location = max(self.current_location - 1, 0)
            try:
                delete_location = self.delete_locations.pop()
            except IndexError:
                delete_location = 0
            self.formatted_input = self.formatted_input[:delete_location]

        else:
            self.save_entry(current_input, current_char)

            if current_input == current_char:
                # correct input
                formatted_char = surround_with_style(self.correct_style,
                                                     current_char)
                self.hits += 1
            else:
                # incorrect input
                if current_char.isspace():
                    # since we cannot color in a space, we replace it with an underscore
                    current_char = "_"
                formatted_char = surround_with_style(self.incorrect_style,
                                                     current_char)
                self.misses += 1

            # new location to jump to, when deleting text is the current lenght of the text, before adding the new formatted char
            self.delete_locations.append(max(len(self.formatted_input), 0))
            self.formatted_input += formatted_char
            self.current_location += 1

        self.formatted_text = self.assemble_formatted_text()

        await self.text.update(self.formatted_text)
        await self.gutter.update(f"<<{current_char}>>    <<{current_input}>>")
        await self.info.update(
            accuracy=self.get_accuracy(),
            speed=self.get_speed(),
            progress=self.get_progress(),
        )

        if self.current_location >= self.text_length:
            await self.exit()

    def assemble_formatted_text(self) -> str:
        """Return a renderable string based on the previous input and the remaining text."""
        try:
            return self.formatted_input \
                   + surround_with_style(self.current_style, self.full_text[self.current_location]) \
                   + self.full_text[self.current_location + 1:]
        except IndexError:
            return self.formatted_input

    def save_entry(
        self,
        current_input: str,
        current_char: str,
    ) -> None:
        """Save information about what as put in, what was expected, the current word, the characters location in the word, and a time stamp."""

        current_word_index = self.word_indices[self.current_location]
        current_search_location = self.current_location

        while self.word_indices[current_search_location] == current_word_index:
            current_search_location -= 1

        location_in_word = self.current_location - current_search_location - 1

        self.session_database.entries.append(
            SessionDatabaseEntry(
                input=current_input,
                text=current_char,
                correct=current_input == current_char,
                word=self.word_list[current_word_index],
                location_in_word=location_in_word,
                time=time(),
            ))

    def get_progress(self) -> str:
        """Percentage of typed text."""
        return f"{(self.current_location/self.text_length)*100:.1f}%"

    def get_accuracy(self) -> str:
        """Percentage of hits in typed text."""
        try:
            return f"{(self.hits/(self.hits+self.misses))*100:.1f}%"
        except ZeroDivisionError:
            return "100%"

    def get_speed(self) -> str:
        """Characters per minute since start."""
        try:
            start = self.session_database.entries[0].time
            return f"{int(self.current_location/(time() - start)*60)} cpm"
        except IndexError:
            return "0 cpm"

    async def exit(self) -> None:
        """What to do on exit."""
        database_save_path = self.data_dir / f"{self.session_database.date}_session_database.pkl"
        with open(str(database_save_path), "wb") as output_file:
            pickle.dump(self.session_database, output_file)
        await self.shutdown()

    async def action_quit(self) -> None:
        """What to do on quit."""
        database_save_path = self.data_dir / f"{self.session_database.date}_session_database.pkl"
        with open(str(database_save_path), "wb") as output_file:
            pickle.dump(self.session_database, output_file)
        await self.shutdown()


def surround_with_style(style: List[str], text: str) -> str:
    """Take a text and surround it with a rich text style like [bold red] text [/bold red], stored in a list."""
    return style[0] + text + style[1]


if __name__ == "__main__":
    num_words_in_text = 20
    exploration_percentage = 0.2
    word_file_path = Path("/usr/share/dict/words")
    data_dir = Path("data")
    srs_database_name = "srs_database.pkl"

    update_srs_database_from_latest_session(data_dir=data_dir, srs_database_name=srs_database_name)
    srs_database = read_database(data_dir / srs_database_name)

    sampled_ngrams = sample_ngrams_from_srs_database(srs_database, int(num_words_in_text*(1-exploration_percentage)))

    assert word_file_path.is_file(), f"Cannot find {word_file_path.absolute()}."

    with open(str(word_file_path.absolute()), "r") as word_file:
        WORDS = word_file.read().splitlines()

    relevant_words = get_words_with_ngrams(sampled_ngrams, WORDS)

    text_words = []

    while len(sampled_ngrams) > 0:
        ngram = sampled_ngrams.pop()
        ngram_word_list = [ngram_word for ngram_word in relevant_words if ngram in ngram_word]
        # if there is no word matching the ngram, add the ngram itself
        if len(ngram_word_list) == 0:
            if len(ngram) > 0:
                text_words.append(ngram)
        else:
            word = np.random.choice(ngram_word_list)
            text_words.append(word)

    num_missing_words = num_words_in_text - len(text_words)
    if num_missing_words > 0:
        text_words.extend(np.random.choice(WORDS, size=num_missing_words))


    full_text = " ".join(text_words)

    SrsTyperApp.run(full_text=full_text)
