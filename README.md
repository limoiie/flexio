# FlexIO

[![AutoSerde unit tests](https://github.com/limoiie/flexio/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/limoiie/flexio/actions?branch=master)

A flexible IO object that wraps path, file or fd.

## Get started

### Install from source

Open a terminal, and run:

```shell
pip install git+https://github.com/limoiie/flexio.git@master
```

### Introduction

FlexIO can wrap either path, or file, or io, or fd into an io object:

```python
from flexio import FlexTextIO

with FlexTextIO('/path/to/file', mode='w+') as file_io:
    file_io.write('some logs to file')

with FlexTextIO() as in_mem_io:
    in_mem_io.write('some logs to memory')

with FlexTextIO(in_mem_io) as io:
    io.read()
```