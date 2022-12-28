import os
import tempfile
from typing import Any, BinaryIO, IO, Iterable, Iterator, List, Optional, \
    TextIO, Union

FilePointer = Union[str, bytes, os.PathLike, int]


def flex_open(fp: Optional[FilePointer] = None, mode: str = 'rt', *,
              init: Optional[str] = None, buffering: Optional[int] = -1,
              encoding: Optional[str] = None, errors: Optional[str] = None,
              newline: Optional[str] = None, close_io: bool = True, **kwargs):
    """
    Open given file pointer, and return a file-like object.

    The file pointer could either
    - be a path-like object pointing to a file path; or
    - be an int value which is the file descriptor; or
    - be None, in this case, a temporary file shall be created.

    :param fp: The file pointer.
    :param mode: The open mode.
    :param init: Used for initializing the temporary file when fp is None.
    :param buffering: The open buffering.
    :param encoding: The open encoding. Only available in text mode.
    :param errors: The open errors. Only available in text mode.
    :param newline: The open newline. Only available in text mode.
    :param close_io: If close the inner io or not before exiting.
    :param kwargs: Optional open args.
    """

    if 'b' in mode:
        return FlexBinaryIO(fp=fp, mode=mode, init=init, buffering=buffering,
                            close_io=close_io, **kwargs)

    return FlexTextIO(fp=fp, mode=mode, init=init, buffering=buffering,
                      encoding=encoding, errors=errors, newline=newline,
                      close_io=close_io, **kwargs)


class FlexTextIO(TextIO):
    def __init__(self, fp: Optional[FilePointer] = None, mode: str = 'rt',
                 *, init: Optional[str] = None, buffering: Optional[int] = -1,
                 encoding: Optional[str] = None, errors: Optional[str] = None,
                 newline: Optional[str] = None, close_io: bool = True,
                 **kwargs):

        if 'b' in mode:
            raise ValueError(
                f'FlexTextIO expect text mode, but got binary mode {mode}')

        if fp is None:
            io_ = SpooledTemporaryFile(init=init, mode=mode,
                                       buffering=buffering, encoding=encoding,
                                       errors=errors, newline=newline, **kwargs)

        else:
            assert isinstance(fp, (os.PathLike, str, bytes, int))
            if init is not None:
                raise ValueError(f'Arg `init` should be absent when `fp` '
                                 f'points to a file, but got {init}')

            io_ = open(fp, mode, buffering=buffering, encoding=encoding,
                       errors=errors, newline=newline, **kwargs)

        self._io: IO[str] = io_
        self._close_io: bool = close_io
        self._in_mem: bool = fp is None

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
        return self._io.mode

    @property
    def name(self) -> Union[str, int, None]:
        return self._io.name

    def read(self, size: int = -1) -> str:
        return self._io.read(size)

    def readable(self) -> bool:
        return self._io.readable()

    def readline(self, limit: int = -1) -> str:
        return self._io.readline(limit)

    def readlines(self, hint: int = -1) -> List[str]:
        return self._io.readlines(hint)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._io.seek(offset, whence)

    def seekable(self) -> bool:
        return self._io.seekable()

    def tell(self) -> int:
        return self._io.tell()

    def truncate(self, pos: Optional[int] = None) -> int:
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
    def errors(self) -> Optional[str]:
        return self._io.errors if hasattr(self._io, 'errors') else None

    @property
    def line_buffering(self) -> int:
        return self._io.line_buffering \
            if hasattr(self._io, 'line_buffering') else None

    @property
    def newlines(self) -> Any:
        return self._io.newlines if hasattr(self._io, 'newlines') else None


class FlexBinaryIO(BinaryIO):
    def __init__(self, fp: Optional[FilePointer] = None, mode: str = 'rb',
                 *, init: Optional[bytes] = None, buffering: Optional[int] = -1,
                 close_io: bool = True, **kwargs):
        if 'b' not in mode:
            raise ValueError(
                f'FlexBinaryIO expect binary mode, but got text mode {mode}')

        if fp is None:
            io_ = SpooledTemporaryFile(init=init, mode=mode,
                                       buffering=buffering, **kwargs)

        else:
            if not isinstance(fp, (os.PathLike, str, bytes, int)):
                raise ValueError(f'Arg `fp` should be an instance of '
                                 f'os.PathLike, str, bytes, int, or None')

            if init is not None:
                raise ValueError(f'Arg `init` should be absent when `fp` '
                                 f'points to a file, but got {init}')

            io_ = open(fp, mode=mode, buffering=buffering, **kwargs)

        self._io: IO[bytes] = io_
        self._close_io: bool = close_io
        self._in_mem: bool = fp is None

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
        return self._io.mode

    @property
    def name(self) -> Union[str, int, None]:
        return self._io.name

    def read(self, size: int = -1) -> bytes:
        return self._io.read(size)

    def readable(self) -> bool:
        return self._io.readable()

    def readline(self, limit: int = -1) -> bytes:
        return self._io.readline(limit)

    def readlines(self, hint: int = -1) -> List[bytes]:
        return self._io.readlines(hint)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._io.seek(offset, whence)

    def seekable(self) -> bool:
        return self._io.seekable()

    def tell(self) -> int:
        return self._io.tell()

    def truncate(self, pos: Optional[int] = None) -> int:
        return self._io.truncate(pos)

    def writable(self) -> bool:
        return self._io.writable()

    def write(self, binary: bytes) -> int:
        return self._io.write(binary)

    def writelines(self, lines: Iterable[bytes]) -> None:
        return self._io.writelines(lines)


class SpooledTemporaryFile(tempfile.SpooledTemporaryFile):
    # noinspection PyShadowingBuiltins
    # noinspection PyUnresolvedReferences
    def __init__(self, init: Union[str, bytes, None], max_size=0, mode='w+b',
                 buffering=-1, encoding=None, newline=None, suffix=None,
                 prefix=None, dir=None, *, errors=None):
        super().__init__(max_size=max_size, mode=mode, buffering=buffering,
                         encoding=encoding, newline=newline, suffix=suffix,
                         prefix=prefix, dir=dir, errors=errors)

        if init:
            self._file.write(init)
            self._file.seek(0)
