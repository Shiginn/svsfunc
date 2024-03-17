from abc import ABC
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Generic, NamedTuple, TypeVar, overload

from vstools import copy_signature

from ..custom_types import IndexedT, PathLike
from ..utils import ensure_path

__all__ = ["Indexer", "IndexerCache"]

T = TypeVar("T")


class IndexerCache(NamedTuple):
    arg_name: str
    ext: str


@dataclass
class Indexer(ABC, Generic[IndexedT]):
    _index_func: Callable[[Path], IndexedT] = field(init=False, repr=False)
    _cache: IndexerCache | None = field(init=False, repr=False, default=None)

    def _get_kwargs(self, default: dict[str, Any] | None = None) -> dict[str, Any]:
        kwargs: dict[str, Any] = {key: self.__dict__.get(key) for key in self.__match_args__}  # type: ignore
        if default:
            kwargs |= default

        return kwargs

    @overload
    def index(self, source_file: list[PathLike], **indexer_overrides: Any) -> list[IndexedT]:
        ...

    @overload
    def index(self, source_file: PathLike, **indexer_overrides: Any) -> IndexedT:
        ...

    def index(self, source_file: PathLike | list[PathLike], **indexer_overrides: Any) -> IndexedT | list[IndexedT]:
        """
        Index the given file

        :param path:    Path to the file

        :return:        Indexed file
        """
        if isinstance(source_file, list):
            return [self.index(ensure_path(p), **indexer_overrides) for p in source_file]

        path = ensure_path(source_file, f"{self.__class__.__name__}.index")
        cache = {self._cache.arg_name: str(path.with_suffix(self._cache.ext))} if self._cache else None

        return self._index_func(path, **(self._get_kwargs(cache) | indexer_overrides))


    @copy_signature(index)
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.index(*args, **kwargs)

    def copy(self: T, **kwargs: Any) -> T:
        return replace(self, **kwargs)
