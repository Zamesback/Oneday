#!/usr/bin/env python3
"""OneDay 一日 - macOS 桌面版入口

在后台启动内置服务器，用无边框原生窗口加载应用。
支持原生语音识别（SFSpeechRecognizer），弥补 WKWebView 不支持 Web Speech API 的问题。
"""
import os
import sys
import threading
import time
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

# 桌面版数据目录：打包后 _MEIPASS 只读，数据须放用户目录（首次运行自动迁移）
DATA_ROOT = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'OneDay')
os.environ.setdefault('ONEDAY_DATA_DIR', os.path.join(DATA_ROOT, 'data'))
os.environ.setdefault('ONEDAY_WALLPAPER_DIR', os.path.join(DATA_ROOT, 'wallpapers'))

import shutil
from pathlib import Path


def migrate_data_if_needed():
    """首次运行时，把随包附带的示例数据迁移到用户数据目录"""
    user_data = Path(os.environ['ONEDAY_DATA_DIR'])
    user_data.mkdir(parents=True, exist_ok=True)
    user_wallpapers = Path(os.environ['ONEDAY_WALLPAPER_DIR'])
    user_wallpapers.mkdir(parents=True, exist_ok=True)

    # 只在用户数据目录为空时迁移（不覆盖用户已有数据）
    if not any(user_data.iterdir()):
        src_data = Path(APP_DIR) / 'data'
        if src_data.exists():
            for f in src_data.iterdir():
                if f.is_file() and f.suffix in ('.json',):
                    try:
                        shutil.copy2(str(f), str(user_data / f.name))
                        print(f'[桌面版] 迁移示例数据: {f.name}')
                    except Exception as e:
                        print(f'[桌面版] 迁移 {f.name} 失败: {e}')
        src_wp = Path(APP_DIR) / 'assets' / 'generated'
        if src_wp.exists():
            for f in src_wp.iterdir():
                if f.is_file():
                    try:
                        shutil.copy2(str(f), str(user_wallpapers / f.name))
                    except Exception:
                        pass


import server

# 桌面版使用独立动态端口（避免与其他服务冲突，如 agent-collab-dev 占用 8766）
def find_free_port(start=8771):
    """从 start 开始找第一个空闲端口"""
    import socket
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start

DESKTOP_PORT = find_free_port()


# ===== 原生语音识别（macOS SFSpeechRecognizer）=====
class SpeechBridge:
    """封装 macOS 原生语音识别：SFSpeechRecognizer + AVAudioEngine"""

    def __init__(self, window=None):
        self._window = window
        self._recognizer = None
        self._engine = None
        self._request = None
        self._task = None
        self._listening = False
        self._final_text = ''
        self._init_recognizer()

    def _init_recognizer(self):
        try:
            from Cocoa import NSLocale
            import Speech
            locale = NSLocale.localeWithLocaleIdentifier_('zh-CN')
            self._recognizer = Speech.SFSpeechRecognizer.alloc().initWithLocale_(locale)
            if self._recognizer is None:
                self._recognizer = Speech.SFSpeechRecognizer.alloc().init()
            print('[语音] SFSpeechRecognizer 初始化成功')
        except Exception as e:
            print('[语音] 初始化识别器失败:', e)
            self._recognizer = None

    def is_available(self):
        return self._recognizer is not None

    def request_permissions(self):
        """请求麦克风 + 语音识别权限，返回是否都已授权"""
        import AVFoundation
        import Speech
        from Cocoa import NSObject

        mic_ok = [False]
        speech_ok = [False]

        # 麦克风权限
        def mic_handler(granted):
            mic_ok[0] = bool(granted)

        # macOS 14+ 用 AVAudioApplication；旧版用 AVCaptureDevice
        if hasattr(AVFoundation, 'AVAudioApplication'):
            AVFoundation.AVAudioApplication.requestRecordPermissionWithCompletionHandler_(mic_handler)
        else:
            AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                'audi', mic_handler
            )

        # 语音识别权限
        def speech_handler(status):
            speech_ok[0] = (int(status) == 1)  # SFSpeechRecognizerAuthorizationStatusAuthorized

        Speech.SFSpeechRecognizer.requestAuthorization_(speech_handler)

        # 等待权限结果（最多 5 秒）
        deadline = time.time() + 5
        while time.time() < deadline:
            if mic_ok[0] and speech_ok[0]:
                break
            time.sleep(0.1)

        return mic_ok[0] and speech_ok[0]

    def start(self):
        """开始实时识别，返回是否成功启动"""
        import AVFoundation
        import Speech

        if self._listening or self._recognizer is None:
            return False
        try:
            self._engine = AVFoundation.AVAudioEngine.alloc().init()
            input_node = self._engine.inputNode()

            self._request = Speech.SFSpeechAudioBufferRecognitionRequest.alloc().init()
            self._request.setShouldReportPartialResults_(True)
            self._final_text = ''
            self._listening = True

            fmt = input_node.outputFormatForBus_(0)

            def result_handler(result, error):
                if error is not None:
                    print('[语音] 识别错误:', error)
                if result is not None:
                    text = result.bestTranscription().formattedString()
                    if text:
                        self._final_text = text
                        # 推送部分结果到前端
                        try:
                            if self._window is not None:
                                safe = text.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')
                                self._window.evaluate_js(
                                    f"window.__onedayPartialResult && window.__onedayPartialResult('{safe}')"
                                )
                        except Exception as e:
                            print('[语音] 推送部分结果失败:', e)
                    if result.isFinal():
                        self._stop_engine()

            self._task = self._recognizer.recognitionTaskWithRequest_resultHandler_(
                self._request, result_handler
            )

            def tap_handler(buffer, when):
                if self._request is not None and self._listening:
                    try:
                        self._request.appendAudioPCMBuffer_(buffer)
                    except Exception:
                        pass

            input_node.installTapOnBus_bufferSize_format_block_(0, 1024, fmt, tap_handler)
            self._engine.prepare()
            success = self._engine.startAndReturnError_(None)
            if not success:
                print('[语音] AVAudioEngine 启动失败')
                self._stop_engine()
                return False
            print('[语音] 开始识别...')
            return True
        except Exception as e:
            print('[语音] 启动失败:', e)
            self._listening = False
            self._stop_engine()
            return False

    def stop(self):
        """停止识别，返回最终文本"""
        self._stop_engine()
        self._listening = False
        return self._final_text

    def _stop_engine(self):
        try:
            if self._engine is not None:
                try:
                    self._engine.inputNode().removeTapOnBus_(0)
                except Exception:
                    pass
                self._engine.stop()
                self._engine = None
            if self._request is not None:
                try:
                    self._request.endAudio()
                except Exception:
                    pass
                self._request = None
            if self._task is not None:
                try:
                    self._task.cancel()
                except Exception:
                    pass
                self._task = None
        except Exception as e:
            print('[语音] 停止引擎失败:', e)


# ===== 桥接给前端的 API =====
class Api:
    """pywebview js_api：前端通过 pywebview.api.xxx() 调用"""

    def __init__(self, window_holder):
        self._window_holder = window_holder  # 字典引用，窗口创建后填充
        self._speech = None

    def _get_window(self):
        return self._window_holder.get('window')

    # ---- 窗口控制（红绿灯按钮）----
    def minimize(self):
        w = self._get_window()
        if w:
            w.minimize()

    def toggle_fullscreen(self):
        w = self._get_window()
        if w:
            w.toggle_fullscreen()

    def resize(self, width, height):
        """调整窗口大小（右下角拖拽手柄调用）"""
        w = self._get_window()
        if not w:
            return {'ok': False}
        try:
            w.resize(int(width), int(height))
            return {'ok': True}
        except Exception as e:
            print('[窗口] resize 异常:', e)
            return {'ok': False, 'error': str(e)}

    def close(self):
        w = self._get_window()
        try:
            if w:
                w.destroy()
        except Exception as e:
            print('[窗口] destroy 异常:', e)
        # pywebview 在 macOS 上 destroy 后事件循环可能不退出，延迟强制退出兜底
        threading.Timer(0.8, lambda: os._exit(0)).start()

    # ---- 语音识别 ----
    def speech_available(self):
        return self._speech is not None and self._speech.is_available()

    def start_listening(self):
        """开始语音识别，返回 {'ok': True/False, 'reason': '...'}"""
        try:
            if self._speech is None:
                self._speech = SpeechBridge(self._get_window())
            if not self._speech.is_available():
                return {'ok': False, 'reason': '系统语音识别不可用'}
            if not self._speech.request_permissions():
                return {'ok': False, 'reason': '麦克风或语音识别权限未授予，请到 系统设置 > 隐私与安全性 中开启'}
            ok = self._speech.start()
            return {'ok': ok, 'reason': '' if ok else '启动语音识别失败'}
        except Exception as e:
            print('[语音] start_listening 异常:', e)
            return {'ok': False, 'reason': str(e)}

    def stop_listening(self):
        """停止语音识别，返回识别文本"""
        try:
            if self._speech is None:
                return {'ok': False, 'text': ''}
            text = self._speech.stop()
            return {'ok': True, 'text': text}
        except Exception as e:
            print('[语音] stop_listening 异常:', e)
            return {'ok': False, 'text': ''}


# ===== 后台服务器 =====
def start_backend():
    """后台线程：启动 OneDay HTTP 服务器"""
    import http.server
    server.PORT = DESKTOP_PORT
    try:
        server.start_scheduler()
    except Exception as e:
        print('[后端] 定时任务启动失败:', e)
    httpd = http.server.HTTPServer(('127.0.0.1', DESKTOP_PORT), server.Handler)
    print('=' * 50)
    print('OneDay / 一日 桌面版后端已启动')
    print(f'端口: {DESKTOP_PORT}')
    print(f'目录: {server.BASE_DIR}')
    print(f'访问: http://127.0.0.1:{DESKTOP_PORT}')
    print('=' * 50)
    try:
        httpd.serve_forever()
    except Exception as e:
        print('[后端] 服务器异常退出:', e)


def wait_for_server(timeout=15):
    """等待服务器就绪"""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{DESKTOP_PORT}/api/health', timeout=2)
            return True
        except Exception:
            time.sleep(0.3)
    return False


# ===== 主入口 =====
def main():
    import webview

    migrate_data_if_needed()

    # 启动后端
    t = threading.Thread(target=start_backend, daemon=True)
    t.start()

    if not wait_for_server():
        print('❌ 服务器启动超时，请检查端口占用')
        sys.exit(1)

    window_holder = {}
    api = Api(window_holder)

    window = webview.create_window(
        'OneDay 一日',
        f'http://127.0.0.1:{DESKTOP_PORT}/?desktop=1',
        js_api=api,
        width=1440,
        height=900,
        min_size=(1100, 700),
        frameless=True,
        easy_drag=False,  # 用前端 CSS -webkit-app-region: drag 做拖拽条，避免干扰页面交互
        background_color='#000000',
    )
    window_holder['window'] = window

    webview.start()

    # 兜底：正常退出路径（Cmd+Q / 全部窗口关闭）确保进程完全退出
    # pywebview 在 macOS 上 start() 返回后 Cocoa 资源可能仍挂住
    os._exit(0)


if __name__ == '__main__':
    main()
