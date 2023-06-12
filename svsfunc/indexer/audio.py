from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vstools import DataType, core, vs

from .abstract import Indexer, IndexerCache


@dataclass
class AudioIndexer(Indexer[vs.AudioNode]):
    ...


@dataclass
class BestSourceAudio(AudioIndexer):
    """
    bs.AudioSource from BestSource. Fallback on bas.Source from BestAudioSource if BestSource is not installed
    See https://github.com/vapoursynth/bestsource for documentation.
    """

    track: int | None = None
    adjustdelay: int | None = None
    exact: bool | None = None
    enable_drefs: bool | None = None
    use_absolute_path: bool | None = None
    drc_scale: float | None = None
    cachepath: DataType | None = None
    # cachesize: int | None = None  # not available in latest beta

    _use_bs: bool = field(init=False, repr=False)
    _cache = IndexerCache("cachepath", ".json")

    def __post_init__(self) -> None:
        self._use_bs = hasattr(core, "bs")
        self._index_func = core.lazy.bs.AudioSource if self._use_bs else core.lazy.bas.Source  # type: ignore

        if not self._use_bs:
            import warnings
            warnings.warn("BestSourceAudio: BestSource plugin not installed, falling back on BestAudioSource.")


    def _get_kwargs(self, default: dict[str, Any] | None = None) -> dict[str, Any]:
        kwargs = super()._get_kwargs(default)

        if not self._use_bs:
            kwargs["exactsamples"] = kwargs.get("exact")
            kwargs.pop("exact", None)
            kwargs.pop("cachepath", None)
            # kwargs.pop("cachesize", None)

        return kwargs
