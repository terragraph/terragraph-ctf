# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import logging
import os


logger = logging.getLogger(__name__)


class PluginManager(object):
    def __init__(self, in_callback=None, device_type=None, class_name=None):
        self.callback = in_callback
        self.device_type = device_type
        self.class_name = class_name

    def init_plugin(self, function_name):
        return_output = None

        try:
            module_name = ""
            # Get the module name from the device type
            # if self.device_type in [constants.CTF_DEVICE_TYPE_TERRAGRAPH]:
            #     module_name = 'Terragraph' + file_name
            if self.class_name:
                module_name = self.class_name

            # Call SKU class and its function
            return_output = self.load_plugin_function(module_name, function_name)

            # Save output_info in action result here
        except Exception as e:
            logger.exception(e)
            self.callback.append(str(e))

        # Return output
        return return_output

    def load_plugin_function(self, module_name, function_name):
        class_ = None
        try:
            # Get plugin folder path
            plugin_folder_path = os.path.join(
                os.path.dirname(__file__), "..", "plugins"
            )
            import sys

            sys.path.append(plugin_folder_path)
            import importlib

            try:
                module = importlib.import_module(module_name, plugin_folder_path)
                if module:
                    class_ = getattr(module, module_name)
                    if isinstance(function_name, list):
                        for f_name in function_name:
                            attr = getattr(class_, f_name, None)
                            if not attr:
                                class_ = None
                                break
                    else:
                        attr = getattr(class_, function_name, None)
                        if not attr:
                            class_ = None

            except Exception as e:
                self.callback.append(str(e))
                class_ = None
            finally:
                # Since we may exit via an exception, close fp explicitly.
                pass
        except Exception as e:
            self.callback.append(str(e))

        return class_
