from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from vsmuxtools import Trim, src_file
from vstools import vs

from .abstract import Indexer
from .video import VideoIndexer

__all__ = ["SrcFile"]


@dataclass
class SrcFile(Indexer[src_file]):
    """src_file from vs-muxtools"""
    _index_func = src_file

    trim: Trim | None = None
    idx: VideoIndexer | Callable[[str], vs.VideoNode] | None = None
    force_lsmas: bool = False
