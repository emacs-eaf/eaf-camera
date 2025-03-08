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
from PyQt6.QtCore import QUrl
from core.webengine import BrowserBuffer
from core.utils import get_emacs_var, message_to_emacs
import base64
import os

class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, arguments):
        BrowserBuffer.__init__(self, buffer_id, url, arguments, False)

        self.download_path = get_emacs_var("eaf-webengine-download-path")
        
        # Set WebEngine permissions
        self.buffer_widget.web_page.setFeaturePermission(
            QUrl("file://"),
            self.buffer_widget.web_page.Feature.MediaVideoCapture,
            self.buffer_widget.web_page.PermissionPolicy.PermissionGrantedByUser
        )
        
        # Print WebEngine version
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        print(f"WebEngine version: {QWebEngineProfile.defaultProfile().httpUserAgent()}")

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

    def destroy_buffer(self):
        """Release camera resources before destroying buffer"""
        try:
            # Call JavaScript release method
            self.buffer_widget.eval_js_function("releaseCamera")
            
            # Force clear any hanging permissions
            from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
            try:
                # Close any possible permission request dialogs
                self.buffer_widget.web_page.setFeaturePermission(
                    QUrl("file://"),
                    QWebEnginePage.Feature.MediaVideoCapture,
                    QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
                )
                
                # Clear WebEngine cache
                profile = QWebEngineProfile.defaultProfile()
                profile.clearHttpCache()
                print("WebEngine cache cleared")
            except Exception as e:
                print(f"Error clearing permissions: {e}")
        
        except Exception as e:
            print(f"Error releasing camera resources: {e}")
        
        # Call parent class destroy_buffer method
        super().destroy_buffer()

    @QtCore.pyqtSlot(result=bool)
    def request_camera_permission(self):
        """Request camera permission, may trigger system permission dialog"""
        try:
            print("Forcing camera permission request...")
            # Correctly get web_page object
            from PyQt6.QtWebEngineCore import QWebEnginePage

            # Directly set permission, don't try to reset
            self.buffer_widget.web_page.setFeaturePermission(
                QUrl("file://"),
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

            # Try to set HTTP protocol permission
            self.buffer_widget.web_page.setFeaturePermission(
                QUrl("http://localhost/"),
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

            # Refresh page to apply new permissions
            self.buffer_widget.reload()
            return True
        except Exception as e:
            print(f"Error requesting camera permission: {e}")
            return False
