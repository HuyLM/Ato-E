#!/usr/bin/env python3
"""Đọc câu tiếng Anh thành file mp3 bằng Kokoro (giọng af_heart), có dạng đọc nhẹ.

Người thật đọc nhẹ các từ nhỏ (can → /kən/, for → /fɚ/, and → /ənd/), còn giọng
máy đọc rõ từng từ. Đánh dấu từ cần đọc nhẹ bằng ngoặc nhọn:

    "You {can} skip this ad."      can đọc /kən/ (lấy từ bảng DANG_NHE)
    "Wait {for} me."               for đọc /fɚ/
    "I {can|kæn} do it."           tự cho phiên âm sau dấu |

Thẻ HTML như <b>…</b> bị bỏ qua khi đọc.

Dùng trong code:
    from tts import Giong
    g = Giong()
    g.mp3("You {can} skip this ad.", "a.mp3", speed=0.85)

Dùng từ dòng lệnh:
    python tts.py "You {can} skip this ad." a.mp3 --speed 0.85

Cần: pip install kokoro-onnx soundfile, và ffmpeg. Model (~350 MB) tự tải từ
GitHub releases của thewh1teagle/kokoro-onnx vào $KOKORO_DIR (mặc định
~/.cache/kokoro) ở lần chạy đầu.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
MODEL_FILES = ("kokoro-v1.0.onnx", "voices-v1.0.bin")
GIONG_MAC_DINH = "af_heart"

# Dạng đọc nhẹ (weak form) kiểu Mỹ, viết bằng ký hiệu Kokoro hiểu được.
DANG_NHE = {
    "a": "ə", "an": "ən", "and": "ənd", "are": "ɚ", "as": "əz", "at": "ət",
    "can": "kən", "could": "kəd", "do": "də", "does": "dəz", "for": "fɚ",
    "from": "fɹəm", "has": "həz", "have": "həv", "his": "ɪz", "her": "ɚ",
    "of": "əv", "or": "ɚ", "some": "səm", "than": "ðən", "that": "ðət",
    "the": "ðə", "them": "ðəm", "to": "tə", "was": "wəz", "were": "wɚ",
    "you": "jə", "your": "jɚ",
}

DANH_DAU = re.compile(r"\{([^{}|]+)(?:\|([^{}]+))?\}")
THE_HTML = re.compile(r"<[^>]+>")


def bo_html(text: str) -> str:
    """Bỏ thẻ HTML (<b>…</b>)."""
    return THE_HTML.sub("", text)


def bo_danh_dau(text: str) -> str:
    """Chữ để hiển thị: bỏ ngoặc nhọn đánh dấu đọc nhẹ, giữ nguyên thẻ HTML."""
    return DANH_DAU.sub(lambda m: m.group(1), text)


def chu_thuan(text: str) -> str:
    """Chữ thuần: bỏ cả đánh dấu đọc nhẹ lẫn thẻ HTML."""
    return bo_html(bo_danh_dau(text))


def thu_muc_model() -> Path:
    d = Path(os.environ.get("KOKORO_DIR", Path.home() / ".cache" / "kokoro"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def tai_model(d: Path):
    """Tải model nếu chưa có. Trả về (đường dẫn .onnx, đường dẫn voices)."""
    for name in MODEL_FILES:
        p = d / name
        if p.exists() and p.stat().st_size > 1_000_000:
            continue
        tmp = p.with_name(p.name + ".part")
        print(f"Đang tải {name} (lần đầu, vài phút)…", file=sys.stderr)
        try:
            urllib.request.urlretrieve(MODEL_URL + name, tmp)
        except Exception as loi:  # một số môi trường chỉ đi được qua curl
            print(f"urllib lỗi ({loi}); thử curl…", file=sys.stderr)
            subprocess.run(["curl", "-sSfL", "-o", str(tmp), MODEL_URL + name], check=True)
        tmp.rename(p)
    return d / MODEL_FILES[0], d / MODEL_FILES[1]


class Giong:
    def __init__(self, voice: str = GIONG_MAC_DINH, lang: str = "en-us"):
        from kokoro_onnx import Kokoro

        onnx, voices = tai_model(thu_muc_model())
        self.k = Kokoro(str(onnx), str(voices))
        self.voice = voice
        self.lang = lang

    def phien_am(self, text: str) -> str:
        """Phiên âm cả câu; phần đánh dấu {…} thay bằng dạng đọc nhẹ."""
        text = bo_html(text)
        phan, vi_tri = [], 0
        for m in DANH_DAU.finditer(text):
            truoc = text[vi_tri:m.start()]
            if truoc.strip():
                phan.append(self.k.tokenizer.phonemize(truoc, self.lang))
            tu, pa = m.group(1).strip(), m.group(2)
            if pa is None:
                pa = DANG_NHE.get(tu.lower())
                if pa is None:
                    raise ValueError(
                        f"Chưa có dạng đọc nhẹ cho '{tu}'. Viết {{{tu}|phiên âm}}, ví dụ {{can|kən}}."
                    )
            phan.append(pa.strip())
            vi_tri = m.end()
        sau = text[vi_tri:]
        if sau.strip():
            phan.append(self.k.tokenizer.phonemize(sau, self.lang))
        return " ".join(p for p in phan if p)

    def tao(self, text: str, speed: float = 0.85):
        """Trả về (samples, sample_rate)."""
        if DANH_DAU.search(text):
            return self.k.create(
                self.phien_am(text), voice=self.voice, speed=speed, lang=self.lang, is_phonemes=True
            )
        return self.k.create(bo_html(text), voice=self.voice, speed=speed, lang=self.lang)

    def mp3(self, text: str, out, speed: float = 0.85, kbps: int = 64):
        """Ghi một file mp3 (mono, 64 kbps) và trả về đường dẫn."""
        import soundfile as sf

        samples, sr = self.tao(text, speed)
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "a.wav"
            sf.write(wav, samples, sr)
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                 "-codec:a", "libmp3lame", "-b:a", f"{kbps}k", str(out)],
                check=True,
            )
        return out


def main():
    ap = argparse.ArgumentParser(description="Đọc một câu tiếng Anh thành mp3.")
    ap.add_argument("cau", help='Câu cần đọc, ví dụ "You {can} skip this ad."')
    ap.add_argument("out", help="File mp3 đầu ra")
    ap.add_argument("--speed", type=float, default=0.85)
    ap.add_argument("--phien-am", action="store_true", help="Chỉ in phiên âm, không tạo file")
    a = ap.parse_args()
    g = Giong()
    if a.phien_am:
        print(g.phien_am(a.cau) if DANH_DAU.search(a.cau) else g.k.tokenizer.phonemize(bo_html(a.cau)))
        return
    print(g.mp3(a.cau, a.out, speed=a.speed))


if __name__ == "__main__":
    main()
