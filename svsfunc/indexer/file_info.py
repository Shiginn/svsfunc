from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Union

from vardautomation import FileInfo as FI
from vardautomation import FileInfo2 as FI2
from vardautomation import AnyPath, DuplicateFrame, Preset, PresetBD, PresetBDWAV64, Trim, VPath, VPSIdx

from .abstract import Indexer
from .video import VideoIndexer


FileInfoIndexer = Union[Indexer[FI], Indexer[FI2]]


@dataclass
class _FileInfoIndexer:
    trims_or_dfs: list[Trim | DuplicateFrame] | Trim | None = None
    idx: VideoIndexer | VPSIdx | None = None
    workdir: AnyPath = field(default_factory=lambda: VPath().cwd())
    preset: Preset | Sequence[Preset] = field(default_factory=lambda: [PresetBD, PresetBDWAV64])


@dataclass
class FileInfo(_FileInfoIndexer, Indexer[FI]):
    """FileInfo from Vardautomation"""
    _index_func = FI


@dataclass
class FileInfo2(_FileInfoIndexer, Indexer[FI2]):
    """FileInfo2 from Vardautomation"""
    _index_func = FI2
