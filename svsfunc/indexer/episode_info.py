from __future__ import annotations

from pathlib import Path
from typing import Any, Generic

from vsmuxtools import src_file
from vstools import vs, initialize_clip

from ..custom_types import HoldsVideoNodeT
from ..utils import ensure_path, trim
from .abstract import Indexer, PathLike
from .video import LSMAS

__all__ = ["EpisodeInfo"]


class EpisodeInfo(Generic[HoldsVideoNodeT]):
    """Class that represent an indexed episode with episode number and optional OP/ED ranges."""
    indexed: HoldsVideoNodeT

    path: Path
    ep_num: int
    op_range: tuple[int, int] | None = None
    ed_range: tuple[int, int] | None = None
    ncop: vs.VideoNode | None
    nced: vs.VideoNode | None


    def __init__(
        self: "EpisodeInfo[HoldsVideoNodeT]", path: PathLike, ep_num: int = -1,
        op_range: tuple[int, int] | None = None, ed_range: tuple[int, int] | None = None,
        ncop: vs.VideoNode | None = None, nced: vs.VideoNode | None = None,
        indexer: Indexer[HoldsVideoNodeT] = LSMAS(), **indexer_overrides: Any
    ) -> None:
        self.path = ensure_path(path, "EpisodeInfo")
        self.indexed = indexer.index(self.path, **indexer_overrides)

        self.ep_num = ep_num
        self.op_range = op_range
        self.ed_range = ed_range
        self.ncop = ncop
        self.nced = nced


    def get_op(self, clip: vs.VideoNode | None = None) -> vs.VideoNode:
        """
        Trims the episode clip to only keep the range that corresponds to the OP.

        :param clip: Clip to trim OP from. Indexed clip is used if None

        :raises ValueError: If `self.op_range` is None.

        :return: OP clip
        """
        if self.op_range is None:
            raise ValueError("EpisodeInfo.get_op: cannot get OP clip if op_range is None.")

        return trim(clip or self.clip, self.op_range)


    def get_ed(self, clip: vs.VideoNode | None = None) -> vs.VideoNode:
        """
        Trims the episode clip to only keep the range that corresponds to the ED.

        :param clip: Clip to trim ED from. Indexed clip is used if None

        :raises ValueError: If `self.ed_range` is None.

        :return: ED clip
        """
        if self.ed_range is None:
            raise ValueError("EpisodeInfo.get_ed: cannot get ED clip if ed_range is None.")

        return trim(clip or self.clip, self.ed_range)


    def get_ncop(self) -> vs.VideoNode:
        """
        Get NCOP and raise an exception if it is not set.

        :raises ValueError:     If NCOP is not set.

        :return:                NCOP clip
        """
        if self.ncop is None:
            raise ValueError("EpiosdeInfo.get_ncop: no NCOP set.")

        return self.ncop


    def get_nced(self) -> vs.VideoNode:
        """
        Get NCED and raise an exception if it is not set.

        :raises ValueError:     If NCED is not set.

        :return:                NCED clip
        """
        if self.nced is None:
            raise ValueError("EpiosdeInfo.get_nced: no NCED set.")

        return self.nced


    def ep_num_str(self, padding: int = 2) -> str:
        """
        Generate a padded string of the episode number

        :param padding:     Length of the string, defaults to 2
        :return:            Padded string
        """
        return str(self.ep_num).zfill(padding)


    @property
    def clip(self) -> vs.VideoNode:
        """
        Indexed clip

        :return:    VideoNode object
        """
        return self.indexed.src_cut if isinstance(self.indexed, src_file) else self.indexed  # type: ignore


    def clip_init(self, **kwargs: Any) -> vs.VideoNode:
        """
        Initializes indexed clip using vs-tools' :py:func:`initialize_clip`.

        :return:    VideoNode object
        """

        return initialize_clip(self.clip, **kwargs)


    @property
    def src_file(self: "EpisodeInfo[src_file]") -> src_file:
        """
        Get src_file object from the indexed file

        :raises TypeError:  If indexer used is not SrcFile
        :return:            FileInfo object
        """
        if not isinstance(self.indexed, src_file):
            raise TypeError("EpisodeInfo.src_file: This property is only available if the indexer is SrcFile")

        return self.indexed
