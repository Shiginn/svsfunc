from pathlib import Path
from typing import Callable, TypeAlias, TypeVar

from vardautomation import (
    FFV1, X264, X265, Eac3toAudioExtracter, EztrimCutter, FFmpegAudioExtracter, FileInfo, FileInfo2, FlacEncoder,
    MatroskaXMLChapters, MKVAudioExtracter, NVEncCLossless, OGMChapters, OpusEncoder, PassthroughAudioEncoder,
    PassthroughCutter, QAACEncoder, ScipyCutter, SoxCutter
)
from vstools import vs

__all__ = [
    "FileInfoT", "IndexedT", "VSIdxFunc",
    "EncoderTypes",
]


FileInfoT = TypeVar("FileInfoT", FileInfo, FileInfo2)
IndexedT = TypeVar("IndexedT", vs.VideoNode, FileInfo, FileInfo2)
VSIdxFunc: TypeAlias = Callable[[str | Path], vs.VideoNode]


class EncoderTypes:
    class Video:
        Encoder: TypeAlias = X264 | X265
        LosslessEncoder: TypeAlias = FFV1 | NVEncCLossless

    class Audio:
        Extracter: TypeAlias = FFmpegAudioExtracter | MKVAudioExtracter | Eac3toAudioExtracter
        Cutter: TypeAlias = EztrimCutter | SoxCutter | ScipyCutter | PassthroughCutter
        Encoder: TypeAlias = FlacEncoder | OpusEncoder | QAACEncoder | PassthroughAudioEncoder

    class Chapter:
        Format: TypeAlias = MatroskaXMLChapters | OGMChapters
