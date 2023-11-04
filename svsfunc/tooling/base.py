from vardautomation import FileInfo
from vstools import vs

__all__ = ["BaseEncoder"]


class BaseEncoder:
    """Base class for all Tooling and Encoder"""

    file: FileInfo
    clip: vs.VideoNode

    def __init__(self, file: FileInfo, clip: vs.VideoNode) -> None:
        """
        Set file and clip that will be used by the encoder.

        :param file: FileInfo object.
        :param clip: Clip to encode.
        """
        import warnings
        warnings.warn(
            "svsfunc.Encoder is deprecated and will be removed in future versions. Please use vs-muxtools instead.",
            category=DeprecationWarning
        )

        self.file = file
        self.clip = clip


    @staticmethod
    def get_offset(file: FileInfo) -> int:
        """
        Get offset based on FileInfo trims
        """
        trims = file.trims_or_dfs

        if trims is None:
            offset: int | None = 0
        elif isinstance(trims, tuple):
            offset = trims[0]
        elif isinstance(trims, list) and isinstance(trims[0], tuple):
            offset = trims[0][0]

        return 0 if offset is None else offset * -1


    @staticmethod
    def get_offset_ms(file: FileInfo, clip: vs.VideoNode) -> int:
        """
        Get offset in ms from FileInfo trims
        """
        return round(BaseEncoder.get_offset(file) * (1000 / clip.fps))
