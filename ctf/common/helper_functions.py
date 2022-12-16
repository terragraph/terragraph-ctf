# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import ast
import base64
import importlib.util
import logging
import os


logger = logging.getLogger(__name__)


def safe_trailing_slash(url_snippet):
    return url_snippet.rstrip("/") + "/"


def create_full_path(dir_path, full_path):
    full_path_file = os.path.basename(full_path.replace("\\", os.sep))
    dir_path = os.path.join(dir_path, full_path_file)
    return dir_path


def get_driver_class_obj(dir_path, file_name):
    class_obj = None
    try:
        temp_file_location = f"{dir_path}/{file_name}"
        spec = importlib.util.spec_from_file_location(file_name, temp_file_location)
        imported_obj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imported_obj)

        class_obj_name = get_class_obj_name(temp_file_location)
        class_obj = getattr(
            imported_obj,
            class_obj_name,
        )
    except Exception as e:
        logger.exception(f"Error retrieving driver class object: {e}")
    return class_obj


def get_class_obj_name(file_name):
    with open(file_name, "r") as fileObject:
        text = fileObject.read()
        p = ast.parse(text)
        node = ast.NodeVisitor()
        for node in ast.walk(p):
            if isinstance(node, ast.ClassDef):
                class_obj_name = node.name
                break
    return class_obj_name


def b64_decode_and_write_file(temp_dir, file_name, file_content):
    with open(os.path.join(f"{temp_dir}/{file_name}"), "w") as driver_file:
        driver_file.write(base64.b64decode(file_content).decode("utf-8"))
        driver_file.close()


def paginate(result_set, page_no, page_offset=10):
    """
    Function to bind the data in pagination format.
    :param result_set: contains the result/data which needs to bind in
    paginate format.
    :param page_no: contains the page number which is used to bind the data
    for that page number.
    :param page_offset: contains the offset for page, means how many
    entries/results should be added into the paginated result.
    :return: returns the result set with paginated data.
    """
    try:
        from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

    except ImportError:
        print("Paginator: EmptyPage, PageNotAnInteger, Paginator import error")
    page_offset = int(page_offset)
    if page_offset <= 0:
        page_offset = 1
    page_no = int(page_no)
    # Code for pagination
    paginator = Paginator(result_set, page_offset)
    page = int(page_no)
    total_no_of_records = paginator.count
    try:
        result_set = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        result_set = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        result_set = paginator.page(paginator.num_pages)

    # Total number of pages
    total_pages = paginator.num_pages

    # Add above params into dictionary
    pagination_dict = {
        "total_no_of_pages": total_pages,
        "total_no_of_records": total_no_of_records,
        "current_page": int(page_no),
        "current_page_offset": int(page_offset),
    }
    return result_set, pagination_dict
