#!/usr/bin/env fbpython

# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import collections.abc as collections

import pytest
from ctf.ctf_client.lib.helper_functions import dict_to_pretty_table
from prettytable import PrettyTable


@pytest.mark.parametrize(
    "dict_list, columns",
    [
        ([{"a": 1, "b": 2}], None),
        ([{"a": 1, "b": 2, "c": 3}], ["a", "c"]),
        ([{"a": 1, "b": 2, "c": 3}], {"a": "Alpha", "c": "Charlie"}),
        ([], None),
    ],
)
def test_dict_to_pretty_table(dict_list, columns):
    table = dict_to_pretty_table(dict_list, columns)

    # assert correct type was returned
    assert isinstance(table, PrettyTable)
    table_columns = table._field_names
    table_rows = table._rows

    # The table should only have as many columns as are in the columns param or in the dict_list's dicts
    if columns:
        assert len(columns) == len(table_columns)
    else:
        if dict_list:
            assert len(dict_list[0]) == len(table_columns)

    # The table should only have as many rows as the length of the dict_list
    assert len(dict_list) == len(table_rows)

    # If a mapping or filtering occured, assert that theose column names are present
    if columns:
        column_names = (
            columns.values() if isinstance(columns, collections.Mapping) else columns
        )
        assert all(col in table_columns for col in column_names)


@pytest.mark.parametrize(
    "dict_list, columns",
    [
        ([{"a": 1, "b": 2}], "FAIL"),
        ([{"a": 1, "b": 2, "c": 3}], 123),
        ([{"a": 1, "b": 2, "c": 3}], ValueError),
    ],
)
def test_dict_to_pretty_table_raises_with_bad_input(dict_list, columns):
    with pytest.raises(ValueError):
        # the function will raise ValiueError if anything other than None, List, Dict is passed for "columns"
        dict_to_pretty_table(dict_list, columns)
