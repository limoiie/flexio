import io
import os
from typing import Any, BinaryIO, IO, Iterable, Iterator, Literal, TextIO

StrOrBytesPath = str | bytes | os.PathLike[str] | os.PathLike[bytes]


class FlexTextIO(TextIO):
    def __init__(self, fp: IO[str] | StrOrBytesPath | int | None = None,
                 mode: str = 'rt', *, init: str | None = None,
                 encoding: str | None = None, errors: str or None = None,
                 newline: Literal['', '\n', '\r', '\r\n'] | None = None,
                 close_io: bool | None = None, **kwargs):

        if fp is None:
            name = None
            create = set('w+') <= set(mode)
            io_ = io.StringIO(str() if create else init or str())
            close_io = False if close_io is None else close_io
            mode = 'w+' if create else 'w'
            in_mem = True

        elif isinstance(fp, (os.PathLike, str, bytes, int)):
            assert 'b' not in mode
            io_ = open(fp, mode, encoding=encoding, errors=errors,
                       newline=newline, **kwargs)
            name = io_.name
            close_io = True if close_io is None else close_io
            mode = io_.mode
            in_mem = False

        else:
            name = fp.name if hasattr(fp, 'name') else None
            io_ = fp
            close_io = False if close_io is None else close_io
            mode = fp.mode if hasattr(fp, 'mode') else mode
            in_mem = isinstance(fp, io.StringIO) or (
                fp.in_mem if hasattr(fp, 'in_mem') else False)

        self._io: IO[str] = io_
        self._close_io: bool = close_io
        self._name: str | bytes | None = name
        self._mode = mode
        self._in_mem: bool = in_mem

    def __enter__(self) -> 'FlexTextIO':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_io:
            self._io.close()

    def __next__(self) -> str:
        return self._io.__next__()

    def __iter__(self) -> Iterator[str]:
        return self._io.__iter__()

    @property
    def in_mem(self):
        return self._in_mem

    def close(self) -> None:
        self._io.close()

    @property
    def closed(self) -> bool:
        return self._io.closed

    def fileno(self) -> int:
        return self._io.fileno()

    def flush(self) -> None:
        return self._io.flush()

    def isatty(self) -> bool:
        return self._io.isatty()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def name(self) -> str | int | None:
        return self._name

    def read(self, size: int = -1) -> str:
        return self._io.read(size)

    def readable(self) -> bool:
        return self._io.readable()

    def readline(self, limit: int = -1) -> str:
        return self._io.readline(limit)

    def readlines(self, hint: int = -1) -> list[str]:
        return self._io.readlines(hint)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._io.seek(offset, whence)

    def seekable(self) -> bool:
        return self._io.seekable()

    def tell(self) -> int:
        return self._io.tell()

    def truncate(self, pos: int | None = None) -> int:
        return self._io.truncate(pos)

    def writable(self) -> bool:
        return self._io.writable()

    def write(self, text: str) -> int:
        return self._io.write(text)

    def writelines(self, lines: Iterable[str]) -> None:
        return self._io.writelines(lines)

    @property
    def buffer(self) -> BinaryIO:
        return self._io.buffer if hasattr(self._io, 'buffer') else None

    @property
    def encoding(self) -> str:
        return self._io.encoding if hasattr(self._io, 'encoding') else None

    @property
    def errors(self) -> str | None:
        return self._io.errors if hasattr(self._io, 'errors') else None

    @property
    def line_buffering(self) -> int:
        return self._io.line_buffering \
            if hasattr(self._io, 'line_buffering') else None

    @property
    def newlines(self) -> Any:
        return self._io.newlines if hasattr(self._io, 'newlines') else None


class FlexBinaryIO(BinaryIO):
    def __init__(self, fp: IO[bytes] | StrOrBytesPath | int | None = None,
                 mode: str = 'rb', *, init: bytes | None = None,
                 close_io: bool | None = None, **kwargs):

        if fp is None:
            name = None
            create = set('w+') < set(mode)
            io_ = io.BytesIO(bytes() if create else init or bytes())
            close_io = False if close_io is None else close_io
            mode = 'rb+' if create else 'rb'
            in_mem = True

        elif isinstance(fp, (os.PathLike, str, bytes, int)):
            assert 'b' in mode
            io_ = open(fp, mode=mode, **kwargs)
            name = io_.name
            close_io = True if close_io is None else close_io
            mode = io_.mode
            in_mem = False

        else:
            name = fp.name if hasattr(fp, 'name') else None
            io_ = fp
            close_io = False if close_io is None else close_io
            mode = fp.mode if hasattr(fp, 'mode') else mode
            in_mem = isinstance(fp, io.BytesIO) or (
                fp.in_mem if hasattr(fp, 'in_mem') else False)

        self._io: IO[bytes] = io_
        self._close_io: bool = close_io
        self._name: str | bytes | None = name
        self._mode = mode
        self._in_mem: bool = in_mem

    def __enter__(self) -> 'FlexBinaryIO':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_io:
            self._io.close()

    def __next__(self) -> bytes:
        return self._io.__next__()

    def __iter__(self) -> Iterator[bytes]:
        return self._io.__iter__()

    @property
    def in_mem(self):
        return self._in_mem

    def close(self) -> None:
        self._io.close()

    @property
    def closed(self) -> bool:
        return self._io.closed

    def fileno(self) -> int:
        return self._io.fileno()

    def flush(self) -> None:
        return self._io.flush()

    def isatty(self) -> bool:
        return self._io.isatty()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def name(self) -> str | int | None:
        return str(self._name) \
            if isinstance(self._name, os.PathLike) else self._name

    def read(self, size: int = -1) -> bytes:
        return self._io.read(size)

    def readable(self) -> bool:
        return self._io.readable()

    def readline(self, limit: int = -1) -> bytes:
        return self._io.readline(limit)

    def readlines(self, hint: int = -1) -> list[bytes]:
        return self._io.readlines(hint)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._io.seek(offset, whence)

    def seekable(self) -> bool:
        return self._io.seekable()

    def tell(self) -> int:
        return self._io.tell()

    def truncate(self, pos: int | None = None) -> int:
        return self._io.truncate(pos)

    def writable(self) -> bool:
        return self._io.writable()

    def write(self, binary: bytes) -> int:
        return self._io.write(binary)

    def writelines(self, lines: Iterable[bytes]) -> None:
        return self._io.writelines(lines)
