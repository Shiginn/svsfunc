from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from subprocess import check_call
from typing import Any, Literal

from vstools import DataType, core, vs

from .abstract import Indexer, IndexerCache

__all__ = ["VideoIndexer", "LSMAS", "DGIndexNV", "FFMS2", "BestSourceVideo"]


@dataclass
class VideoIndexer(Indexer[vs.VideoNode]):
    ...



@dataclass
class LSMAS(VideoIndexer):
    """
    LWLibavSource from LSMAS plugin.
    See https://github.com/AkarinVS/L-SMASH-Works for documentation.
    """
    _index_func = core.lazy.lsmas.LWLibavSource
    _cache = IndexerCache("cachefile", ".lwi")

    stream_index: int | None = None
    cache: bool | None = None
    threads: int | None = None
    seek_mode: Literal[0, 1, 2] | None = None
    seek_threshold: int | None = None
    dr: bool | None = None  # bool ?
    fpsnum: int | None = None
    fpsden: int | None = None
    variable: bool | None = None
    format: DataType | None = None
    decoder: DataType | None = None
    prefer_hw: Literal[0, 1, 2, 3] | None = None
    repeat: bool | None = None
    dominance: Literal[0, 1, 2] | None = None
    ff_loglevel: Literal[0, 1, 2, 3, 4, 5, 6, 7, 8] | None = None
    soft_reset: bool | None = None
    # framelist: bool | None = None  # vsrepo list vA.3j as latest version


@dataclass
class DGIndexNV(VideoIndexer):
    """
    dgdecodenv.DGSource from DGIndexNV/DGDecodeNV plugin.
    See the DGDecodeNVManual.html and DGIndexNVManual.html files for documentation.
    """
    _cache = IndexerCache("cachefile", ".dgi")

    i420: bool | None = None
    deinterlace: Literal[0, 1, 2] | None = None
    use_top_field: bool | None = None
    use_pf: bool | None = None
    ct: int | None = None
    cb: int | None = None
    cl: int | None = None
    cr: int | None = None
    rw: int | None = None
    rh: int | None = None
    fieldop: Literal[0, 1, 2] | None = None
    show: bool | None = None
    show2: DataType | None = None

    def _index_func(self, path: Path, *args: Any, **kwargs: Any) -> vs.VideoNode:  # type: ignore
        cache_path = Path(kwargs.pop(self._cache.arg_name))

        if not cache_path.exists():
            check_call(["DGIndexNV", "-i", str(path), "-o", str(cache_path), "-h"])
            Path(cache_path.with_suffix(".log")).unlink(True)

        return core.dgdecodenv.DGSource(cache_path, *args, **kwargs)


@dataclass
class FFMS2(VideoIndexer):
    """
    ffms2.Source from ffms2 plugin.
    See https://github.com/FFMS/ffms2 for documentation.
    """
    _index_func = core.lazy.ffms2.Source
    _cache = IndexerCache("cachefile", ".ffindex")

    track: int | None = None
    cache: bool | None = None
    fpsnum: int | None = None
    fpsden: int | None = None
    threads: int | None = None
    timecodes: DataType | None = None
    seekmode: Literal[-1, 0, 1, 2, 3] | None = None
    width: int | None = None
    height: int | None = None
    resizer: DataType | None = None
    format: int | None = None
    alpha: bool | None = None


@dataclass
class BestSourceVideo(VideoIndexer):
    """
    bs.VideoSource from BestSource.
    See https://github.com/vapoursynth/bestsource for documentation.
    """
    _index_func = core.lazy.bs.VideoSource  # type: ignore
    _cache = IndexerCache("cachepath", ".json")

    track: int | None = None
    variableformat: bool | None = None
    threads: int | None = None
    seekpreroll: int | None = None
    exact: bool | None = None
    enable_drefs: bool | None = None
    use_absolute_path: bool | None = None
    hwdevice: DataType | None = None
    # cachesize: int | None = None  # not available in latest beta
