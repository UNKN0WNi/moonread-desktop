@echo off
chcp 65001 >nul
REM 一键打包绿色版：生成 dist\MoonRead.exe（单文件，解压即用）
echo ============================================
echo  MoonRead 绿色版打包
echo ============================================

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 python，请先安装 Python 3.10+ 并加入 PATH。
  pause
  exit /b 1
)

echo [1/3] 安装依赖...
python -m pip install --quiet pywebview pyinstaller
if errorlevel 1 (
  echo [错误] 依赖安装失败。
  pause
  exit /b 1
)

echo [2/3] 打包 exe...
python -m PyInstaller --clean --noconfirm moonread.spec
if errorlevel 1 (
  echo [错误] 打包失败。
  pause
  exit /b 1
)

echo [3/3] 完成！
echo 产物：dist\MoonRead.exe （约 13 MB，单文件绿色版）
echo 直接双击即可运行，也可把 .epub 拖到 exe 图标上打开。
pause
