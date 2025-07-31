from __future__ import annotations

from typing import Any, Generic

from vsmuxtools import src_file
from vstools import initialize_clip, vs

from .custom_types import HoldsVideoNodeT
from .utils import trim

__all__ = ["EpisodeInfo"]


class EpisodeInfo(Generic[HoldsVideoNodeT]):
    """Class that represent an indexed episode with episode number and optional OP/ED ranges + NCOP/NCED."""

    source: HoldsVideoNodeT
    ep_num: int
    op_range: tuple[int, int] | None = None
    ed_range: tuple[int, int] | None = None
    ncop: vs.VideoNode | None
    nced: vs.VideoNode | None


    def __init__(
        self, source: HoldsVideoNodeT, ep_num: int = -1,
        op_range: tuple[int, int] | None = None, ed_range: tuple[int, int] | None = None,
        ncop: vs.VideoNode | None = None, nced: vs.VideoNode | None = None,
    ) -> None:
        self.source = source
        self.ep_num = ep_num
        self.op_range = op_range
        self.ed_range = ed_range
        self.ncop = ncop
        self.nced = nced


    def get_op(self, clip: vs.VideoNode | None = None) -> vs.VideoNode:
        """
        Trims the episode clip to only keep the range that corresponds to the OP.

        :param clip: Clip to trim OP from. :py:func:`EpisodeInfo.src_cut` is used if None

        :raises ValueError: If `self.op_range` is None.

        :return: OP clip
        """
        if self.op_range is None:
            raise ValueError("EpisodeInfo.get_op: cannot get OP clip if op_range is None.")

        return trim(clip or self.src_cut, self.op_range)


    def get_ed(self, clip: vs.VideoNode | None = None) -> vs.VideoNode:
        """
        Trims the episode clip to only keep the range that corresponds to the ED.

        :param clip: Clip to trim ED from. :py:func:`EpisodeInfo.src_cut` is used if None

        :raises ValueError: If `self.ed_range` is None.

        :return: ED clip
        """
        if self.ed_range is None:
            raise ValueError("EpisodeInfo.get_ed: cannot get ED clip if ed_range is None.")

        return trim(clip or self.src_cut, self.ed_range)


    def get_ncop(self, trim_ncop: bool = True) -> vs.VideoNode:
        """
        Get NCOP and raise an exception if it is not set.

        :param trim_ncop:         Trim NCOP to match frame number of the non-NC OP (needs op_range to be set).
                                Defaults to True.

        :raises ValueError:     If NCOP is not set.

        :return:                NCOP clip
        """
        if self.ncop is None:
            raise ValueError("EpiosdeInfo.get_ncop: no NCOP set.")

        clip = self.ncop

        if trim_ncop and self.op_range:
            op_s, op_e = self.op_range
            frame_num = op_e - op_s + 1
            clip = clip[:frame_num]

        return clip


    def get_nced(self, trim_nced: bool = True) -> vs.VideoNode:
        """
        Get NCED and raise an exception if it is not set.

        :param trim_nced:         Trim NCED to match frame number of the non-NC ED (needs ed_range to be set).
                                Defaults to True.

        :raises ValueError:     If NCED is not set.

        :return:                NCED clip
        """
        if self.nced is None:
            raise ValueError("EpiosdeInfo.get_nced: no NCED set.")

        clip = self.nced

        if trim_nced and self.ed_range:
            ed_s, ed_e = self.ed_range
            frame_num = ed_e - ed_s + 1
            clip = clip[:frame_num]

        return clip


    def ep_num_str(self, padding: int = 2) -> str:
        """
        Generate a padded string of the episode number

        :param padding:     Length of the string, defaults to 2
        :return:            Padded string
        """
        return str(self.ep_num).zfill(padding)


    @property
    def src(self) -> vs.VideoNode:
        """
        Get the indexed clip.

        :return:    VideoNode object
        """
        return self.source.src if isinstance(self.source, src_file) else self.source

    @property
    def src_cut(self) -> vs.VideoNode:
        """
        Get the indexed and trimmed clip. Only available when using :py:func:`vsmuxtools.src_file`.

        :raises TypeError:     If source is not :py:func:`vsmuxtools.src_file`.

        :return:    VideoNode object
        """
        if not isinstance(self.source, src_file):
            raise TypeError("Source trimming is only available via src_file")

        return self.source.src_cut


    def init(self, **kwargs: Any) -> vs.VideoNode:
        """
        Get the indexed clip and initializes it using :py:func:`vstools.initialize_clip`.

        :return:    VideoNode object
        """
        return self.source.init(**kwargs) if isinstance(self.source, src_file) else initialize_clip(self.source, **kwargs)  # noqa: E501


    def init_cut(self, **kwargs: Any) -> vs.VideoNode:
        """
        Get the indexed and trimmed clip and initializes it using :py:func:`vstools.initialize_clip`.
        Only available when using :py:func:`vsmuxtools.src_file`.

        :raises TypeError:     If source is not :py:func:`vsmuxtools.src_file`.

        :return:    VideoNode object
        """
        if not isinstance(self.source, src_file):
            raise TypeError("Source trimming is only available via src_file")

        return self.source.init_cut(**kwargs)
