
from abc import ABC, abstractmethod
from typing import Dict

import vapoursynth as vs

__all__ = ["BaseFiltering"]


class BaseFiltering(ABC):
    filtersteps_clips: Dict[str, vs.VideoNode] | None = None

    @abstractmethod
    def filter(self) -> vs.VideoNode:
        ...


    def set_output(self, clip: vs.VideoNode, name: str | None = None) -> None:
        """
        Add a VideoNode to the list of filtersteps.

        :param clip:    Clip to output. If None, name will be `Video Node x`.
        :param name:    Name of the clip.
        """
        if name is None:
            name = f"Video Node {1 if self.filtersteps_clips is None else len(self.filtersteps_clips) + 1}"

        input = {name: clip}
        self.filtersteps_clips = input if self.filtersteps_clips is None else self.filtersteps_clips | input


    def preview(self, name_pos: int = 8, display_props: int | None = None, font_scaling: int = 1) -> None:
        """
        Preview every clip in the list of filtersteps.

        :param name_pos:        Position of the name of the clip (0 = disable). Default to 8 (top-middle)
        :param display_props:   Position of the frame-props of the clip. Default to disable.
        :param font_scaling:    Scaling of the font used to write name and frame_props. Defaults to 1.
        """

        if self.filtersteps_clips is None:
            raise ValueError("BaseFiltering: no output set.")

        for i, (output_name, output) in enumerate(self.filtersteps_clips.items()):
            if display_props:
                output = output.text.FrameProps(alignment=display_props, scale=font_scaling)

            if name_pos:
                output = output.text.Text(output_name, name_pos, font_scaling)

            output = output.std.SetFrameProp("Name", data=output_name)
            output.set_output(i)


    def get_clip(self, clip_name: str | int) -> vs.VideoNode:
        """
        Get a clip from the filtersteps.

        :param clip_name:   Name of the clip. If int, will get `Video Node x`.

        :return:            Requested clip.
        """

        if self.filtersteps_clips is None:
            raise ValueError("BaseFiltering: no output set.")

        if isinstance(clip_name, int):
            clip_name = f"Video Node {clip_name}"

        clip = self.filtersteps_clips.get(clip_name)
        if clip is None:
            raise ValueError("BaseFiltering: requested clip does not exist.")

        return clip
