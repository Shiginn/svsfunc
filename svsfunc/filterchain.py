
from abc import ABC, abstractmethod
from typing import Callable

from vstools import set_output, vs, vs_object

__all__ = ["BaseFilterchain"]


class BaseFilterchain(vs_object, ABC):
    """Abstract base class that can be used to build a filterchain"""

    preview_clips: dict[str, vs.VideoNode] | None = None

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


    def set_outputs(self, preview_func: Callable[[vs.VideoNode], vs.VideoNode] | None = None) -> None:
        """
        Output every clip in the list of preview clips.

        :param preview_func:    Function to apply to every clip before outputting (e.g. PlaneStat, stack_planes, ...)
        """
        if preview_func is not None and not callable(preview_func):
            raise TypeError(f"{self.__class__.__name__}.set_outputs: preview_func must be callable.")

        if self.preview_clips is None:
            raise ValueError(f"{self.__class__.__name__}.set_outputs: no output set.")

        for output_name, output in self.preview_clips.items():
            if preview_func is not None:
                output = preview_func(output)

            set_output(output, output_name)


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

    def __vs_del__(self, core_id: int) -> None:
        if self.preview_clips is None:
            return

        for value in self.preview_clips.values():
            del value

        self.preview_clips.clear()
