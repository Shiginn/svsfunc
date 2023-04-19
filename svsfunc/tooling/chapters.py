from __future__ import annotations

__all__ = ["ChapterTooling"]

from typing import Sequence, Type, Union, cast

from vardautomation import Chapter, MatroskaXMLChapters, OGMChapters, VPath

from .base import BaseEncoder

ChaptersFormat = Union[MatroskaXMLChapters, OGMChapters]


class ChapterTooling(BaseEncoder):
    """Tools for generating chapter files"""

    def make_chapters(
        self,
        chapters: list[int] | list[Chapter],
        chapters_names: Sequence[str | None] | None = None,
        format: Type[ChaptersFormat] = MatroskaXMLChapters,
        path: str | VPath | None = None,
        shift_time: int | None = None,
    ) -> None:
        """
        Create a chapter file from list of Chapter or int.

        :param chapters:            List of chapters.
        :param chapters_names:      Overrides the default chapters name.
        :param format:              Chapter file format. Default to Matroska XML Chapters.
        :param path:                Override chapter file path.
        :param shift_time:          Custom shift for all of the chapters in number of frames. Positive shift means
                                    chapters will start latter, negative means earlier. If None, use FileInfo trims.
        """

        if path is not None:
            if isinstance(path, str):
                path = VPath(path)
            self.file.chapter = path
        elif self.file.chapter is None:
            raise TypeError("ChapterEncoder.make_chapters: file.chapter is None")

        if all(isinstance(chapter, int) for chapter in chapters):
            chapters = [Chapter(f"Chapter {i}", f, None) for i, f in enumerate(chapters, 1)]  # type: ignore
            if shift_time is None:  # shift is forced to 0 if None because we assume frames are taken on the cut clip
                shift_time = 0

        elif any(not isinstance(chapter, Chapter) for chapter in chapters):
            raise TypeError("ChapterEncoder.make_chapters: chapters must be all int or chapter")

        chapters = cast(list[Chapter], chapters)

        chapter_file = format(self.file.chapter)
        chapter_file.create(chapters, self.clip.fps)

        if chapters_names is not None:
            chapter_file.set_names(chapters_names)

        if shift_time is None:
            shift_time = self.get_offset(self.file)

        chapter_file.shift_times(shift_time, self.clip.fps)
