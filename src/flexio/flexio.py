import os
import tempfile
from typing import Any, BinaryIO, IO, Iterable, Iterator, List, Optional, \
    TextIO, Union

FilePointer = Union[str, bytes, os.PathLike, int]
FPOrStrIO = Union[FilePointer, IO[str]]
FPOrBytesIO = Union[FilePointer, IO[bytes]]
FPOrIO = Union[FilePointer, IO[str], IO[bytes]]


def flex_open(fp: Optional[FPOrIO] = None, mode: Optional[str] = None, *,
              init: Optional[str] = None, buffering: Optional[int] = -1,
              encoding: Optional[str] = None, newline: Optional[str] = None,
              close_io: Optional[bool] = True, **kwargs):
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
    :param newline: The open newline. Only available in text mode.
    :param close_io: If close the inner io or not before exiting.
    :param kwargs: Optional open args.
    """
    if fp is None or is_file_pointer(fp):
        if mode is None:
            raise ValueError(f'Arg `Mode` should be present when `fp` is None '
                             f'or a file pointer.')

        is_binary = 'b' in mode
    else:
        if mode is not None:
            raise ValueError(f'Arg `Mode` should be absent when `fp` points to '
                             f'a file-like object.')

        is_binary = 'b' in fp.mode

    if is_binary:
        return FlexBinaryIO(fp=fp, mode=mode, init=init, buffering=buffering,
                            close_io=close_io, **kwargs)

    return FlexTextIO(fp=fp, mode=mode, init=init, buffering=buffering,
                      encoding=encoding, newline=newline, close_io=close_io,
                      **kwargs)


class FlexTextIO(TextIO):
    def __init__(self, fp: Optional[FPOrStrIO] = None,
                 mode: Optional[str] = None, *, init: Optional[str] = None,
                 buffering: Optional[int] = -1, encoding: Optional[str] = None,
                 newline: Optional[str] = None, close_io: Optional[bool] = None,
                 **kwargs):
        if mode and 'b' in mode:
            raise ValueError(f'FlexTextIO expect text mode, but got binary '
                             f'mode - `{mode}`')

        if fp is None:
            mode = mode or 'rt'
            io_ = SpooledTemporaryFile(init=init, mode=mode,
                                       buffering=buffering, encoding=encoding,
                                       newline=newline, **kwargs)
            close_io = True if close_io is None else close_io

        elif is_file_pointer(fp):
            mode = mode or 'rt'
            if init is not None:
                raise ValueError(f'Arg `init` should be absent when `fp` '
                                 f'points to a file, but got {init}')

            io_ = open(fp, mode=mode, buffering=buffering, encoding=encoding,
                       newline=newline, **kwargs)
            close_io = True if close_io is None else close_io

        else:
            if mode is not None:
                raise ValueError(f'Arg `mode` should be absent when `fp` is '
                                 f'a file-like object.')

            io_ = fp
            close_io = False if close_io is None else close_io

        self._io: IO[str] = io_
        self._close_io: bool = close_io

    def __enter__(self) -> 'FlexTextIO':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_io:
            self._io.close()

    def __next__(self) -> str:
        return self._io.__next__()

    def __iter__(self) -> Iterator[str]:
        return self._io.__iter__()

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
    def __init__(self, fp: Union[IO[bytes], FilePointer, None] = None,
                 mode: Optional[str] = None, *, init: Optional[bytes] = None,
                 buffering: Optional[int] = -1, close_io: bool = True,
                 **kwargs):
        if mode and 'b' not in mode:
            raise ValueError(f'FlexBinaryIO expect binary mode, but got text '
                             f'mode `{mode}`')

        if fp is None:
            mode = mode or 'rb'
            io_ = SpooledTemporaryFile(init=init, mode=mode,
                                       buffering=buffering, **kwargs)
            close_io = True if close_io is None else close_io

        elif is_file_pointer(fp):
            mode = mode or 'rb'
            if init is not None:
                raise ValueError(f'Arg `init` should be absent when `fp` '
                                 f'points to a file, but got {init}')

            io_ = open(fp, mode=mode, buffering=buffering, **kwargs)
            close_io = True if close_io is None else close_io

        else:
            if mode is not None:
                raise ValueError(f'Arg `mode` should be absent when `fp` is '
                                 f'a file-like object.')

            io_ = fp
            close_io = False if close_io is None else close_io

        self._io: IO[bytes] = io_
        self._close_io: bool = close_io

    def __enter__(self) -> 'FlexBinaryIO':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._close_io:
            self._io.close()

    def __next__(self) -> bytes:
        return self._io.__next__()

    def __iter__(self) -> Iterator[bytes]:
        return self._io.__iter__()

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
    def __init__(self, init: Union[str, bytes, None], **kwargs):
        super().__init__(**kwargs)

        if init:
            self._file.write(init)
            self._file.seek(0)


def is_file_pointer(obj: Any) -> bool:
    return isinstance(obj, (str, bytes, os.PathLike, int))
