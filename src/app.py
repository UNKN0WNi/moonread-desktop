#!/usr/bin/env python3
"""MoonRead 桌面阅读器 —— 轻量、绿色、免安装的 Windows EPUB 阅读器。

用 pywebview + 系统自带 WebView2 显示界面（不打包浏览器引擎），
EPUB 解析复用 moonread 项目的规则（src/epub.py，纯标准库）。

运行：
    python src/app.py [book.epub]
打包后：
    MoonRead.exe [book.epub]
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

import webview

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epub import parse_epub  # noqa: E402

APP_NAME = "MoonRead"


def resource_path(rel: str) -> str:
    """定位打包内/开发时的静态资源。"""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


def data_dir() -> Path:
    """绿色便携：优先写在 exe 同目录的 .moonread-data，无权限则退回用户目录。"""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = Path(__file__).resolve().parent.parent
    candidate = exe_dir / ".moonread-data"
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        probe = candidate / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return candidate
    except OSError:
        fallback = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


DATA = data_dir()
PREFS_FILE = DATA / "prefs.json"
PROGRESS_FILE = DATA / "progress.json"
STARTUP_PATH = ""


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save_json(path: Path, obj) -> None:
    try:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def key_for(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]


class Api:
    """暴露给前端 JavaScript 的接口。"""

    def open_file(self):
        files = webview.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("EPUB 电子书 (*.epub)", "所有文件 (*.*)"),
        )
        return files[0] if files else None

    def load_epub(self, path: str) -> dict:
        try:
            data = parse_epub(path)
        except Exception as exc:
            return {"error": str(exc)}
        data["key"] = key_for(str(path))
        data["path"] = str(path)
        progress = _load_json(PROGRESS_FILE, {})
        data["saved_index"] = int(progress.get(data["key"], 0))
        return data

    def load_epub_bytes(self, b64: str, name: str) -> dict:
        """拖拽打开：接收 base64 字节，写临时文件后解析。"""
        try:
            raw = base64.b64decode(b64)
        except Exception as exc:  # noqa: B902
            return {"error": f"字节解码失败：{exc}"}
        tmp = Path(tempfile.gettempdir()) / f"moonread-drop-{os.getpid()}.epub"
        try:
            tmp.write_bytes(raw)
            data = parse_epub(tmp)
            data["key"] = hashlib.sha1(raw).hexdigest()[:16]
            data["path"] = name
            progress = _load_json(PROGRESS_FILE, {})
            data["saved_index"] = int(progress.get(data["key"], 0))
            return data
        except Exception as exc:
            return {"error": str(exc)}
        finally:
            try:
                tmp.unlink()
            except OSError:
                pass

    def save_progress(self, key: str, index: int) -> None:
        progress = _load_json(PROGRESS_FILE, {})
        if progress.get(key) != index:
            progress[key] = index
            _save_json(PROGRESS_FILE, progress)

    def get_prefs(self) -> dict:
        return _load_json(PREFS_FILE, {"night": False, "font_size": 18})

    def set_prefs(self, prefs: dict) -> None:
        _save_json(PREFS_FILE, prefs)

    def get_startup_path(self) -> str:
        return STARTUP_PATH


def main() -> int:
    global STARTUP_PATH
    if len(sys.argv) > 1:
        candidate = sys.argv[1]
        if os.path.isfile(candidate) and candidate.lower().endswith(".epub"):
            STARTUP_PATH = os.path.abspath(candidate)

    window = webview.create_window(
        APP_NAME,
        resource_path(os.path.join("web", "index.html")),
        js_api=Api(),
        width=1120,
        height=780,
        min_size=(820, 560),
        background_color="#f4f1ea",
        text_select=True,
    )
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
