from pathlib import Path
from subprocess import check_call
from typing import Any, Generic, Sequence, overload

from vardautomation import (
    AnyPath, DuplicateFrame, FileInfo, FileInfo2, Preset, PresetBD, PresetBDWAV64, Trim, VPath, VPSIdx
)
from vstools import DataType, core, vs

from .custom_types import FileInfoT, IndexedT, VSIdxFunc
from .utils import trim

__all__ = ["Indexer", "EpisodeInfo"]


class Indexer(Generic[IndexedT]):
    """
    Collection of various indexer with unified API.
    """
    _indexer: VSIdxFunc | type[FileInfo]


    @overload
    def __init__(self: "Indexer[vs.VideoNode]", indexer: VSIdxFunc, *args: Any, **kwargs: Any):
        ...

    @overload
    def __init__(self: "Indexer[FileInfo2]", indexer: type[FileInfo2], *args: Any, **kwargs: Any):
        ...

    @overload
    def __init__(self: "Indexer[FileInfo]", indexer: type[FileInfo], *args: Any, **kwargs: Any):
        ...

    def __init__(self, indexer: VSIdxFunc | type[FileInfo], *args: Any, **kwargs: Any) -> None:
        """
        Create a preconfigured indexer with the given settings.

        :param indexer: Indexing function
        """
        self._indexer = indexer
        self.args = args
        self.kwargs = kwargs


    def __call__(self, path: str | Path, **indexer_overrides: Any) -> IndexedT:
        return self.index(path, **indexer_overrides)


    def index(self, path: str | Path, **indexer_overrides: Any) -> IndexedT:
        """
        Index a file with the chosen indexer

        :param path:                File to index
        :param indexer_overrides:   Override indexer settings (keyword arguments only)

        :raises ValueError:         If the given path is not valid

        :return:                    Indexed file
        """
        if isinstance(path, str):
            path = Path(path)

        if not path.exists():
            raise ValueError(f"Indexer.index: The path \"{path}\" does not exist.")

        return self._indexer(str(path), *self.args, **(self.kwargs | indexer_overrides))  # type: ignore


    @classmethod
    def file_info(
        cls, trims_or_dfs: list[Trim | DuplicateFrame] | Trim | None = None,
        idx: "Indexer[vs.VideoNode]" | VPSIdx | None = None,
        preset: Preset | Sequence[Preset] = [PresetBD, PresetBDWAV64],
        workdir: AnyPath = VPath().cwd()
    ) -> "Indexer[FileInfo]":
        """
        FileInfo from Vardautomation.

        :param trims_or_dfs:    Adjust the clip length by trimming or duplicating frames. Python slicing.
                                Defaults to None.
        :param idx:             Indexer used to index the video track, defaults to None.
        :param preset:          Preset used to fill idx, a_src, a_src_cut, a_enc_cut and chapter attributes,
                                defaults to [PresetBD, PresetBDWAV64]
        :param workdir:         Work directory. Default to the current directorie where the script is launched.

        :return: Preconfigured FileInfo indexer
        """
        return cls(FileInfo, trims_or_dfs=trims_or_dfs, idx=idx, preset=preset, workdir=workdir)


    @classmethod
    def file_info2(
        cls, trims_or_dfs: list[Trim | DuplicateFrame] | Trim | None = None,
        idx: "Indexer[vs.VideoNode]" | VPSIdx | None = None,
        preset: Preset | Sequence[Preset] = [PresetBD, PresetBDWAV64],
        workdir: AnyPath = VPath().cwd()
    ) -> "Indexer[FileInfo2]":
        """
        FileInfo2 from Vardautomation.

        :param trims_or_dfs:    Adjust the clip length by trimming or duplicating frames. Python slicing.
                                Defaults to None.
        :param idx:             Indexer used to index the video track, defaults to None.
        :param preset:          Preset used to fill idx, a_src, a_src_cut, a_enc_cut and chapter attributes,
                                defaults to [PresetBD, PresetBDWAV64]
        :param workdir:         Work directory. Default to the current directorie where the script is launched.

        :return: Preconfigured FileInfo2 indexer
        """
        return cls(FileInfo2, trims_or_dfs=trims_or_dfs, idx=idx, preset=preset, workdir=workdir)


    @classmethod
    def lsmas(
        cls, stream_index: int | None = None, cache: int | None = None, cachefile: DataType | None = None,
        threads: int | None = None, seek_mode: int | None = None, seek_threshold: int | None = None,
        dr: int | None = None, fpsnum: int | None = None, fpsden: int | None = None, variable: int | None = None,
        format: DataType | None = None, decoder: DataType | None = None,
        prefer_hw: int | None = None, repeat: int | None = None, dominance: int | None = None,
        ff_loglevel: int | None = None, cachedir: DataType | None = None, soft_reset: int | None = None
    ) -> "Indexer[vs.VideoNode]":
        """
        LWLibavSource from LSMAS plugin.

        Documentation: see https://github.com/AkarinVS/L-SMASH-Works/blob/master/VapourSynth/README

        :return: Preconfigured lsmas indexer.
        """
        return cls(
            core.lazy.lsmas.LWLibavSource, stream_index=stream_index, cache=cache, cachefile=cachefile, threads=threads,
            seek_mode=seek_mode, seek_threshold=seek_threshold, dr=dr, fpsnum=fpsnum, fpsden=fpsden, variable=variable,
            format=format, decoder=decoder, prefer_hw=prefer_hw, repeat=repeat, dominance=dominance,
            ff_loglevel=ff_loglevel, cachedir=cachedir, soft_reset=soft_reset
        )


    @classmethod
    def ffms2(
        cls, track: int | None = None, cache: int | None = None, cachefile: DataType | None = None,
        fpsnum: int | None = None, fpsden: int | None = None, threads: int | None = None,
        timecodes: DataType | None = None, seekmode: int | None = None, width: int | None = None,
        height: int | None = None, resizer: DataType | None = None, format: int | None = None,
        alpha: int | None = None
    ) -> "Indexer[vs.VideoNode]":
        """
        ffms2.Source from ffms2 plugin.

        Documentation: see https://github.com/FFMS/ffms2/blob/master/doc/ffms2-vapoursynth.md

        :return: Preconfigured ffms2 indexer.
        """
        return cls(
            core.lazy.ffms2.Source, track=track, cache=cache, cachefile=cachefile, fpsnum=fpsnum, fpsden=fpsden,
            threads=threads, timecodes=timecodes, seekmode=seekmode, width=width, height=height, resizer=resizer,
            format=format, alpha=alpha
        )


    @classmethod
    def best_source(
        cls, track: int | None = None, variableformat: int | None = None, threads: int | None = None,
        seekpreroll: int | None = None, exact: int | None = None, enable_drefs: int | None = None,
        use_absolute_path: int | None = None, cachepath: DataType | None = None,
        hwdevice: DataType | None = None
    ) -> "Indexer[vs.VideoNode]":
        """
        bs.VideoSource from BestSource plugin.

        Documentation: see https://github.com/vapoursynth/bestsource/blob/master/README.md

        :return: Preconfigured BestSource indexer.
        """
        return cls(
            core.lazy.bs.VideoSource, track=track, variableformat=variableformat, threads=threads,  # type: ignore
            seekpreroll=seekpreroll, exact=exact, enable_drefs=enable_drefs, use_absolute_path=use_absolute_path,
            cachepath=cachepath, hwdevice=hwdevice
        )


    @classmethod
    def dg_index_nv(
        cls, i420: int | None = None, deinterlace: int | None = None, use_top_field: int | None = None,
        use_pf: int | None = None, ct: int | None = None, cb: int | None = None, cl: int | None = None,
        cr: int | None = None, rw: int | None = None, rh: int | None = None, fieldop: int | None = None,
        show: int | None = None, show2: DataType | None = None
    ) -> "Indexer[vs.VideoNode]":
        """
        dgdecodenv.DGSource from DGIndexNV/DGDecodeNV plugin

        Documentation: see the DGDecodeNVManual.html and DGIndexNVManual.html files

        :return: Preconfigured DGIndexNV indexer.
        """
        def _index_file(path: str, *args: Any, **kwargs: Any) -> vs.VideoNode:
            input_path = Path(path)
            dgi_path = input_path.with_suffix(".dgi")

            if not dgi_path.exists():
                check_call([
                    "DGIndexNV", "-i", str(input_path), "-o", str(dgi_path), "-h"
                ])

            return core.lazy.dgdecodenv.DGSource(dgi_path, *args, **kwargs)

        return cls(
            _index_file, i420=i420, deinterlace=deinterlace, use_top_field=use_top_field, use_pf=use_pf, ct=ct, cb=cb,  # type: ignore  # noqa: E501
            cl=cl, cr=cr, rw=rw, rh=rh, fieldop=fieldop, show=show, show2=show2
        )


class EpisodeInfo(Generic[IndexedT]):
    """
    Class that represent an indexed episode with episode number and optional OP/ED ranges.

    :param Generic: Type of the indexed file.
    """
    indexed: IndexedT
    ep_num: int
    op_range: tuple[int, int] | None = None
    ed_range: tuple[int, int] | None = None


    def __init__(
        self: "EpisodeInfo[IndexedT]", path: str | Path, ep_num: int = -1, op_range: tuple[int, int] | None = None,
        ed_range: tuple[int, int] | None = None, indexer: Indexer[IndexedT] = Indexer.lsmas(), **indexer_overrides: Any  # type: ignore  # noqa: E501
    ) -> None:
        """
        Index a file and set episode number + OP/ED range.

        :param path:                Input file path
        :param ep_num:              Episode number, defaults to -1
        :param op_range:            Range of the opening, defaults to None
        :param ed_range:            Range of the ending, defaults to None
        :param indexer:             Indexer used to index given file, defaults to :py:func:`Indexer.lsmas()`
        :param indexer_overrides:   Overrdide indexer settings (keyword arguments only)
        """
        self.indexed = indexer.index(path, **indexer_overrides)
        self.ep_num = ep_num
        self.op_range = op_range
        self.ed_range = ed_range


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
        return self.indexed.clip_cut if isinstance(self.indexed, FileInfo) else self.indexed


    @property
    def file(self: "EpisodeInfo[FileInfoT]") -> FileInfoT:
        """
        Get FileInfo object from the indexed file

        :raises TypeError:  If indexer used is not FileInfo or FileInfo2
        :return:            FileInfo object
        """
        if not isinstance(self.indexed, FileInfo):
            raise TypeError("EpisodeInfo.file: The indexer used does not support FileInfo")

        return self.indexed
