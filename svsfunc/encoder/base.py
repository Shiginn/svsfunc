__all__ = ["BaseEncoder"]

import vapoursynth as vs
from vardautomation import FileInfo


class BaseEncoder:
    file: FileInfo
    clip: vs.VideoNode

    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        self.file = file
        self.clip = clip
