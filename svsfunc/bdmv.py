from __future__ import annotations

import os
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Sequence

from pyparsebluray import mpls
from pytimeconv import Convert

from .utils import ensure_path

__all__ = ["BDMV", "BdVolume", "MplsItem", "MplsFile"]


@dataclass
class BDMV:
    """Represent BDMV with multiple volumes"""

    bdmv_folder: Path
    """Path to the BDMV folder"""

    bd_volumes: list["BdVolume"]
    """List of every BD volume of the BDMV"""

    @classmethod
    def from_path(cls, path: str | Path) -> "BDMV":
        """
        Searches subdirectories of the given path to find BD volumes and create BDMV

        :param path:    Path to the BDMV folder

        :return:        BDMV object
        """
        path = ensure_path(path, "BDMV.from_path")
        subdirs = [subdir for subdir in path.iterdir() if subdir.is_dir()]
        bd_volumes: list[BdVolume] = [vol for subdir in subdirs if (vol := cls._find_bd_volume(subdir)) is not None]
        return BDMV(path, bd_volumes)

    @classmethod
    def from_volumes(
        cls, bd_volumes: Sequence[str | Path | "BdVolume"], bdmv_folder: str | Path | None = None
    ) -> "BDMV":
        """
        Uses BD volumes to create BDMV object.

        :param bd_volumes:      List of all the BD volumes. Can be :py:class:`svsfunc.mpls.BdVolume` or path to BD
                                volume
        :param bdmv_folder:     Folder that contains all the BD volumes, defaults to None. If None, will use the last
                                common folder of every volume

        :return:                BDMV object
        """
        volumes = [BdVolume.from_path(bd_vol) if isinstance(bd_vol, str | Path) else bd_vol for bd_vol in bd_volumes]

        if bdmv_folder is not None:
            return BDMV(ensure_path(bdmv_folder, "BDMV.from_volumes"), volumes)

        # finding common path of all volume, most likely to be the bdmv folder
        all_path = [vol.volume_path.parts for vol in volumes]
        path_parts = [path_part[0] for path_part in zip(*all_path) if len(set(path_part)) == 1]
        common_path = ensure_path(Path(*path_parts), "BDMV.from_volumes")

        return BDMV(common_path, volumes)

    @classmethod
    def _find_bd_volume(cls, root_dir: Path) -> "BdVolume" | None:
        subdirs = [x.name for x in root_dir.iterdir() if x.is_dir()]

        if "BDMV" in subdirs and "CERTIFICATE" in subdirs:
            return BdVolume.from_path(root_dir)

        for subdir in subdirs:
            path = cls._find_bd_volume(root_dir / subdir)

            if path is not None:
                return path

        return None


@dataclass
class BdVolume:
    """
    Represent a BD volume. A folder is considered a BD volume if it has a ``BDMV`` folder and a ``CERTIFICATE`` folder.
    """

    volume_path: Path
    """Path to this volume"""

    mpls_folder: Path
    """Path to the ``PLAYLIST`` folder"""

    m2ts_folder: Path
    """Path to the ``STREAM`` folder"""

    @classmethod
    def from_path(cls, path: str | Path) -> "BdVolume":
        """
        Create a BdVolume object from the given path

        :param path:            Path to BD volume

        :raises ValueError:     If path is not a valid BD volume

        :return:                BdVolume object
        """
        path = ensure_path(path, "BdVolume.from_path")

        bdmv_folder = path / "BDMV"
        certificate_folder = path / "CERTIFICATE"

        if not (bdmv_folder.exists() and certificate_folder.exists()):
            raise ValueError("BdVolume.from_path: input path is not a valid BD volume")

        mpls_folder = bdmv_folder / "PLAYLIST"
        m2ts_folder = bdmv_folder / "STREAM"

        return BdVolume(path, mpls_folder.resolve(), m2ts_folder.resolve())

    def get_playlist(self, playlist_idx: int) -> "MplsFile":
        """
        Get the a playlist of this BD volume

        :param playlist_idx:    Id of the playlist

        :return:                MplsFile object
        """
        playlist_id = str(playlist_idx).zfill(5)
        files = list(self.mpls_folder.glob(f"{playlist_id}.mpls"))

        if len(files) < 0:
            raise ValueError(f"BdVolume.get_playlist: No playlist file found with id {playlist_id}.")
        elif len(files) > 1:
            raise ValueError(f"BdVolume.get_playlist: Multitple files found with id {playlist_id}.")
        else:
            playlist_file = files[0]

        return MplsFile.parse(playlist_file, self.m2ts_folder)

    def get_playlists(self) -> list["MplsFile"]:
        """
        Get every playlist of this BD volume

        :return: List of playlist of this BD volume
        """
        return [MplsFile.parse(file, self.m2ts_folder) for file in self.mpls_folder.glob("*.mpls")]


@dataclass
class MplsFile:
    """Represent a MPLS file (BD playlist)"""

    mpls_file: Path
    """Path to this mpls file"""

    items: list["MplsItem"]
    """List of all the items of this playlist"""

    @classmethod
    def parse(cls, mpls_file: str | Path, m2ts_folder: str | Path) -> "MplsFile":
        """
        Parse playlist file to get its items

        :param mpls_file:       Path to the MPLS file to parse
        :param m2ts_folder:     Path to the ``STREAM`` folder of the BDMV

        :raises ValueError:     If the playlist does not have any play item
        :raises ValueError:     If the playlist does not have any playlist marks
        :raises ValueError:     If the playlist does not have path to an item
        :raises ValueError:     If the playlist does not have the framerate of an item (only if chapters are present)
        :raises ValueError:     If an item of the playlist has an unknonw framerate (only if chapters are present)

        :return:                MplsFile object
        """
        mpls_file = ensure_path(mpls_file, "MplsFile.parse")
        m2ts_folder = ensure_path(m2ts_folder, "MplsFile.parse")

        # taken from vardautomation and modified
        with mpls_file.open('rb') as file:
            header = mpls.load_movie_playlist(file)

            file.seek(header.playlist_start_address, os.SEEK_SET)
            items = mpls.load_playlist(file).play_items

            if items is None:
                raise ValueError(f"MplsFile.parse: File {mpls_file} does not have play items")

            file.seek(header.playlist_mark_start_address, os.SEEK_SET)
            marks = mpls.load_playlist_mark(file).playlist_marks

            if marks is None:
                raise ValueError(f"MplsFile.parse: File {mpls_file} does not have playlist marks")

        mpls_items = list[MplsItem]()
        for i, item in enumerate(items):
            # get item path
            file_name = item.clip_information_filename
            file_ext = item.clip_codec_identifier

            if (file_name or file_ext) is None:
                raise ValueError(f"MplsFile.parse: Could not locate file of item {i} of playlist {mpls_file}")

            file_path = ensure_path(m2ts_folder / f"{file_name}.{file_ext}", "MplsFile.parse")

            # all marks associated with the current file, sorted by timestamp
            item_marks = sorted(
                [mark for mark in marks if mark.ref_to_play_item_id == i],
                key=lambda x: x.mark_timestamp
            )

            # offset from start of bd to start of current item
            if item.intime is None:
                raise ValueError(f"MplsFile.parse: Could not locate intime of item {i} of playlist {mpls_file}")

            offset = item.intime if not item_marks else min(item_marks[0].mark_timestamp, item.intime)

            # Extract the fps and store it
            item_chapters = list[int]()
            if not (
                item.stn_table and item.stn_table.length != 0 and                      # stn table is present
                item.stn_table.prim_video_stream_entries and                           # stn table has video streams
                (fps_n := item.stn_table.prim_video_stream_entries[0][1].framerate)    # stn table has 1st video stream fps  # noqa: E501
            ):
                raise ValueError(
                    "MplsFile.parse: Could not locate video stream framerate of item " +
                    f"{item.clip_information_filename} of file {mpls_file}"
                )

            # find item fps
            try:
                fps = mpls.FRAMERATE[fps_n]
            except AttributeError:
                raise ValueError(
                    f"MplsFile.parse: Unknown framerate {fps_n} for item {item.clip_information_filename} of " +
                    f"file {mpls_file}."
                )

            # get chapters
            for item_mark in item_marks:
                item_chapters.append(Convert.seconds2f((item_mark.mark_timestamp - offset) / 45000, fps))

            chapter = MplsItem(file_path, item_chapters, fps, item, item_marks)
            mpls_items.append(chapter)

        return MplsFile(mpls_file.resolve(), mpls_items)


@dataclass
class MplsItem:
    """Reprensent an item of a MPLS file."""

    m2ts_file: Path
    """Path to the M2TS file"""

    chapters: list[int]
    """List of the chapters of this item"""

    framerate: Fraction
    """Framerate of this item"""

    item_data: mpls.PlayItem
    """RAW data of this item. See `pyparsebluray <https://github.com/Ichunjo/pyparsebluray>`_ for more info."""

    item_marks: list[mpls.PlaylistMark]
    """
    List of playlist marks refering to this item. See `pyparsebluray <https://github.com/Ichunjo/pyparsebluray>`_
    for more info.
    """

    def chapters_timestamp(self, precison: int = 3) -> list[str]:
        """
        Get the chapters in timestamp format (HH:mm:ss.xxx)

        :param precison:    Rouding precision, must be a multiple of 3 (can be 0). Defaults to 3

        :return:            List of timestamps
        """
        return [Convert.f2ts(chapter, self.framerate, precision=precison) for chapter in self.chapters]
