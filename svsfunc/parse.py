from __future__ import annotations

from glob import glob
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, Sequence

from vsmuxtools import Chapters, src_file
from vstools import to_arr, vs_object

from .bdmv import BDMV, MplsItem
from .custom_types import HoldsVideoNodeT, PathLike
from .utils import normalize_list

__all__ = ["ParseFolder", "ParseBD"]


class HasEpisode(Generic[HoldsVideoNodeT], vs_object):
    episodes: list[Path]
    indexer: Callable[[str | Path], HoldsVideoNodeT]

    _ep_cache: dict[int, HoldsVideoNodeT]
    _idx: int

    def __init__(self, eps: Sequence[Path]) -> None:
        if not eps:
            raise ValueError(f"{self.__class__.__name__}: input file list is empty.")

        self.episodes = []
        for ep in eps:
            if not ep.exists():
                raise ValueError(f"{self.__class__.__name__}: file with path \"{ep}\" does not exist.")
            self.episodes.append(ep)

        self._ep_cache = {}

    @property
    def episode_number(self) -> int:
        return len(self.episodes)

    def get_episode(
        self, ep_num: int, force_reindex: bool = False, **indexer_overrides: Any
    ) -> HoldsVideoNodeT:
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
            self._ep_cache[ep_num] = self.indexer(self.episodes[ep_num - 1], **indexer_overrides)

        return self._ep_cache[ep_num]


    def __iter__(self) -> Iterator[HoldsVideoNodeT]:
        self._idx = 1
        return self

    def __next__(self) -> HoldsVideoNodeT:
        try:
            episode = self.get_episode(self._idx)
        except IndexError:
            self._idx = 1
            raise StopIteration

        self._idx += 1
        return episode

    def __vs_del__(self, core_id: int) -> None:
        for value in self._ep_cache.values():
            del value
        self._ep_cache.clear()


class ParseFolder(HasEpisode[HoldsVideoNodeT]):
    """
    Folder parser that uses pattern mathching to get episode list.
    """
    folder: Path

    def __init__(
        self,
        folder: PathLike, pattern: str,
        indexer: Callable[[str | Path], HoldsVideoNodeT],
        recursive: bool = False, sort: bool = True
    ) -> None:
        """
        Parse folder and list every file that matches given pattern.

        :param folder:      Folder that includes all the files to match.
        :param pattern:     Pattern that files must match (uses glob syntax). If None, will match every file.
        :param recursive:   If true, the pattern '**' will match any files and zero or more directories and
                            subdirectories.
        :param sort:        Sort matched files by name.
        :param indexer:     Indexer used to index the files. Defaults to :py:meth:`svsfunc.indexer.Indexer.lsmas`
        """
        self.indexer = indexer

        self.folder = Path(folder).resolve()
        if not self.folder.exists():
            raise ValueError("ParseFolder: Invalid episode folder path")

        if pattern is None:
            pattern = "**" if recursive else "*"

        eps = [Path(self.folder / ep) for ep in glob(pattern, root_dir=self.folder, recursive=recursive)]
        super().__init__(sorted(eps, key=lambda x: x.name) if sort else eps)


class ParseBD(HasEpisode[HoldsVideoNodeT]):
    """
    BDMV parser that uses playlist files to get episodes and chapters
    """
    bdmv: BDMV
    items: list[MplsItem]

    def __init__(
        self,
        bdmv_path: PathLike | list[PathLike] | tuple[PathLike, list[PathLike]] | BDMV,
        ep_playlist: int | Sequence[int], indexer: Callable[[str | Path], HoldsVideoNodeT]
    ) -> None:
        """
        Parse BDMV and list every file in matching episode playlist(s).

        :param bdmv_path:       Path to the BDMV. If str or Path, it must be the folder that contains every BD volume.
                                If list of str/Path, it is the list to the folder of every volume.
                                If tuple, first value is path to BDMV folder, second is list of every volume.
        :param ep_playlist:     ID of the playlist file for the episodes, can be set for each BD volume
        :param indexer:         Indexer used to index the files. Defaults to :py:meth:`svsfunc.indexer.Indexer.lsmas`
        """
        self.indexer = indexer

        if isinstance(bdmv_path, tuple):
            folder, volumes = bdmv_path
            bdmv = BDMV.from_volumes(volumes, folder)
        elif isinstance(bdmv_path, list):
            bdmv = BDMV.from_volumes(bdmv_path)
        elif isinstance(bdmv_path, str) or isinstance(bdmv_path, Path):
            bdmv = BDMV.from_path(bdmv_path)
        else:
            bdmv = bdmv_path

        self.bdmv = bdmv

        ep_playlist = to_arr(ep_playlist)
        ep_playlist = normalize_list(ep_playlist, len(self.bdmv.bd_volumes), ep_playlist[-1], "ParseBD")

        self.items = []
        for bd_vol, p in zip(self.bdmv.bd_volumes, ep_playlist):
            self.items += bd_vol.get_playlist(p).items

        super().__init__([item.m2ts_file for item in self.items])


    def get_chapter(
        self, ep_num: int, chapters_names: list[str | None] | None = None,
        src_file: src_file | None = None
    ) -> Chapters:
        """
        Get the list of chapters of an episode from the BD's playlist file

        :param ep_num:          Episode number
        :param chapters_names:  Names of the chapters, defaults to None
        :param src_file:        src_file to trim the chapters, defaults to None

        :raises ValueError:     The number of chapters names does not match the number of chapters (after trimming).

        :return:                List of chapters
        """

        mpls_item = self.items[ep_num - 1]
        chaps_frames = mpls_item.chapters

        chapters = Chapters([(frame, None) for frame in chaps_frames], timesource=mpls_item.framerate)

        if src_file:
            # src_file.trim can be None despite type hint saying Trim
            trim: tuple[int | None, int | None] = src_file.trim or (0, 0)
            start = trim[0] or 0
            chapters.trim(start, src_file.src_cut.num_frames, src_file.src_cut.num_frames)

        chap_num = len(chapters.chapters)

        if chapters_names is None:
            chapters_names = [None] * chap_num

        elif (name_num := len(chapters_names)) != chap_num:
            raise ValueError(
                f"ParseBD.get_chapter: invalid number of chapters_names given, expected {chap_num}, got {name_num}. " +
                f"Chapters frames: {', '.join([str(f) for f in chaps_frames])}"
            )

        return chapters.set_names(chapters_names)
