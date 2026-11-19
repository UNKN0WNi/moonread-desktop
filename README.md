# MoonRead Desktop

[![CI](https://github.com/UNKN0WNi/moonread-desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/UNKN0WNi/moonread-desktop/actions/workflows/ci.yml)

一个轻量、绿色、免安装的 Windows EPUB 桌面阅读器。单文件 exe，双击即用，不写注册表。

它以 [MoonRead](https://github.com/UNKN0WNi/moonread) 阅读内核的 EPUB 解析规则为核心，界面用系统自带的 WebView2 渲染（不打包浏览器引擎），因此安装包只有约 13 MB。

## Features

- **绿色单文件**：一个 `MoonRead.exe`（约 13 MB），无需安装，不写注册表，可放 U 盘随身携带
- **拖拽打开**：把 `.epub` 拖进窗口，或拖到 exe 图标上，直接阅读
- **完整目录**：还原 NCX 多级目录，点击跳转
- **阅读体验**：上一章 / 下一章、键盘 `←` `→` / 空格翻页、字号调节、夜间模式
- **记住进度**：自动保存每本书的阅读位置与字号 / 主题偏好
- **本地解析**：解析全在本机完成，不联网、不上传任何内容

## Download

到 [Releases](https://github.com/UNKN0WNi/moonread-desktop/releases) 下载 `MoonRead.exe`，解压后双击运行即可。

> 需要 Windows 10 / 11 且已安装 **WebView2 Runtime**（Windows 11 与较新的 Windows 10 默认自带；若缺失，[点此安装](https://developer.microsoft.com/microsoft-edge/webview2/)）。

## Usage

```
双击 MoonRead.exe                 打开空白阅读器，再点「打开 EPUB」
拖 .epub 到窗口                   直接打开
MoonRead.exe book.epub            命令行 / 文件关联打开指定书
```

| 操作 | 方式 |
|---|---|
| 翻页 | 底部按钮，或键盘 `←` `→` / 空格 |
| 目录跳转 | 左侧目录点击；顶部「目录」按钮可折叠 |
| 字号 | 顶部 `A−` / `A＋` |
| 夜间模式 | 顶部「夜间」 |

偏好与进度保存在 exe 同目录的 `.moonread-data/`（绿色便携）；若该目录不可写，则退回 `%LOCALAPPDATA%\MoonRead`。

## Build from source

需要 Python 3.10+（Windows）：

```bat
pip install pywebview pyinstaller
python -m PyInstaller --clean --noconfirm moonread.spec
REM 产物：dist\MoonRead.exe
```

或直接双击 `build.bat` 一键打包。

源码运行（不打包）：

```bat
pip install -r requirements.txt
python src/app.py [book.epub]
```

## How it works

```
EPUB（ZIP）
  └─ epub.py        读 OPF 拿书目与 spine 顺序；读 NCX 还原目录；提取 XHTML 正文
       └─ app.py     pywebview 桌面窗口 + WebView2 渲染，API 桥接文件对话框 / 进度
            └─ web/  阅读器界面（目录、翻页、字号、夜间、拖拽）
```

- 解析逻辑与 [moonread](https://github.com/UNKN0WNi/moonread) 的 `tools/render_html.py` 共用同一套规则，只依赖 Python 标准库。
- GUI 用 `pywebview` + 系统 WebView2，不捆绑 Chromium，这是体积小的主要原因。
- 界面是本地 HTML/CSS/JS，随 exe 一起打包。

## Status

这是阅读器**壳**：EPUB 解析为纯文本 + 目录，不含 CSS 样式渲染或图片排版。加密 / DRM 电子书不支持。内容与进度永远留在本地。

## License

Apache-2.0。遵循 [MoonRead](https://github.com/UNKN0WNi/moonread) 的许可。
