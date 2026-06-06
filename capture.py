"""
ScreenMind - 画面キャプチャモジュール
PIL.ImageGrabを使用してスクリーンショットを取得し、
Base64エンコードされたJPEG文字列として返す
"""

import base64
import io
import logging
import platform
from typing import Optional

from PIL import Image

import config

logger = logging.getLogger(__name__)


def capture_screen() -> Optional[str]:
    """
    画面全体をキャプチャしてBase64エンコードされたJPEG文字列を返す。

    Returns:
        Base64エンコードされたJPEG文字列。失敗時はNone。
    """
    try:
        # OS別のキャプチャ処理
        img = _grab_screen()
        if img is None:
            return None

        # RGBAの場合はRGBに変換（JPEG非対応のため）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 指定サイズにリサイズ（アスペクト比を維持しながらフィット）
        img = _resize_image(img, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT)

        # JPEG形式でメモリバッファに書き出し
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=config.CAPTURE_QUALITY, optimize=True)
        buffer.seek(0)

        # Base64エンコード
        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        logger.debug(
            "スクリーンキャプチャ完了: %dx%d, %d bytes (Base64)",
            img.width,
            img.height,
            len(encoded),
        )
        return encoded

    except Exception as e:
        logger.error("スクリーンキャプチャに失敗しました: %s", e, exc_info=True)
        return None


def _grab_screen() -> Optional[Image.Image]:
    """
    OS別の方法で画面をキャプチャする。

    Returns:
        PIL.Image オブジェクト。失敗時はNone。
    """
    system = platform.system()

    # Windows / macOS: PIL.ImageGrab を使用
    if system in ("Windows", "Darwin"):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab(all_screens=True)
            return img
        except Exception as e:
            logger.warning("ImageGrab失敗 (%s): %s", system, e)

    # Linux: scrot / gnome-screenshot / xwd などをフォールバックとして試みる
    if system == "Linux":
        img = _grab_screen_linux()
        if img:
            return img

    # 最終フォールバック: ImageGrabをそのまま試みる
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        return img
    except Exception as e:
        logger.error("全キャプチャ方法が失敗しました: %s", e)
        return None


def _grab_screen_linux() -> Optional[Image.Image]:
    """
    Linuxでのスクリーンキャプチャ（複数の方法を試みる）。
    """
    import subprocess
    import tempfile
    import os

    # scrot を試みる
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        result = subprocess.run(
            ["scrot", "-z", tmp_path],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and os.path.exists(tmp_path):
            img = Image.open(tmp_path)
            img = img.copy()  # ファイルを閉じるためにコピー
            os.unlink(tmp_path)
            return img
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception as e:
        logger.debug("scrot失敗: %s", e)

    # gnome-screenshot を試みる
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        result = subprocess.run(
            ["gnome-screenshot", "-f", tmp_path],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0 and os.path.exists(tmp_path):
            img = Image.open(tmp_path)
            img = img.copy()
            os.unlink(tmp_path)
            return img
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    except Exception as e:
        logger.debug("gnome-screenshot失敗: %s", e)

    # PIL.ImageGrab (Xlib経由) を試みる
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        return img
    except Exception as e:
        logger.debug("PIL.ImageGrab (Linux)失敗: %s", e)

    return None


def _resize_image(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    アスペクト比を維持しながら指定サイズ内に収まるようリサイズする。
    """
    orig_w, orig_h = img.size
    ratio = min(target_w / orig_w, target_h / orig_h)
    new_w = int(orig_w * ratio)
    new_h = int(orig_h * ratio)
    return img.resize((new_w, new_h), Image.LANCZOS)


def capture_screen_as_bytes() -> Optional[bytes]:
    """
    画面全体をキャプチャしてJPEGバイト列を返す（デバッグ・テスト用）。
    """
    try:
        img = _grab_screen()
        if img is None:
            return None
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img = _resize_image(img, config.CAPTURE_WIDTH, config.CAPTURE_HEIGHT)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=config.CAPTURE_QUALITY)
        return buffer.getvalue()
    except Exception as e:
        logger.error("キャプチャ（バイト）失敗: %s", e)
        return None


# ===== 単体テスト =====
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("スクリーンキャプチャのテストを開始します...")
    result = capture_screen()
    if result:
        print(f"成功: Base64文字列の長さ = {len(result)} 文字")
        # テスト用に保存
        img_bytes = base64.b64decode(result)
        with open("test_capture.jpg", "wb") as f:
            f.write(img_bytes)
        print("test_capture.jpg に保存しました")
    else:
        print("失敗: キャプチャできませんでした")
