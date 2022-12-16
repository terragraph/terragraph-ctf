# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


class DuplicateResourceException(Exception):
    """Raise when a resource already exists"""

    def __init__(self, message, *args):
        self.message = message
        super(DuplicateResourceException, self).__init__(message, *args)


class ResourceNotFoundException(Exception):
    """Raise when a resource does not exist"""

    def __init__(self, message, *args):
        self.message = message
        super(ResourceNotFoundException, self).__init__(message, *args)


class ServerlessConfigException(Exception):
    """Raise when Serverless config is not present or malformed"""

    pass
