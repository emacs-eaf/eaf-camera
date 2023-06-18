#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2018 Andy Stewart
#
# Author:     Andy Stewart <lazycat.manatee@gmail.com>
# Maintainer: Andy Stewart <lazycat.manatee@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt6 import QtCore
from core.webengine import BrowserBuffer
from core.utils import get_emacs_var, message_to_emacs
import base64
import os

class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, arguments):
        BrowserBuffer.__init__(self, buffer_id, url, arguments, False)

        self.download_path = get_emacs_var("eaf-webengine-download-path")

        self.load_index_html(__file__)

    @QtCore.pyqtSlot(str)
    def save_screenshot(self, base64_string):
        path = os.path.expanduser(os.path.join(self.download_path, "screenshot.png"))
        self.save_base64_image(base64_string, path)

        message_to_emacs(f"Save screenshot to: {path}")

    def save_base64_image(self, base64_string, file_path):
        # Remove "data:image/png;base64," if it's included in the string
        if base64_string.startswith("data:image/png;base64,"):
            base64_string = base64_string[len("data:image/png;base64,"):]

        # Decode the Base64 string to bytes
        image_data = base64.b64decode(base64_string)

        with open(file_path, "wb") as f:
            f.write(image_data)
