from __future__ import annotations

from abc import ABC, abstractmethod
from glob import glob
from pathlib import Path
from typing import Any, Generic, Sequence, Type, TypeVar, Union, cast, overload

import vapoursynth as vs
from vardautomation import Chapter, FileInfo, FileInfo2, MplsChapters, MplsReader, VPath, VPSIdx

__all__ = ["ParseFolder", "ParseBD"]


core = vs.core

Indexed = Union[vs.VideoNode, FileInfo]
Indexer = Union[VPSIdx, Type[FileInfo]]
IndexedT = TypeVar("IndexedT", bound=Indexed)
IndexerT = TypeVar("IndexerT", bound=Indexer)


class HasEpisode(ABC):
    episodes: list[VPath]
    indexer: Indexer
    indexer_settings: dict[str, Any]


    def _get_episode(self, ep_num: int | str, **indexer_overrides: Any) -> Indexed:
        if isinstance(ep_num, str):
            ep_num = int(ep_num)

        idx_settings: dict[str, Any] = self.indexer_settings | indexer_overrides
        return self.indexer(self.episodes[ep_num - 1].to_str(), **idx_settings)


    @abstractmethod
    def get_episode(self, ep_num: int | str, **indexer_overrides: Any) -> Indexed:
        ...


class ParseFolder(HasEpisode, Generic[IndexedT, IndexerT]):
    """
    Folder parser that uses pattern mathching to get episode list.

    :param folder:              Folder that includes all of the episodes.
    :param indexer:             Indexer used to index the files. Needs to be a function that takes a string (path to the
                                file) and return a VideoNone or a FileInfo
    :param indexer_settings:    Global settings for the indexer.
    """

    folder: VPath
    episode_number: int
    indexer: IndexerT
    indexer_settings: dict[str, Any]

    @overload
    def __init__(
        self: "ParseFolder[vs.VideoNode, VPSIdx]",
        episode_folder: str | Path, episode_pattern: str | None = None,
        indexer: VPSIdx | None = None, **indexer_settings: Any
    ) -> None:
        ...

    # using generics for fileinfo/fileinfo2 breaks mypy lmao
    @overload
    def __init__(
        self: "ParseFolder[FileInfo2, Type[FileInfo2]]",
        episode_folder: str | Path, episode_pattern: str | None = None,
        indexer: Type[FileInfo2] | None = None, **indexer_settings: Any
    ) -> None:
        ...

    @overload
    def __init__(
        self: "ParseFolder[FileInfo, Type[FileInfo]]",
        episode_folder: str | Path, episode_pattern: str | None = None,
        indexer: Type[FileInfo] | None = None, **indexer_settings: Any
    ) -> None:
        ...

    def __init__(
        self, episode_folder: str | Path, episode_pattern: str | None = None,
        indexer: VPSIdx | Type[FileInfo] | Type[FileInfo2] | None = None, **indexer_settings: Any
    ) -> None:
        self.folder = VPath(episode_folder).resolve()
        if not self.folder.exists():
            raise ValueError("Invalid episode folder path")

        if indexer is None:
            indexer = core.lsmas.LWLibavSource
        elif not callable(indexer):
            raise ValueError("Indexer must be callable")
        self.indexer = cast(IndexerT, indexer)
        self.indexer_settings = indexer_settings

        if episode_pattern is None:
            self.episodes = [VPath(x) for x in self.folder.iterdir() if x.is_file()]
        else:
            self.episodes = [
                VPath(self.folder / ep) for ep in glob(episode_pattern, root_dir=self.folder.to_str())
            ]
        self.episode_number = len(self.episodes)

        if not self.episode_number:
            raise ValueError("No episode found, check episode folder and/or pattern.")


    def get_episode(self, ep_num: int | str, **indexer_overrides: Any) -> IndexedT:
        """
        Get indexed episode

        :param ep_num:              Episode to get (not zero-based)
        :param indexer_overrides:   Override for indexer settings

        :return:                    FileInfo object
        """
        return cast(IndexedT, super()._get_episode(ep_num, **indexer_overrides))


class ParseBD(HasEpisode, Generic[IndexedT, IndexerT]):
    """
    BDMV parser that uses playlist files to get episodes and chapters

    :param bdmv_folder:         Path to the BDMV folder that contains every volume
    :param bd_volumes:          Path to every volume of the BD (relative to the BDMV folder). Will try to automatically
                                find them if None.
    :param ep_playlist:         Playlist file for the episodes (defaults to 1, can be set for each volume)
    :param indexer:             Indexer used to index the files. Needs to be a function that takes a string (path to the
                                file) and return a VideoNone or a FileInfo
    :param indexer_settings:    Global settings for the indexer.
    """

    bdmv_folder: VPath
    episodes: list[VPath]
    chapters: list[MplsChapters]
    episode_number: int
    indexer: IndexerT
    indexer_settings: dict[str, Any]

    @overload
    def __init__(
        self: "ParseBD[vs.VideoNode, VPSIdx]", bdmv_folder: str | Path,
        bd_volumes: Sequence[str | Path] | None = None,
        ep_playlist: int | Sequence[int] = 1,
        indexer: VPSIdx | None = None, **indexer_settings: Any
    ) -> None:
        ...

    # using generics for fileinfo/fileinfo2 breaks mypy lmao
    @overload
    def __init__(
        self: "ParseBD[FileInfo2, Type[FileInfo2]]", bdmv_folder: str | Path,
        bd_volumes: Sequence[str | Path] | None = None,
        ep_playlist: int | Sequence[int] = 1,
        indexer: Type[FileInfo2] | None = None, **indexer_settings: Any
    ) -> None:
        ...

    @overload
    def __init__(
        self: "ParseBD[FileInfo, Type[FileInfo]]", bdmv_folder: str | Path,
        bd_volumes: Sequence[str | Path] | None = None,
        ep_playlist: int | Sequence[int] = 1,
        indexer: Type[FileInfo] | None = None, **indexer_settings: Any
    ) -> None:
        ...

    def __init__(
        self, bdmv_folder: str | Path,
        bd_volumes: Sequence[str | Path] | None = None,
        ep_playlist: int | Sequence[int] = 1,
        indexer: VPSIdx | Type[FileInfo] | Type[FileInfo2] | None = None, **indexer_settings: Any
    ) -> None:

        self.bdmv_folder = VPath(bdmv_folder).resolve()
        if not self.bdmv_folder.exists():
            raise ValueError("Invalid BDMV path")

        if indexer is None:
            indexer = core.lsmas.LWLibavSource
        elif not callable(indexer):
            raise ValueError("Indexer must be callable")
        self.indexer = cast(IndexerT, indexer)
        self.indexer_settings = indexer_settings

        if bd_volumes:
            vols = [Path(self.bdmv_folder / bd_vol).resolve() for bd_vol in bd_volumes]
            if any(not path.exists() for path in vols):
                raise ValueError("BD volume path does not exist.")
        else:
            subdirs = [x for x in self.bdmv_folder.iterdir() if x.is_dir()]
            vols = [self._find_vol_path(vol) for vol in subdirs]  # type: ignore
            if any(path is None for path in vols):
                raise ValueError("Could not find BD volume path.")

        vol_num = len(vols)
        if not isinstance(ep_playlist, Sequence):
            ep_playlist = [ep_playlist] * vol_num
        elif len(ep_playlist) < vol_num:
            ep_playlist = list(ep_playlist) + ([ep_playlist[-1]] * (vol_num - len(ep_playlist)))
        elif len(ep_playlist) > vol_num:
            raise ValueError(f"Too many playlist values, expected {vol_num} max")

        self.episodes = []
        self.chapters = []
        for bd_vol, p in zip(vols, ep_playlist):
            chaps = [chap for chap in MplsReader(bd_vol).get_playlist()[p].mpls_chapters]
            self.episodes += [chap.m2ts for chap in chaps]
            self.chapters += chaps

        self.episode_number = len(self.episodes)


    def _find_vol_path(self, root_dir: Path) -> Path | None:
        subdirs = [x.name for x in root_dir.iterdir() if x.is_dir()]

        if "BDMV" in subdirs and "CERTIFICATE" in subdirs:
            return root_dir

        elif len(subdirs):
            for dir in subdirs:
                path = self._find_vol_path(root_dir / dir)

                if path is not None:
                    return path

        return None


    def get_episode(self, ep_num: int | str, **indexer_overrides: Any) -> IndexedT:
        """
        Get indexed episode

        :param ep_num:              Episode to get (not zero-based)
        :param indexer_overrides:   Override for indexer settings

        :return:                    FileInfo object
        """
        return cast(IndexedT, super()._get_episode(ep_num, **indexer_overrides))


    def get_chapter(self, ep_num: int | str) -> list[Chapter]:
        """Get a list of chapters of an episode

        :param ep_num:      Episode to get (not zero-based)

        :return:            List of chapters
        """
        if isinstance(ep_num, str):
            ep_num = int(ep_num)

        return self.chapters[ep_num - 1].to_chapters()
