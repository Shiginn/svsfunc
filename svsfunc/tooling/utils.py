__all__ = ["UtilsTooling"]

import os
from shutil import rmtree
from typing import Any

from vardautomation import logger, make_comps
from vstools import Keyframes, SceneChangeMode

from ..indexer import LSMAS
from ..utils import write_props
from .base import BaseEncoder


class UtilsTooling(BaseEncoder):
    """Set of useful functions"""

    def make_comp(self, num_frames: int = 100, **comp_args: Any) -> None:
        """
        Make comp with source, filtered and encoded file. Will use lossless intermediate if the file exists.

        :param num_frames:      Number of comp to generate.
        :param delete_index:    Delete index file generated when indexing `file.name_file_final` and/or lossless clip.
                                Defaults to True.
        :param comp_args:       Additional paramters to be passed to :py:func:`make_comp`
        """
        logger.info("Generating comps")

        args: dict[str, Any] = dict(num=num_frames, force_bt709=True)
        args |= comp_args

        if os.path.isdir("comps"):
            rmtree("comps")
            logger.info("Removed old comps folder")

        idx = LSMAS(cache=False)

        lossless = self.file.name_clip_output.append_stem("_lossless.mkv")
        filtered = idx(lossless.to_str()) if lossless.exists() else self.clip
        make_comps({
            "source": write_props(self.file.clip_cut, clip_name="Source"),
            "filtered": write_props(filtered, clip_name="Filtered"),
            "encode": write_props(idx(self.file.name_file_final.to_str()), clip_name="Encode"),
        }, **args)


    def generate_keyframes(self, mode: SceneChangeMode = SceneChangeMode.WWXD_SCXVID_UNION) -> None:
        """
        Generate Aegisub compatible keyframes.

        :param mode:            Scene change detection mode. Defaults to WWXD or SCXVID.
        :param delete_index:    Delete index file generated when indexing `file.name_file_final`. Defaults to True.
        """
        if self.file.name_file_final.exists():
            logger.info("Generating keyframes from encoded file")
            clip = LSMAS(cache=False).index(self.file.name_file_final.to_str())
        else:
            logger.info("Generating keyframes from filtered clip")
            clip = self.clip

        kf = Keyframes.from_clip(clip, mode)

        with open(f"{self.file.name_file_final.to_str()}_keyframes.txt", "w") as f:
            f.write("# WWXD log file, using qpfile format\n\n")
            f.writelines([f"{frame} I -1\n" for frame in kf[1:]])
