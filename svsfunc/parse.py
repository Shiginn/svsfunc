from __future__ import annotations

from glob import glob
from pathlib import Path
from typing import Any, Generic, Iterator, Sequence

from vstools import to_arr, vs

from .bdmv import BDMV, MplsItem
from .custom_types import IndexedT, NCRange
from .indexer import EpisodeInfo, Indexer
from .utils import clip_from_indexer, normalize_list

__all__ = ["ParseFolder", "ParseBD"]


class HasNCs(Generic[IndexedT]):
    indexer: Indexer[IndexedT]
    _ncops: dict[int, vs.VideoNode | Path | None] = {}
    _nceds: dict[int, vs.VideoNode | Path | None] = {}

    @staticmethod
    def _parse_nc_ranges(ncs: NCRange | None = None) -> dict[int, vs.VideoNode | Path | None]:
        ncs_dict = dict[int, vs.VideoNode | Path | None]()

        if ncs is None:
            return ncs_dict

        for ep_range, nc in ncs.items():
            if isinstance(nc, str):
                nc = Path(nc)

            if isinstance(ep_range, int):
                ncs_dict[ep_range] = nc
            else:
                start, end = ep_range
                for i in range(start, end + 1):
                    ncs_dict[i] = nc

        return ncs_dict


    def set_ncs(self, ncops: NCRange | None = None, nceds: NCRange | None = None) -> None:
        """
        Set the NCOP/NCED for an episode or a range of episodes. The input is a dictionary where the key is the range
        of episodes and the value is the path to the NCOP/NCED of theses episodes. If the key is a tuple, it will be
        parsed as an inclusive range of episodes.

        :param ncops: Episodes ranges with matching NCOPs, defaults to None
        :param nceds: Episodes ranges with matching NCEDs, defaults to None
        """
        self._ncops = self._parse_nc_ranges(ncops)
        self._nceds = self._parse_nc_ranges(nceds)


    def _get_nc(self, ncs: list[Path | vs.VideoNode], nc_idx: int) -> vs.VideoNode:
        nc = ncs[nc_idx - 1]

        if isinstance(nc, Path):
            nc = clip_from_indexer(nc, self.indexer, True)

        return nc

    def get_ncop(self, nc_idx: int) -> vs.VideoNode:
        """
        Get a NCOP and index it if necessary. Ignores the NCOPs set to None.

        :param nc_idx:  Index of the NCOP to get (one-based)

        :return:        Indexed NCOP
        """
        return self._get_nc(self.ncops, nc_idx)

    def get_nced(self, nc_idx: int) -> vs.VideoNode:
        """
        Get a NCED and index it if necessary. Ignores the NCEDs set to None.

        :param nc_idx:  Index of the NCED to get (one-based)

        :return:        Indexed NCED
        """
        return self._get_nc(self.nceds, nc_idx)

    @property
    def ncops(self) -> list[vs.VideoNode | Path]:
        """
        List of all of the NCOPs set.

        :return: Path or clip of all the NCOPs
        """
        return [nc for nc in self._ncops.values() if nc is not None]

    @property
    def nceds(self) -> list[vs.VideoNode | Path]:
        """
        List of all of the NCEDs set.

        :return: Path or clip of all the NCEDs
        """
        return [nc for nc in self._nceds.values() if nc is not None]



class HasEpisode(HasNCs[IndexedT], Generic[IndexedT]):
    episodes: list[Path]
    episode_number: int
    indexer: Indexer[IndexedT]
    op_ranges: list[tuple[int, int] | None]
    ed_ranges: list[tuple[int, int] | None]

    _idx: int = 1
    _ep_cache = dict[int, EpisodeInfo[IndexedT]]()


    def _set_episodes(self, eps: Sequence[Path]) -> None:
        if not eps:
            raise ValueError(f"{self.__class__.__name__}._set_episodes: input file list is empty.")

        self.episodes = []
        for ep in eps:
            if not ep.exists():
                raise ValueError(f"{self.__class__.__name__}._set_episodes: file with path \"{ep}\" does not exist.")

        self.episodes = sorted(eps, key=lambda x: x.name)
        self.episode_number = len(self.episodes)
        self.set_op_ed_ranges()


    def get_episode(self, ep_num: int, force_reindex: bool = False, **indexer_overrides: Any) -> EpisodeInfo[IndexedT]:
        """
        Get indexed episode

        :param ep_num:              Episode to get (one-based)
        :param force_reindex:       Re-index episode even if it is present in cache
        :param indexer_overrides:   Override for indexer settings. Will force re-indexing (`force_reindex=True`).

        :return:                    EpisodeInfo object
        """
        if (force_reindex or indexer_overrides) and ep_num in self._ep_cache:
            del self._ep_cache[ep_num]

        if ep_num not in self._ep_cache:
            self._ep_cache[ep_num] = EpisodeInfo(
                self.episodes[ep_num - 1], ep_num, self.op_ranges[ep_num - 1], self.ed_ranges[ep_num - 1],
                self._ncops.get(ep_num), self._nceds.get(ep_num), self.indexer, **indexer_overrides
            )

        return self._ep_cache[ep_num]


    def set_op_ed_ranges(
        self, op_ranges: list[tuple[int, int] | None] | None = None,
        ed_ranges: list[tuple[int, int] | None] | None = None
    ) -> None:
        """
        Set the frame range of the OP and ED of each episode. Range is tuple of two integer (first frame and last frame)
        or None if there is no OP/ED in the episode. Ranges are inclusive.
        Theses ranges are then used by EpisodeInfo.get_op/ed.

        :param op_ranges: List of OP ranges, defaults to None
        :param ed_ranges: List of ED ranges, defaults to None
        """

        func_name = f"{self.__class__.__name__}.set_op_ed_ranges"
        self.op_ranges = normalize_list(op_ranges, self.episode_number, None, func_name)
        self.ed_ranges = normalize_list(ed_ranges, self.episode_number, None, func_name)


    def __iter__(self) -> Iterator[EpisodeInfo[IndexedT]]:
        return self

    def __next__(self) -> EpisodeInfo[IndexedT]:
        try:
            episode = self.get_episode(self._idx)
        except IndexError:
            raise StopIteration

        self._idx += 1
        return episode



class ParseFolder(HasEpisode[IndexedT], HasNCs[IndexedT]):
    """
    Folder parser that uses pattern mathching to get episode list.
    """
    folder: Path

    def __init__(
        self: "ParseFolder[IndexedT]", folder: str | Path, pattern: str | None = None, recursive: bool = False,
        indexer: Indexer[IndexedT] = Indexer.lsmas()  # type: ignore
    ) -> None:
        """
        Parse folder and list every file that matches given pattern.

        :param folder:      Folder that includes all the files to match.
        :param pattern:     Pattern that files must match (uses glob syntax). If None, will match every file.
        :param recursive:   If true, the pattern '**' will match any files and zero or more directories and
                            subdirectories.
        :param indexer:     Indexer used to index the files. Defaults to :py:meth:`svsfunc.indexer.Indexer.lsmas`
        """
        self.indexer = indexer

        self.folder = Path(folder).resolve()
        if not self.folder.exists():
            raise ValueError("ParseFolder: Invalid episode folder path")

        if pattern is None:
            pattern = "**" if recursive else "*"

        eps = [Path(self.folder / ep) for ep in glob(pattern, root_dir=self.folder, recursive=recursive)]
        self._set_episodes(sorted(eps, key=lambda x: x.name))


class ParseBD(HasEpisode[IndexedT], HasNCs[IndexedT]):
    """
    BDMV parser that uses playlist files to get episodes and chapters
    """
    bdmv_folder: Path
    items: list[MplsItem]

    def __init__(
        self: "ParseBD[IndexedT]", bdmv_path: str | Path | list[str | Path] | tuple[str | Path, list[str | Path]],
        ep_playlist: int | Sequence[int], indexer: Indexer[IndexedT] = Indexer.lsmas()  # type: ignore
    ) -> None:
        """
        Parse BDMV and list every file in matching episode playlist(s).

        :param bdmv_path:       Path to the BDMV. If str or Path, it must be the folder that contains every BD volume.
                                If list of str/Path, it is the list to the folder of every volume.
                                If tuple, first value is path to BDMV folder, second is list of every volume.
        :param ep_playlist:     ID of the playlist file for the episodes, can be set for each BD volume
        :param indexer:         Indexer used to index the files. Defaults to :py:meth:`svsfunc.indexer.Indexer.lsmas`

        :raises ValueError:     If the BDMV folder does not exists
        :raises ValueError:     If any of the BD volume folder does not exists
        :raises ValueError:     If BD volume cannot be found (in recursive search)
        :raises ValueError:     If number of episode playlist is greater than number of BD volume
        """
        self.indexer = indexer

        if isinstance(bdmv_path, tuple):
            folder, volumes = bdmv_path
            bdmv = BDMV.from_volumes(volumes, folder)
        elif isinstance(bdmv_path, list):
            bdmv = BDMV.from_volumes(bdmv_path)
        else:
            bdmv = BDMV.from_path(bdmv_path)

        self.bdmv_folder = bdmv.bdmv_folder

        vol_num = len(bdmv.bd_volumes)
        ep_playlist = to_arr(ep_playlist)
        ep_playlist = normalize_list(ep_playlist, vol_num, ep_playlist[-1], "ParseBD")

        self.items = []
        for bd_vol, p in zip(bdmv.bd_volumes, ep_playlist):
            self.items += bd_vol.get_playlist(p).items

        self._set_episodes([item.m2ts_file for item in self.items])


    def get_chapter(self, ep_num: int) -> list[int]:
        """Get a list of chapters of an episode

        :param ep_num:      Number of the episode to get chapters from, one-based

        :return:            List of chapters
        """
        return self.items[ep_num - 1].chapters
