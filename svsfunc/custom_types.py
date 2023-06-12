from __future__ import annotations

from pathlib import Path
from typing import Literal, TypeAlias, TypeVar, Union

from vardautomation import (
    FFV1, X264, X265, Eac3toAudioExtracter, EztrimCutter, FFmpegAudioExtracter, FileInfo, FileInfo2, FlacEncoder,
    MatroskaXMLChapters, MKVAudioExtracter, NVEncCLossless, OGMChapters, OpusEncoder, PassthroughAudioEncoder,
    PassthroughCutter, QAACEncoder, ScipyCutter, SoxCutter
)
from vstools import vs

__all__ = [
    "FileInfoT", "HoldsVideoNodeT", "IndexedT",
    "PathLike", "FramePropKey", "NCRange",
    "EncoderTypes",
]


FileInfoT = TypeVar("FileInfoT", FileInfo, FileInfo2)
IndexedT = TypeVar("IndexedT", vs.VideoNode, vs.AudioNode, FileInfo, FileInfo2)
HoldsVideoNodeT = TypeVar("HoldsVideoNodeT", vs.VideoNode, FileInfo, FileInfo2)

PathLike: TypeAlias = Union[str, Path]

FramePropKey: TypeAlias = Literal["_PictType", "_ChromaLocation", "_Primaries", "_Transfer", "_Matrix", "_ColorRange"]

NCRange: TypeAlias = dict[Union[int, tuple[int, int]], Union[PathLike, vs.VideoNode, None]]


class EncoderTypes:
    class Video:
        Encoder: TypeAlias = Union[X264, X265]
        LosslessEncoder: TypeAlias = Union[FFV1, NVEncCLossless]

    class Audio:
        Extracter: TypeAlias = Union[FFmpegAudioExtracter, MKVAudioExtracter, Eac3toAudioExtracter]
        Cutter: TypeAlias = Union[EztrimCutter, SoxCutter, ScipyCutter, PassthroughCutter]
        Encoder: TypeAlias = Union[FlacEncoder, OpusEncoder, QAACEncoder, PassthroughAudioEncoder]

    class Chapter:
        Format: TypeAlias = Union[MatroskaXMLChapters, OGMChapters]
