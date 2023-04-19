from __future__ import annotations

from abc import ABC, abstractmethod
from glob import glob
from pathlib import Path
from typing import Any, Generic, Sequence

from vardautomation import Chapter, MplsChapters, MplsReader, VPath

from .indexer import Indexer, EpisodeInfo
from .custom_types import IndexedT

__all__ = ["ParseFolder", "ParseBD"]


class HasEpisode(Generic[IndexedT], ABC):
    episodes: list[VPath]
    indexer: Indexer[IndexedT]
    op_ranges: list[tuple[int, int] | None]
    ed_ranges: list[tuple[int, int] | None]

    @abstractmethod
    def get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        ...

    def _get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        return EpisodeInfo(
            self.episodes[ep_num - 1], ep_num, self.op_ranges[ep_num - 1], self.ed_ranges[ep_num - 1], self.indexer,
            **indexer_overrides
        )

    def set_op_ed_ranges(
        self, op_ranges: list[tuple[int, int] | None] | None = None,
        ed_ranges: list[tuple[int, int] | None] | None = None
    ) -> None:
        """
        Set the ranges of the OPs and EDs of each episode. Range is tuple of two int: (start_frame, end_frame) or None
        if there is no OP/ED in the episode. Ranges are inclusive.
        Theses ranges are then used by EpisodeInfo.get_op/ed to get a clip that only contains the OP/ED of the episode.

        :param op_ranges: List of OP ranges, defaults to None
        :param ed_ranges: List of ED ranges, defaults to None

        :raises ValueError: If the number of ranges is greater than the number of episode
        """
        eps_num = len(self.episodes)

        if op_ranges is None:
            op_ranges = []
        if ed_ranges is None:
            ed_ranges = []

        ops_num = len(op_ranges)
        eds_num = len(ed_ranges)

        if ops_num < eps_num:
            op_ranges = op_ranges + [None] * ((eps_num - ops_num))
        elif ops_num > eps_num:
            raise ValueError(f"Too many OP ranges given: expected {eps_num} max, got {ops_num}")

        if eds_num < eps_num:
            ed_ranges = ed_ranges + [None] * ((eps_num - eds_num))
        elif eds_num > eps_num:
            raise ValueError(f"Too many ED ranges given: expected {eps_num} max, got {eds_num}")

        self.op_ranges = op_ranges
        self.ed_ranges = ed_ranges


class ParseFolder(HasEpisode, Generic[IndexedT]):
    """
    Folder parser that uses pattern mathching to get episode list.
    """
    folder: VPath
    episode_number: int
    indexer: Indexer[IndexedT]


    def __init__(
        self: "ParseFolder[IndexedT]", folder: str | Path, pattern: str | None = None,
        indexer: Indexer[IndexedT] = Indexer.lsmas()  # type: ignore
    ) -> None:
        """
        Parse folder and list every file that matches given pattern.

        :param folder:      Folder that includes all of the episodes.
        :param pattern:     Pattern that files must match (uses glob syntax)
        :param indexer:     Indexer used to index the files. Defaults to :py:func:`Indexer.lsmas()`
        """
        self.indexer = indexer

        self.folder = VPath(folder).resolve()
        if not self.folder.exists():
            raise ValueError("Invalid episode folder path")

        if pattern is None:
            self.episodes = [VPath(x) for x in self.folder.iterdir() if x.is_file()]
        else:
            self.episodes = [
                VPath(self.folder / ep) for ep in glob(pattern, root_dir=self.folder.to_str())
            ]
        self.episode_number = len(self.episodes)

        if not self.episode_number:
            raise ValueError("No episode found, check episode folder and/or pattern.")

        self.set_op_ed_ranges()


    def get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        """
        Get indexed episode

        :param ep_num:              Episode to get (not zero-based)
        :param indexer_overrides:   Override for indexer settings

        :return:                    EpisodeInfo object
        """
        return super()._get_episode(ep_num, **indexer_overrides)


class ParseBD(HasEpisode, Generic[IndexedT]):
    """
    BDMV parser that uses playlist files to get episodes and chapters
    """

    bdmv_folder: VPath
    episodes: list[VPath]
    chapters: list[MplsChapters]
    episode_number: int
    indexer: Indexer[IndexedT]


    def __init__(
        self, bdmv_folder: str | Path, bd_volumes: Sequence[str | Path] | None = None,
        ep_playlist: int | Sequence[int] = 1, indexer: Indexer[IndexedT] = Indexer.lsmas()  # type: ignore
    ) -> None:
        """
        Parse BDMV and list every file in matching episode playlist(s).

        :param bdmv_folder:     Path to the BDMV folder that contains every volume
        :param bd_volumes:      Path to every volume of the BD (relative to the BDMV folder). Will do a recursive search
                                of every subfolder of the BDMV folder to try to locate them if None.
        :param ep_playlist:     Playlist file for the episodes, defaults to 1, can be set for each BD volume
        :param indexer:         Indexer used to index the files. Defaults to :py:func:`Indexer.lsmas()`

        :raises ValueError:     If the BDMV folder does not exists
        :raises ValueError:     If any of the BD volume folder does not exists
        :raises ValueError:     If BD volume cannot be found (in recursive search)
        :raises ValueError:     If number of episode playlist is greater than number of BD volume
        """
        self.indexer = indexer

        self.bdmv_folder = VPath(bdmv_folder).resolve()
        if not self.bdmv_folder.exists():
            raise ValueError("Invalid BDMV path")

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
        self.set_op_ed_ranges()


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


    def get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        """
        Get indexed episode

        :param ep_num:              Number of the episode to get, one-based
        :param indexer_overrides:   Override for indexer settings

        :return:                    EpisodeInfo object
        """
        return super()._get_episode(ep_num, **indexer_overrides)


    def get_chapter(self, ep_num: int) -> list[Chapter]:
        """Get a list of chapters of an episode

        :param ep_num:      Number of the episode to get chapters from, one-based

        :return:            List of chapters
        """
        return self.chapters[ep_num - 1].to_chapters()
