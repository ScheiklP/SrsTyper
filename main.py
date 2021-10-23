from typing import List
from textual.app import App

from widgets.box import TextBox, InfoBox, GutterBox
from textual import events


full_text =   "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce sit amet nibh et tellus maximus semper. Proin efficitur est sed erat euismod viverra. Morbi pulvinar eget ligula nec volutpat. Integer vitae quam ac ipsum varius mollis quis at mi. Nulla lacinia vulputate blandit. Nullam ac massa sodales, porttitor purus id, tristique nisi. Aliquam sollicitudin quam pretium diam faucibus, eget fringilla lectus vehicula."

class SrsTyperApp(App):
    """Terminal application for personalized typing practice based on the Spaced Repetition Sysem (SRS)."""

    async def on_load(self, _: events.Load) -> None:

        self.full_text = full_text
        self.formatted_text = ""
        self.formatted_input = ""

        self.correct_style = ["[bold green]", "[/bold green]"]
        self.current_style = ["[black on white]", "[/black on white]"]
        self.incorrect_style = ["[bold red]", "[/bold red]"]
        self.current_location = 0
        self.delete_locations = []
        self.inputs = []
        self.entries = []

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

        current_char = self.full_text[self.current_location]

        current_input = str(event.key)
        self.inputs.append(current_input)

        if current_input == current_char:
            # correct input
            self.save_entry(current_input, current_char, surround_width=10)
            formatted_char = surround_with_style(self.correct_style, current_char)
            self.delete_locations.append(max(len(self.formatted_input), 0))
            self.formatted_input += formatted_char
            self.current_location += 1

        elif current_input == "ctrl+h":
            # backspace
            self.current_location = max(self.current_location - 1, 0)
            try:
                delete_location = self.delete_locations.pop()
            except IndexError:
                delete_location = 0
            self.formatted_input = self.formatted_input[:delete_location]

        else:
            # incorrect input
            self.save_entry(current_input, current_char, surround_width=10)
            if current_char.isspace():
                current_char = "_"
            formatted_char = surround_with_style(self.incorrect_style, current_char)
            self.delete_locations.append(max(len(self.formatted_input), 0))
            self.formatted_input += formatted_char
            self.current_location += 1


        self.formatted_text = self.format_text()


        await self.text.update(self.formatted_text)
        await self.gutter.update(f"<<{current_char}>>    <<{current_input}>>")

    def format_text(self) -> str:
        """Return a renderable string based on the previous input and the remaining text."""
        return self.formatted_input \
               + surround_with_style(self.current_style, self.full_text[self.current_location]) \
               + self.full_text[self.current_location + 1:]


    def save_entry(self, current_input: str, current_char: str, surround_width) -> None:
        """Save information about what as put in and what was expected. Also includes the context based on the surrounding text."""
        self.entries.append(dict(
                    input=current_input,
                    text=current_char,
                    surrounding=self.full_text[max(self.current_location-int(surround_width/2), 0):min(self.current_location+int(surround_width/2), len(self.full_text))],
                    ))

def surround_with_style(style: List[str], text: str) -> str:
    """Take a text and surround it with a rich text style like [bold red] text [/bold red], stored in a list."""
    return style[0] + text + style[1]

SrsTyperApp().run(log="textual.log")

