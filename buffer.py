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
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtWidgets import QApplication
from core.webengine import BrowserBuffer
from core.utils import get_emacs_var, message_to_emacs
import base64
import os
import http.server
import socketserver
import threading
import tempfile
import shutil

class AppBuffer(BrowserBuffer):
    def __init__(self, buffer_id, url, arguments):
        BrowserBuffer.__init__(self, buffer_id, url, arguments, False)

        self.download_path = get_emacs_var("eaf-webengine-download-path")
        
        # 设置WebEngine权限
        self.buffer_widget.web_page.setFeaturePermission(
            QUrl("file://"),
            self.buffer_widget.web_page.Feature.MediaVideoCapture,
            self.buffer_widget.web_page.PermissionPolicy.PermissionGrantedByUser
        )
        
        # 打印WebEngine版本
        from PyQt6.QtWebEngineCore import QWebEngineProfile
        print(f"WebEngine版本: {QWebEngineProfile.defaultProfile().httpUserAgent()}")

        self.load_index_html(__file__)

    def start_http_server(self):
        """启动一个本地HTTP服务器来提供静态文件"""
        # 创建临时目录来存放应用文件
        self.temp_dir = tempfile.mkdtemp()
        
        # 复制应用文件到临时目录
        src_dir = os.path.dirname(os.path.abspath(__file__))
        dist_dir = os.path.join(src_dir, "dist")
        
        # 如果dist目录存在，复制其内容
        if os.path.exists(dist_dir):
            for item in os.listdir(dist_dir):
                src_item = os.path.join(dist_dir, item)
                dst_item = os.path.join(self.temp_dir, item)
                if os.path.isdir(src_item):
                    shutil.copytree(src_item, dst_item)
                else:
                    shutil.copy2(src_item, dst_item)
        
        # 获取一个可用端口
        with socketserver.TCPServer(("", 0), None) as s:
            port = s.server_address[1]
        
        # 创建HTTP服务器
        handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", port), handler)
        
        # 设置当前工作目录为临时目录
        os.chdir(self.temp_dir)
        
        # 在新线程中启动服务器
        self.server_thread = threading.Thread(target=httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        print(f"HTTP服务器启动在端口 {port}")
        return port

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
        """在销毁 buffer 前释放摄像头资源"""
        try:
            # 调用 JavaScript 的释放方法
            self.buffer_widget.eval_js_function("releaseCamera")
            
            # 强制清除任何悬挂的权限
            from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
            try:
                # 关闭任何可能的权限请求对话框
                self.buffer_widget.web_page.setFeaturePermission(
                    QUrl("file://"),
                    QWebEnginePage.Feature.MediaVideoCapture,
                    QWebEnginePage.PermissionPolicy.PermissionDeniedByUser
                )
                
                # 清除 WebEngine 缓存
                profile = QWebEngineProfile.defaultProfile()
                profile.clearHttpCache()
                print("已清除 WebEngine 缓存")
            except Exception as e:
                print(f"清除权限时出错: {e}")
            
            # 只有在使用HTTP服务器时才尝试关闭它
            if hasattr(self, 'server_thread') and self.server_thread and self.server_thread.is_alive():
                print("正在关闭HTTP服务器...")
                # 清理临时目录
                if hasattr(self, 'temp_dir'):
                    try:
                        shutil.rmtree(self.temp_dir)
                    except:
                        pass
        
        except Exception as e:
            print(f"释放摄像头资源时出错: {e}")
        
        # 调用父类的 destroy_buffer 方法
        super().destroy_buffer()

    @QtCore.pyqtSlot(result=bool)
    def request_camera_permission(self):
        """请求摄像头权限，可能会触发系统权限对话框"""
        try:
            print("强制请求摄像头权限...")
            # 正确获取 web_page 对象
            from PyQt6.QtWebEngineCore import QWebEnginePage
            
            # 直接设置权限，不尝试重置
            self.buffer_widget.web_page.setFeaturePermission(
                QUrl("file://"),
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )
            
            # 尝试设置 HTTP 协议权限
            self.buffer_widget.web_page.setFeaturePermission(
                QUrl("http://localhost/"),
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser
            )
            
            # 刷新页面以应用新权限
            self.buffer_widget.reload()
            return True
        except Exception as e:
            print(f"请求摄像头权限时出错: {e}")
            return False
