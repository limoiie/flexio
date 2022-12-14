import contextlib
import dataclasses
import os
import pathlib
from collections import namedtuple
from io import BytesIO, StringIO, UnsupportedOperation
from typing import AnyStr, Optional, Union

import pytest

from conftest import Raises, case_name
from flexio.flexio import flex_open


@dataclasses.dataclass
class Case:
    name: str
    binary: bool
    content: Union[str, bytes]
    w_content: Union[str, bytes]
    path: Union[str, pathlib.Path, None]
    fd: Optional[int]
    init: Optional[str]
    mode: Optional[str]
    close_io: Optional[bool]
    close_fd: Optional[bool]
    raises: Optional[Raises]


@pytest.fixture(scope='function')
def real_case(request, fake_local_file, faker):
    meta: 'TestFlexIo.MRMeta' = request.param
    content = fake_local_file.read_text()
    written_content = faker.text()

    if meta.binary:
        content = content.encode()
        written_content = written_content.encode()

    path = fake_local_file

    if not meta.exists:
        os.remove(path)

    return Case(
        name=meta.name,
        binary=meta.binary,
        content=content,
        w_content=written_content,
        path=path,
        fd=None,
        mode=meta.mode,
        init=None,
        close_io=meta.close_io,
        close_fd=None,
        raises=meta.raises,
    )


@pytest.fixture(scope='function')
def path_case(request, fake_local_file, faker):
    meta: 'TestFlexIo.MPMeta' = request.param
    content = fake_local_file.read_text()
    written_content = faker.text()

    if meta.binary:
        content = content.encode()
        written_content = written_content.encode()

    path = meta.path_cls(fake_local_file)

    return Case(
        name=meta.name,
        binary=meta.binary,
        content=content,
        w_content=written_content,
        path=path,
        fd=None,
        mode=meta.mode,
        init=None,
        close_io=meta.close_io,
        close_fd=None,
        raises=meta.raises,
    )


@pytest.fixture(scope='function')
def mem_case(request, faker):
    meta: 'TestFlexIo.MMMeta' = request.param
    init = faker.text() if meta.init else None
    content = init or str()
    written_content = faker.text()

    if meta.binary:
        init = init.encode() if init else None
        content = content.encode()
        written_content = written_content.encode()

    return Case(
        name=meta.name,
        binary=meta.binary,
        content=content,
        w_content=written_content,
        path=None,
        fd=None,
        mode=meta.mode,
        init=init,
        close_io=meta.close_io,
        close_fd=None,
        raises=meta.raises,
    )


@pytest.fixture(scope='function')
def fd_case(request, fake_local_file, faker):
    meta: 'TestFlexIo.MDMeta' = request.param
    content = fake_local_file.read_text()
    written_content = faker.text()

    if meta.binary:
        content = content.encode()
        written_content = written_content.encode()

    path = fake_local_file

    f = open(path, 'w')
    try:
        yield Case(
            name=meta.name,
            binary=meta.binary,
            content=content,
            w_content=written_content,
            path=path,
            fd=f.fileno(),
            mode=meta.mode,
            init=None,
            close_io=meta.close_io,
            close_fd=meta.close_fd,
            raises=meta.raises,
        )
    finally:
        try:
            f.close()
        except IOError:
            pass


class TestFlexIo:
    MRMeta = namedtuple('MetaMakeReal',
                        'exists,binary,mode,close_io,raises,name')

    cases = [
        # text existing
        MRMeta(name='read text existing',
               exists=True, binary=False, mode='rt', close_io=False,
               raises=None),
        MRMeta(name='read existing',
               exists=True, binary=False, mode='r', close_io=False,
               raises=None),
        MRMeta(name='write text existing',
               exists=True, binary=False, mode='wt', close_io=False,
               raises=None),
        MRMeta(name='write existing',
               exists=True, binary=False, mode='w', close_io=False,
               raises=None),
        MRMeta(name='write+ text existing',
               exists=True, binary=False, mode='wt+', close_io=False,
               raises=None),
        MRMeta(name='write+ existing',
               exists=True, binary=False, mode='w+', close_io=False,
               raises=None),

        # text non-existing
        MRMeta(name='read text',
               exists=False, binary=False, mode='rt', close_io=False,
               raises=Raises(exc=FileNotFoundError)),
        MRMeta(name='read',
               exists=False, binary=False, mode='r', close_io=False,
               raises=Raises(exc=FileNotFoundError)),
        MRMeta(name='write text',
               exists=False, binary=False, mode='wt', close_io=False,
               raises=None),
        MRMeta(name='write',
               exists=False, binary=False, mode='w', close_io=False,
               raises=None),
        MRMeta(name='write+ text',
               exists=False, binary=False, mode='wt+', close_io=False,
               raises=None),
        MRMeta(name='write+',
               exists=False, binary=False, mode='w+', close_io=False,
               raises=None),

        # binary existing
        MRMeta(name='read binary existing',
               exists=True, binary=True, mode='rb', close_io=False,
               raises=None),
        MRMeta(name='write binary existing',
               exists=True, binary=True, mode='wb', close_io=False,
               raises=None),
        MRMeta(name='write+ binary existing',
               exists=True, binary=True, mode='wb+', close_io=False,
               raises=None),

        # binary non-existing
        MRMeta(name='read binary',
               exists=False, binary=True, mode='rb', close_io=False,
               raises=Raises(FileNotFoundError)),
        MRMeta(name='write binary',
               exists=False, binary=True, mode='wb', close_io=False,
               raises=None),
        MRMeta(name='write+ binary',
               exists=False, binary=True, mode='wb+', close_io=False,
               raises=None),

        # incorrect usages
        MRMeta(name='write bytes to text io',
               exists=True, binary=True, mode='w', close_io=False,
               raises=Raises(exc=TypeError,
                             kwargs=dict(match='(must be )?str'))),
        MRMeta(name='write text to bytes io',
               exists=True, binary=False, mode='wb', close_io=False,
               raises=Raises(exc=TypeError, kwargs=dict(
                   match='bytes-like object is required'))),
    ]

    @pytest.mark.parametrize('real_case', cases, indirect=True, ids=case_name)
    def test_make_with_file_io(self, real_case: Case):
        case = real_case

        with pytest.raises(case.raises.exc, **case.raises.kwargs) \
                if case.raises else contextlib.nullcontext():
            with case.path.open(mode=case.mode) as f:
                with flex_open(f, close_io=case.close_io) as io:
                    common_test_flexio(io, case.mode, case.content,
                                       case.w_content)

                assert io.closed == (
                    False if case.close_io is None else case.close_io)
                assert set(io.mode) == refactor_mode_as_open(case.mode)
                assert io.name == str(case.path)

            assert io.closed == True

    @pytest.mark.parametrize('real_case', cases, indirect=True, ids=case_name)
    def test_make_with_in_memory_io(self, real_case: Case):
        case = real_case

        with pytest.raises(case.raises.exc, **case.raises.kwargs) \
                if case.raises else contextlib.nullcontext():
            binary_io = 'b' in case.mode

            if 'r' in case.mode:
                with open(case.path, mode='rb' if binary_io else 'r') as f:
                    data: AnyStr = f.read()
            else:
                data = b'' if binary_io else ''

            with BytesIO(data) if binary_io else StringIO(data) as in_memory:
                with flex_open(in_memory, mode=case.mode,
                               close_io=case.close_io) as io:
                    common_test_flexio(io, case.mode, case.content,
                                       case.w_content, unsupported=False)

                assert io.closed == (
                    False if case.close_io is None else case.close_io)
                assert set(io.mode) == set(case.mode)
                assert io.name is None

            assert io.closed == True

    @pytest.mark.parametrize('real_case', cases, indirect=True, ids=case_name)
    def test_make_with_path(self, real_case: Case):
        case = real_case

        with pytest.raises(case.raises.exc, **case.raises.kwargs) \
                if case.raises else contextlib.nullcontext():
            with flex_open(case.path, mode=case.mode,
                           close_io=case.close_io) as io:
                common_test_flexio(io, case.mode, case.content, case.w_content)

            assert io.closed == (
                True if case.close_io is None else case.close_io)
            assert set(io.mode) == refactor_mode_as_open(case.mode)
            assert io.name == str(case.path)

    MPMeta = namedtuple('MetaMakeVariousPath',
                        'path_cls,binary,mode,close_io,raises,name')
    cases = [
        # text
        MPMeta(name='write+ None',
               path_cls=str, binary=False, mode='wt+', close_io=False,
               raises=None),
        MPMeta(name='write+ empty string',
               path_cls=bytes, binary=False, mode='wt+', close_io=False,
               raises=None),
        MPMeta(name='write+ initial string',
               path_cls=pathlib.Path, binary=False, mode='wt+', close_io=False,
               raises=None),

        # binary
        MPMeta(name='write+ None bytes',
               path_cls=str, binary=True, mode='wb+', close_io=False,
               raises=None),
        MPMeta(name='write+ empty bytes',
               path_cls=bytes, binary=True, mode='wb+', close_io=False,
               raises=None),
        MPMeta(name='write+ initial bytes',
               path_cls=pathlib.Path, binary=True, mode='wb+', close_io=False,
               raises=None),
    ]

    @pytest.mark.parametrize('path_case', cases, indirect=True, ids=case_name)
    def test_make_with_various_path(self, path_case: Case):
        case = path_case

        with pytest.raises(case.raises.exc, **case.raises.kwargs) \
                if case.raises else contextlib.nullcontext():
            with flex_open(case.path, mode=case.mode,
                           close_io=case.close_io) as io:
                common_test_flexio(io, case.mode, case.content, case.w_content)

            assert io.closed == (
                True if case.close_io is None else case.close_io)
            assert set(io.mode) == refactor_mode_as_open(case.mode)
            assert str(io.name) == str(case.path)

    MDMeta = namedtuple('MetaMakeFd',
                        'binary,mode,close_fd,close_io,raises,name')
    cases = [
        # text
        MDMeta(name='text not-close_fd close_io',
               binary=False, mode='w+', close_fd=False, close_io=True,
               raises=None),
        MDMeta(name='text close_fd not-close_io',
               binary=False, mode='w+', close_fd=True, close_io=False,
               raises=None),
        MDMeta(name='text close_fd close_io',
               binary=False, mode='w+', close_fd=True, close_io=True,
               raises=None),

        # binary
        MDMeta(name='binary not-close_fd close_io',
               binary=True, mode='wb+', close_fd=False, close_io=True,
               raises=None),
        MDMeta(name='binary close_fd not-close_io',
               binary=True, mode='wb+', close_fd=True, close_io=False,
               raises=None),
        MDMeta(name='binary close_fd close_io',
               binary=True, mode='wb+', close_fd=True, close_io=True,
               raises=None),
    ]

    @pytest.mark.parametrize('fd_case', cases, indirect=True, ids=case_name)
    def test_make_with_fd(self, fd_case: Case):
        case = fd_case

        with pytest.raises(case.raises.exc, **case.raises.kwargs) \
                if case.raises else contextlib.nullcontext():
            with flex_open(case.fd, mode=case.mode, close_io=case.close_io,
                           closefd=case.close_fd) as io:
                common_test_flexio(io, case.mode, case.content, case.w_content)

            assert io.closed == (
                True if case.close_io is None else case.close_io)
            assert set(io.mode) == refactor_mode_as_open(case.mode)
            assert io.name == case.fd

    MMMeta = namedtuple('MetaMakeInMemory',
                        'init,binary,mode,close_io,raises,name')
    cases = [
        # text
        MMMeta(name='write text in-memory',
               init=True, binary=False, mode='w', close_io=False,
               raises=None),
        MMMeta(name='write+ text in-memory',
               init=True, binary=False, mode='w+', close_io=True,
               raises=None),
        MMMeta(name='read text in-memory',
               init=True, binary=False, mode='r', close_io=True,
               raises=None),
        MMMeta(name='read+ text in-memory',
               init=True, binary=False, mode='r+', close_io=False,
               raises=None),

        # binary
        MMMeta(name='read binary in-memory',
               init=True, binary=True, mode='rb', close_io=True,
               raises=None),
        MMMeta(name='read+ binary in-memory',
               init=True, binary=True, mode='rb+', close_io=False,
               raises=None),
        MMMeta(name='write binary in-memory',
               init=True, binary=True, mode='wb', close_io=False,
               raises=None),
        MMMeta(name='write binary in-memory',
               init=True, binary=True, mode='wb+', close_io=True,
               raises=None),

        # misc with none init
        MMMeta(name='write text in-memory without init',
               init=None, binary=False, mode='w', close_io=False,
               raises=None),
        MMMeta(name='read+ binary in-memory without init',
               init=None, binary=True, mode='rb+', close_io=False,
               raises=None),
    ]

    @pytest.mark.parametrize('mem_case', cases, indirect=True, ids=case_name)
    def test_make_in_memory(self, mem_case: Case):
        case = mem_case

        with pytest.raises(case.raises.exc, **case.raises.kwargs) \
                if case.raises else contextlib.nullcontext():
            with flex_open(mode=case.mode, init=case.init,
                           close_io=case.close_io) as io:
                common_test_flexio(io, case.mode, case.content, case.w_content,
                                   unsupported=False)

            assert io.closed == case.close_io
            assert set(io.mode) == set(case.mode)
            assert io.name is None


def common_test_flexio(io, mode, content, written_content, unsupported=True):
    if 'r' in mode and '+' not in mode:
        assert io.read() == content

        if unsupported:
            with pytest.raises(UnsupportedOperation):
                io.write(written_content)

    elif 'r' in mode and '+' in mode:
        # r+ is writable
        assert io.read() == content
        assert io.write(written_content) == len(written_content)

    elif 'w' in mode and '+' not in mode:
        if unsupported:
            with pytest.raises(UnsupportedOperation):
                io.read()

        assert io.write(written_content) == len(written_content)

    elif 'w' in mode and '+' in mode:
        assert io.write(written_content) == len(written_content)


def refactor_mode_as_open(mode):
    mode = set(mode)
    if set('wb+') <= mode:
        # open will rewrite 'wb+' as 'rb+'
        mode = mode - {'w'} | {'r'}

    return mode
