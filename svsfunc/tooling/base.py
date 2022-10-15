__all__ = ["BaseEncoder"]

import inspect

import vapoursynth as vs
from vardautomation import FileInfo


class BaseEncoder:
    """
    Base class for all Tooling and Encoder

    :param file:    FileInfo object.
    :param clip:    Clip to encode.
    """

    file: FileInfo
    clip: vs.VideoNode

    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip


    def get_offset(self) -> int:
        """
        Get offset based on FileInfo trims
        """
        trims = self.file.trims_or_dfs

        if trims is None:
            offset = 0
        elif isinstance(trims, tuple):
            offset = trims[0]
        elif isinstance(trims, list) and isinstance(trims[0], tuple):
            offset = trims[0][0]

        return 0 if offset is None else offset * -1


    @staticmethod
    def get_func_name() -> str:
        return inspect.stack()[1][3]
