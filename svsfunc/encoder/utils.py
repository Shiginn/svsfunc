__all__ = ["UtilsTooling"]

import os
from functools import partial
from shutil import rmtree
from typing import Any, Dict, cast

import vapoursynth as vs
from lvsfunc import find_scene_changes
from lvsfunc.types import SceneChangeMode
from vardautomation import logger, make_comps

from .base import BaseEncoder

core = vs.core


class UtilsTooling(BaseEncoder):

    def make_comp(self, num_frames: int = 100, **comp_args: Any) -> None:
        """
        Make comp with source, filtered and encoded file. Will use lossless intermediate if the file exists.

        :param num_frames:  Number of comp to generate.
        :param comp_args:   Additional paramters to be passed to :py:func:`make_comp`
        """
        logger.info("Generating comps")

        args: Dict[str, Any] = dict(num=num_frames, force_bt709=True)
        args |= comp_args

        if os.path.isdir("comps"):
            rmtree("comps")
            logger.info("Removed old comps folder")


        def _write_props(clip: vs.VideoNode) -> vs.VideoNode:
            def _get_props(n: int, f: vs.VideoFrame, clip: vs.VideoNode) -> vs.VideoNode:
                txt = f"Frame Info:\nFrame Number: {n}"

                pict_type = cast(bytes | None, f.props.get("_PictType"))
                if (pict_type):
                    txt += f"\nPicture Type: {pict_type.decode()}"

                return clip.text.Text(txt, 7, 1)

            f = partial(_get_props, clip=clip)
            return clip.std.FrameEval(f, prop_src=clip)


        lossless = self.file.name_clip_output.append_stem("_lossless.mkv")
        filtered = core.lsmas.LWLibavSource(lossless.to_str()) if lossless.exists() else self.clip
        make_comps(
            {
                "source": _write_props(self.file.clip_cut),
                "filtered": _write_props(filtered),
                "encode": _write_props(core.lsmas.LWLibavSource(self.file.name_file_final.to_str())),
            },
            **args
        )


    def generate_keyframes(
        self, mode: SceneChangeMode = SceneChangeMode.WWXD_SCXVID_UNION, delete_index: bool = True
    ) -> None:
        """
        Generate Aegisub compatible keyframes.

        :param mode:            Scene change detection mode. Defaults to WWXD or SCXVID.
        :param delete_index:    Delete index file generated when indexing `file.name_file_final`. Defaults to True.
        """
        if self.file.name_file_final.exists():
            logger.info("Generating keyframes from encoded file")
            clip = core.lsmas.LWLibavSource(self.file.name_file_final.to_str())
        else:
            logger.info("Generating keyframes from filtered clip")
            clip = self.clip

        kf = find_scene_changes(clip, mode)

        with open(f"{self.file.name_file_final.to_str()}_keyframes.txt", "w") as f:
            f.write("# WWXD log file, using qpfile format\n\n")
            f.writelines([f"{frame} I -1\n" for frame in kf[1:]])

        if delete_index:
            os.remove(f"{self.file.name_file_final.to_str()}.lwi")
