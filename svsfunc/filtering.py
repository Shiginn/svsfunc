
from abc import ABC, abstractmethod
from typing import Callable, Dict

from vstools import vs

__all__ = ["BaseFiltering"]


class BaseFiltering(ABC):
    """Abstract base class that can be used to build a filterchain"""

    preview_clips: Dict[str, vs.VideoNode] | None = None

    @abstractmethod
    def filter(self) -> vs.VideoNode:
        ...


    def add_preview(self, clip: vs.VideoNode, name: str | None = None) -> None:
        """
        Add a VideoNode to the list of preview clips.

        :param clip:    Clip to output.
        :param name:    Name of the clip. If None, name will be `Video Node x`.
        """
        if name is None:
            name = f"Video Node {1 if self.preview_clips is None else len(self.preview_clips) + 1}"

        preview = {name: clip}
        self.preview_clips = preview if self.preview_clips is None else self.preview_clips | preview


    def set_outputs(
        self,
        name_pos: int = 8,
        display_props: int | None = None,
        font_scaling: int = 1,
        preview_func: Callable[[vs.VideoNode], vs.VideoNode] | None = None
    ) -> None:
        """
        Output every clip in the list of preview clips.

        :param name_pos:        Position of the name of the clip (0 = disable). Default to 8 (top-middle)
        :param display_props:   Position of the frame-props of the clip. Default to disable.
        :param font_scaling:    Scaling of the font used to write name and frame_props. Defaults to 1.
        :param preview_func:    Function to apply to every clip before outputting (e.g. PlaneStat, stack_planes, ...)
        """

        if preview_func is not None and not callable(preview_func):
            raise TypeError(f"{self.__class__.__name__}.set_outputs: preview_func must be callable.")

        if self.preview_clips is None:
            raise ValueError(f"{self.__class__.__name__}.set_outputs: no output set.")

        for i, (output_name, output) in enumerate(self.preview_clips.items()):
            if preview_func is not None:
                output = preview_func(output)

            if display_props:
                output = output.text.FrameProps(alignment=display_props, scale=font_scaling)

            if name_pos:
                output = output.text.Text(output_name, name_pos, font_scaling)

            output = output.std.SetFrameProp("Name", data=output_name)
            output.set_output(i)


    def get_clip(self, clip_name: str | int) -> vs.VideoNode:
        """
        Get a clip from the list of preview clips.

        :param clip_name:   Name of the clip. If int, will get `Video Node x`.

        :return:            Requested clip.
        """

        if self.preview_clips is None:
            raise ValueError(f"{self.__class__.__name__}.get_clip: no output set.")

        if isinstance(clip_name, int):
            clip_name = f"Video Node {clip_name}"

        clip = self.preview_clips.get(clip_name)
        if clip is None:
            raise ValueError(f"{self.__class__.__name__}.get_clip: requested clip does not exist.")

        return clip
