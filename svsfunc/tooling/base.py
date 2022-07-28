__all__ = ["BaseEncoder"]

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
