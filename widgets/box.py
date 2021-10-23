from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.console import RenderableType

from textual.widget import Widget


class TextBox(Widget):
    def __init__(
        self,
        renderable: RenderableType,
        name: str | None = None,
    ) -> None:
        super().__init__(name)
        self.renderable = renderable

    def render(self) -> RenderableType:
        renderable = self.renderable

        return Panel(
            Align.center(renderable),
            title="Practice Text",
            border_style="green",
            box=box.ROUNDED,
        )

    async def update(self, renderable: RenderableType) -> None:
        self.renderable = renderable
        self.refresh()


class InfoBox(Widget):
    def __init__(
        self,
        name: str | None = None,
    ) -> None:
        super().__init__(name)
        self.accuracy = 100
        self.speed = 0
        self.progress = 0

    def render(self) -> RenderableType:

        return Panel(
                Align.left(f"Speed: {self.speed}\nAccuracy: {self.accuracy}\nProgress: {self.progress}"),
            title="Info",
            border_style="blue",
            box=box.ROUNDED,
        )

    async def update(self, accuracy: RenderableType, speed: RenderableType, progress: RenderableType) -> None:
        self.progress = progress
        self.speed = speed
        self.accuracy = accuracy
        self.refresh()


class GutterBox(Widget):
    def __init__(
        self,
        name: str | None = None,
    ) -> None:
        super().__init__(name)
        self.renderable = ""

    def render(self) -> RenderableType:

        return Panel(
                Align.center(self.renderable),
            title="Gutter",
            border_style="red",
            box=box.ROUNDED,
        )

    async def update(self, renderable: RenderableType) -> None:
        self.renderable = renderable
        self.refresh()
