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

from PyQt6.QtCore import Qt, QSizeF
from PyQt6.QtGui import QBrush
from PyQt6.QtGui import QColor
from PyQt6.QtMultimedia import QMediaDevices, QCamera, QMediaCaptureSession, QImageCapture
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QFrame
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from core.buffer import Buffer
from core.utils import message_to_emacs, get_emacs_var
from pathlib import Path
import time
import os

class AppBuffer(Buffer):
    def __init__(self, buffer_id, url, arguments):
        Buffer.__init__(self, buffer_id, url, arguments, True)

        self.camera_save_path = get_emacs_var("eaf-camera-save-path")

        self.add_widget(CameraWidget(QColor(self.theme_background_color)))

    def all_views_hide(self):
        # Need stop camera if all view will hide, otherwise camera will crash.
        self.buffer_widget.camera.stop()

    def some_view_show(self):
        # Re-start camero after some view show.
        self.buffer_widget.camera.start()

    def take_photo(self):
        if os.path.exists(os.path.expanduser(self.camera_save_path)):
            location = self.camera_save_path
        else:
            location = "~/Downloads"
        result = self.buffer_widget.take_photo(location)
        if result:
            message_to_emacs("Captured Photo at " + location)

    def destroy_buffer(self):
        self.buffer_widget.stop_camera()

        super().destroy_buffer()

class CameraWidget(QWidget):

    def __init__(self, background_color):
        QWidget.__init__(self)

        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(QBrush(background_color))
        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.graphics_view.setFrameStyle(QFrame.Shape.NoFrame)
        self.graphics_view.scale(-1, 1) # this make live video from camero mirror.
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.graphics_view)

        # Set the default camera.
        self.camera = QCamera(QMediaDevices.defaultVideoInput())
        
        self.image_capture = QImageCapture(self.camera)
        
        self.media_capture_session = QMediaCaptureSession()
        self.media_capture_session.setCamera(self.camera)
        self.media_capture_session.setVideoOutput(self.video_item)
        self.media_capture_session.setImageCapture(self.image_capture)
        
        self.camera.start()

    def resizeEvent(self, event):
        self.video_item.setSize(QSizeF(event.size().width(), event.size().height()))
        QWidget.resizeEvent(self, event)

    def take_photo(self, camera_save_path):
        save_path = str(Path(os.path.expanduser(camera_save_path)))
        photo_path = os.path.join(save_path, "EAF_Camera_Photo_" + time.strftime("%Y%m%d_%H%M%S", time.localtime(int(time.time()))))
        return self.image_capture.captureToFile(photo_path)

    def stop_camera(self):
        self.camera.stop()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    import signal
    app = QApplication(sys.argv)

    test = CameraWidget(QColor(0, 0, 0, 255))
    test.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    sys.exit(app.exec_())
