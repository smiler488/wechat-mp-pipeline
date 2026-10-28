#!/usr/bin/env python3
"""SVG → PNG 渲染器（公众号封面/信息图专用，跨平台 macOS/Windows）

用法: python3 svg2png.py <in.svg> <out.png> [宽=900] [高=383]

渲染器优先级：
1. Playwright 默认浏览器（pip install playwright && playwright install chromium）
2. 各平台缓存的 Chrome for Testing（macOS ~/Library/Caches/ms-playwright，
   Windows %LOCALAPPDATA%\\ms-playwright）
3. 系统 Chrome headless 命令行截图（macOS /Applications/...；
   Windows C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe）

背景：Chrome.app headless 在 macOS 本机自 2026-10-27 起不稳定
（GPU process FATAL / 沙盒拒绝其清理 code_sign_clone 临时文件），勿直接调用。
"""
import sys
import glob
import os
import subprocess

W, H = 900, 383


def playwright_candidates():
    """按平台返回 Chrome for Testing 可执行文件候选路径。"""
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Caches/ms-playwright")
        pats = [os.path.join(base, "chromium-*/chrome-mac*/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing")]
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright")
        pats = [os.path.join(base, "chromium-*/chrome-win*/chrome.exe"),
                os.path.join(base, "chromium_headless_shell-*/chrome-win*/headless_shell.exe")]
    else:  # linux
        base = os.path.expanduser("~/.cache/ms-playwright")
        pats = [os.path.join(base, "chromium-*/chrome-linux*/chrome"),
                os.path.join(base, "chromium_headless_shell-*/chrome-linux/headless_shell")]
    out = []
    for p in pats:
        out.extend(glob.glob(p))
    return sorted(set(out))


def system_chrome():
    if sys.platform == "darwin":
        p = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform.startswith("win"):
        p = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    else:
        p = "/usr/bin/google-chrome"
    return p if os.path.exists(p) else None


def render_playwright(svg, out, w, h):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        # 先试 Playwright 默认浏览器，再退到缓存的 Chrome for Testing
        launchers = [lambda: pw.chromium.launch(args=["--headless=new", "--disable-gpu"])]
        for exe in playwright_candidates():
            launchers.append(lambda e=exe: pw.chromium.launch(executable_path=e, args=["--headless=new", "--disable-gpu"]))
        last_err = None
        for fn in launchers:
            try:
                b = fn()
                pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                pg.goto("file://" + svg)
                pg.wait_for_timeout(600)  # 等字体与渲染稳定
                pg.screenshot(path=out)
                b.close()
                return True
            except Exception as e:
                last_err = e
        print(f"playwright 路径全部失败: {last_err}", file=sys.stderr)
        return False


def render_system_chrome(svg, out, w, h):
    exe = system_chrome()
    if not exe:
        return False
    cmd = [exe, "--headless", "--disable-gpu", f"--screenshot={out}",
           f"--window-size={w},{h}", "--hide-scrollbars", "file://" + svg]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    return r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 5000


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    svg, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    w = int(sys.argv[3]) if len(sys.argv) > 3 else W
    h = int(sys.argv[4]) if len(sys.argv) > 4 else H
    if render_playwright(svg, out, w, h) or render_system_chrome(svg, out, w, h):
        print(f"written: {out} ({w}x{h})")
    else:
        sys.exit("所有渲染路径均失败。Windows 先跑: playwright install chromium；"
                 "macOS 检查 ~/Library/Caches/ms-playwright 是否存在。")


if __name__ == "__main__":
    main()
