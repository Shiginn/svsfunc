from __future__ import annotations

from abc import ABC, abstractmethod
from glob import glob
from pathlib import Path
from typing import Any, Generic, Sequence

from vardautomation import Chapter, MplsChapters, MplsReader, VPath
from vstools import to_arr

from .custom_types import IndexedT, NCRange
from .indexer import EpisodeInfo, Indexer
from .utils import normalize_list

__all__ = ["ParseFolder", "ParseBD"]


class HasNCs(Generic[IndexedT]):
    ncops: dict[int, VPath | None]
    nceds: dict[int, VPath | None]

    @staticmethod
    def _parse_nc_ranges(ncs: NCRange | None = None) -> dict[int, VPath | None]:
        ncs_dict = dict[int, VPath | None]()

        if ncs is None:
            return ncs_dict

        for ep_range, path in ncs.items():
            if isinstance(path, str):
                path = VPath(path)

            if isinstance(ep_range, int):
                ncs_dict[ep_range] = path
            else:
                start, end = ep_range
                for i in range(start, end + 1):
                    ncs_dict[i] = path

        return ncs_dict


    def set_ncs(self, ncops: NCRange | None = None, nceds: NCRange | None = None) -> None:
        """
        Set the NCOP/NCED for an episode or a range of episodes. The input is a dictionary where the key is the range
        of episodes and the value is the path to the NCOP/NCED of theses episodes. If the key is a tuple, it will be
        parsed an inclusive range of episodes.

        :param ncops: Episodes ranges with matching NCOPs, defaults to None
        :param nceds: Episodes ranges with matching NCEDs, defaults to None
        """
        self.ncops = self._parse_nc_ranges(ncops)
        self.nceds = self._parse_nc_ranges(nceds)


class HasEpisode(HasNCs, ABC, Generic[IndexedT]):
    episodes: list[VPath]
    indexer: Indexer[IndexedT]
    op_ranges: list[tuple[int, int] | None]
    ed_ranges: list[tuple[int, int] | None]

    @abstractmethod
    def get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        ...

    def _get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        return EpisodeInfo(
            self.episodes[ep_num - 1], ep_num, self.op_ranges[ep_num - 1], self.ed_ranges[ep_num - 1],
            self.ncops.get(ep_num), self.nceds.get(ep_num), self.indexer, **indexer_overrides
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
        func_name = f"{self.__class__.__name__}.set_op_ed_ranges"
        eps_num = len(self.episodes)
        self.op_ranges = normalize_list(op_ranges, eps_num, None, func_name)
        self.ed_ranges = normalize_list(ed_ranges, eps_num, None, func_name)


class ParseFolder(HasEpisode, HasNCs, Generic[IndexedT]):
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
        :param indexer:     Indexer used to index the files. Defaults to :py:meth:`svsfunc.indexer.Indexer.lsmas`
        """
        self.indexer = indexer

        self.folder = VPath(folder).resolve()
        if not self.folder.exists():
            raise ValueError("ParseFolder: Invalid episode folder path")

        if pattern is None:
            self.episodes = [VPath(x) for x in self.folder.iterdir() if x.is_file()]
        else:
            self.episodes = [
                VPath(self.folder / ep) for ep in glob(pattern, root_dir=self.folder.to_str())
            ]
        self.episode_number = len(self.episodes)

        if not self.episode_number:
            raise ValueError("ParseFolder: No episode found, check episode folder and/or pattern.")

        self.set_op_ed_ranges()
        self.set_ncs()


    def get_episode(self, ep_num: int, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        """
        Get indexed episode

        :param ep_num:              Episode to get (not zero-based)
        :param indexer_overrides:   Override for indexer settings

        :return:                    EpisodeInfo object
        """
        return super()._get_episode(ep_num, **indexer_overrides)


class ParseBD(HasEpisode, HasNCs, Generic[IndexedT]):
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
        :param indexer:         Indexer used to index the files. Defaults to :py:meth:`svsfunc.indexer.Indexer.lsmas`

        :raises ValueError:     If the BDMV folder does not exists
        :raises ValueError:     If any of the BD volume folder does not exists
        :raises ValueError:     If BD volume cannot be found (in recursive search)
        :raises ValueError:     If number of episode playlist is greater than number of BD volume
        """
        self.indexer = indexer

        self.bdmv_folder = VPath(bdmv_folder).resolve()
        if not self.bdmv_folder.exists():
            raise ValueError("ParseBD: Invalid BDMV path")

        if bd_volumes:
            vols = [Path(self.bdmv_folder / bd_vol).resolve() for bd_vol in bd_volumes]
            for path in vols:
                if not path.exists():
                    raise ValueError(f"ParseBD: BD volume \"{path}\" does not exist.")

        else:
            subdirs = [x for x in self.bdmv_folder.iterdir() if x.is_dir()]
            vols = [self._find_vol_path(vol) for vol in subdirs]  # type: ignore
            for vol_path, subdir in zip(vols, subdirs):
                if vol_path is None:
                    raise ValueError(f"ParseBD: sub-directory \"{subdir}\" of BDMV folder does not contains BD volume.")

        vol_num = len(vols)
        ep_playlist = to_arr(ep_playlist)
        ep_playlist = normalize_list(ep_playlist, vol_num, ep_playlist[-1], "ParseBD")

        self.episodes = []
        self.chapters = []
        for bd_vol, p in zip(vols, ep_playlist):
            chaps = MplsReader(bd_vol).get_playlist()[p].mpls_chapters
            self.episodes += [chap.m2ts for chap in chaps]
            self.chapters += chaps

        self.episode_number = len(self.episodes)
        self.set_op_ed_ranges()
        self.set_ncs()


    def _find_vol_path(self, root_dir: Path) -> Path | None:
        subdirs = [x.name for x in root_dir.iterdir() if x.is_dir()]

        if "BDMV" in subdirs and "CERTIFICATE" in subdirs:
            return root_dir

        for subdir in subdirs:
            path = self._find_vol_path(root_dir / subdir)

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
