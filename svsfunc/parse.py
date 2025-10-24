from __future__ import annotations

from glob import glob
from pathlib import Path
from typing import Any, Callable, Generic, Iterator, Sequence

from pytimeconv import Convert
from vsmuxtools import Chapters, debug, src_file, warn
from vstools import to_arr

from .bdmv import BDMV, BdVolume, MplsFile, MplsItem
from .custom_types import HoldsVideoNodeT, PathLike
from .utils import normalize_list, vs_object

BluRayTrim = tuple[int | None, int | None]

__all__ = ["ParseFolder", "ParseBD"]


class HasEpisode(vs_object, Generic[HoldsVideoNodeT]):
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
                raise ValueError(f'{self.__class__.__name__}: file with path "{ep}" does not exist.')
            self.episodes.append(ep)

        self._ep_cache = {}

    @property
    def episode_number(self) -> int:
        return len(self.episodes)

    def get_episode(self, ep_num: int, force_reindex: bool = False, **indexer_overrides: Any) -> HoldsVideoNodeT:
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
        folder: PathLike,
        pattern: str,
        indexer: Callable[[str | Path], HoldsVideoNodeT],
        recursive: bool = False,
        sort: bool = True,
    ) -> None:
        """
        Parse folder and list every file that matches given pattern.

        :param folder:      Folder that includes all the files to match.
        :param pattern:     Pattern that files must match (uses glob syntax). If None, will match every file.
        :param indexer:     Indexer used to index the files.
        :param recursive:   If true, the pattern '**' will match any files and zero or more directories and
                            subdirectories.
        :param sort:        Sort matched files by name.
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
        ep_playlist: int | Sequence[int] | None,
        indexer: Callable[[str | Path], HoldsVideoNodeT],
        trims: BluRayTrim | list[BluRayTrim | None] | None = None,
    ) -> None:
        """
        Parse BDMV and list every file in matching episode playlist(s).

        :param bdmv_path:       Path to the BDMV. If str or Path, it must be the folder that contains every BD volume.
                                If list of str/Path, it is the list to the folder of every volume.
                                If tuple, first value is path to BDMV folder, second is list of every volume.
        :param ep_playlist:     ID of the playlist file for the episodes, can be set for each BD volume
                                If None, heuristic will be used to find the correct playlist. This mode is experimental
                                and will probably break.
        :param indexer:         Indexer used to index the files.
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
        if ep_playlist is None:
            playlists = [self._find_episode_playlist(bd_volume) for bd_volume in self.bdmv.bd_volumes]
        else:
            playlists_idx = to_arr(ep_playlist)
            playlists_idx = normalize_list(playlists_idx, len(self.bdmv.bd_volumes), playlists_idx[-1], "ParseBD")
            playlists = [bd_vol.get_playlist(p) for bd_vol, p in zip(self.bdmv.bd_volumes, playlists_idx)]

        tr = [None] * len(self.bdmv.bd_volumes) if trims is None else trims
        tr = normalize_list(tr, len(self.bdmv.bd_volumes), None, "ParseBD")

        self.items = []
        for p, trim in zip(playlists, tr):
            volume_items = p.items

            if trim is None:
                trim = (0, len(volume_items))

            ts, te = trim
            if ts is None:
                ts = 0
            if te is None:
                te = len(volume_items)

            self.items += volume_items[ts:te]

        super().__init__([item.m2ts_file for item in self.items])

    def _find_episode_playlist(self, bd_volume: BdVolume) -> MplsFile:
        volume_playlists = bd_volume.get_playlists()
        playlist_info = dict[str, tuple[int, list[int], MplsFile]]()
        for playlist in volume_playlists:
            unique_items = set[str]()
            unique_durations = list[int]()
            for item in playlist.items:
                if item.m2ts_file not in unique_items:
                    unique_items.add(item.m2ts_file)
                    unique_durations.append(item.item_data.outtime - item.item_data.intime)

            playlist_info[playlist.mpls_file.name] = (len(unique_items), unique_durations, playlist)

        max_elements = max(playlist_info.items(), key=lambda item: item[1][0])
        max_duration = max(playlist_info.items(), key=lambda item: sum(item[1][1]))

        if max_elements[1][0] == 1:
            correct_playlist = max_duration
        elif max_duration[0] == max_elements[0]:
            correct_playlist = max_elements
        else:
            correct_playlist = max_duration
            warn(
                f"Heuristic conflict when selecting episode playlist for volume {bd_volume.volume_path}. "
                + f"Choosing playlist {correct_playlist[0]} over playlist {max_elements[0]}. Check results carefully.",
                "ParseBD",
            )

        ep_count = correct_playlist[1][0]
        duration = sum(correct_playlist[1][1]) / 45000

        debug(
            f"Playlist {correct_playlist[0]} detected for volume {bd_volume.volume_path}"
            + f" (episodes: {ep_count}, duration: {Convert.seconds2ts(duration, precision=0)}).",
            "ParseBD",
        )
        return correct_playlist[1][2]

    def get_chapter(
        self, ep_num: int, chapters_names: list[str | None] | None = None, src_file: src_file | None = None
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
                f"ParseBD.get_chapter: invalid number of chapters_names given, expected {chap_num}, got {name_num}. "
                + f"Chapters frames: {', '.join([str(f) for f in chaps_frames])}"
            )

        return chapters.set_names(chapters_names)
