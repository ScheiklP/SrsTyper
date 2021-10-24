from typing import List
from time import time

from textual.app import App
from textual import events

from widgets.box import TextBox, InfoBox, GutterBox


full_text =   "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce sit amet nibh et tellus maximus semper. Proin efficitur est sed erat euismod viverra. Morbi pulvinar eget ligula nec volutpat. Integer vitae quam ac ipsum varius mollis quis at mi. Nulla lacinia vulputate blandit. Nullam ac massa sodales, porttitor purus id, tristique nisi. Aliquam sollicitudin quam pretium diam faucibus, eget fringilla lectus vehicula."

class SrsTyperApp(App):
    """Terminal application for personalized typing practice based on the Spaced Repetition Sysem (SRS)."""

    async def on_load(self, _: events.Load) -> None:
        """Calleb before entering application mode."""

        # Raw text that is to be typed in the session.
        self.full_text = full_text
        self.text_length = len(self.full_text)
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

        # A list for storing information about what was typed in which context
        self.entries = []

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


    async def on_key(self, event) -> None:
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
            self.save_entry(current_input, current_char, surround_width=10)

            if current_input == current_char:
                # correct input
                formatted_char = surround_with_style(self.correct_style, current_char)
                self.hits += 1
            else:
                # incorrect input
                if current_char.isspace():
                    # since we cannot color in a space, we replace it with an underscore
                    current_char = "_"
                formatted_char = surround_with_style(self.incorrect_style, current_char)
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

    def assemble_formatted_text(self) -> str:
        """Return a renderable string based on the previous input and the remaining text."""
        try:
            return self.formatted_input \
                   + surround_with_style(self.current_style, self.full_text[self.current_location]) \
                   + self.full_text[self.current_location + 1:]
        except IndexError:
            return self.formatted_input


    def save_entry(self, current_input: str, current_char: str, surround_width) -> None:
        """Save information about what as put in and what was expected. Also includes the context based on the surrounding text."""
        self.entries.append(dict(
                    input=current_input,
                    text=current_char,
                    surrounding=self.full_text[max(self.current_location-int(surround_width/2), 0):min(self.current_location+int(surround_width/2), len(self.full_text))],
                    time=time(),
                    ))

    def get_progress(self) -> str:
        return f"{(self.current_location/self.text_length)*100:.1f}%"

    def get_accuracy(self) -> str:
        try:
            return f"{(self.hits/(self.hits+self.misses))*100:.1f}%"
        except ZeroDivisionError:
            return "100%"

    def get_speed(self) -> str:
        try:
            start = self.entries[0]["time"]
            return f"{int(self.current_location/(time() - start)*60)} cpm"
        except IndexError:
            return "0 cpm"



def surround_with_style(style: List[str], text: str) -> str:
    """Take a text and surround it with a rich text style like [bold red] text [/bold red], stored in a list."""
    return style[0] + text + style[1]

SrsTyperApp().run(log="textual.log")

