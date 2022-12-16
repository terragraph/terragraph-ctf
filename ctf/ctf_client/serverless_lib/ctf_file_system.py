#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


def _is_list(e):
    import typing

    return isinstance(e, typing.List)


def mkdir(path, recursive=True, **kwargs):
    import os

    if recursive:
        os.makedirs(path, **kwargs)
    else:
        os.mkdir(path, **kwargs)


def exists(path, **kwargs):
    import os.path

    return os.path.exists(path, **kwargs)


def get_json_object(path):
    import json

    with open(path, "r") as file:
        return json.load(file)


def put_json_object(path, obj):
    import json

    with open(path, "w") as file:
        return json.dump(obj, file, indent=4)


def join(*args, **kwargs):
    import os.path

    if _is_list(args[0]):
        return os.path.join(*args[0])
    return os.path.join(*args, **kwargs)


def rm(path, **kwargs):
    import os

    return os.unlink(path, **kwargs)
