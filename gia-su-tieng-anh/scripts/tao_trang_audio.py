#!/usr/bin/env python3
"""Dựng trang HTML phát audio cho bài tập (một file, chạy offline, không có đáp án).

    python tao_trang_audio.py spec.json --out audio-bai-tap-tiep-theo.html

Trang chỉ phát audio và thu câu trả lời; đáp án nằm trong bai-tap-tiep-theo.md
(chỉ gia sư xem). Người học bấm "Tạo câu trả lời" rồi dán vào chat.

spec.json:
{
  "tieu_de": "Audio bài tập tiếp theo",
  "mo_ta": "Một câu giới thiệu ngắn.",
  "phan": [
    {"id": "b4-1a", "nhom": "Buổi 4 — Nghe", "tieu_de": "Phần 1A · …",
     "huong_dan": "…", "kieu": "chon", "toc_do": 0.85,
     "muc": [{"doc": "fixed", "lua_chon": ["/t/", "/d/", "/ɪd/"]}]},
    {"id": "b4-1b", "kieu": "chon", "so_sanh": true,
     "muc": [{"lua_chon": ["I worked on the menu.", "I work on the menu."], "phat": 0}]},
    {"id": "chep", "kieu": "chep", "muc": [{"doc": "You {can} skip this ad."}]},
    {"id": "b5", "kieu": "nghe", "muc": [{"nhan": "Cả bài", "doc": "…", "toc_do": 0.9}]}
  ]
}

Kiểu phần:
  chon  nghe rồi chọn một đáp án. Lời đọc = "doc", hoặc lua_chon[phat].
        so_sanh=true thêm mục (gập sẵn) để nghe so sánh từng lựa chọn sau khi chấm.
  chep  nghe rồi gõ lại câu.
  nghe  chỉ phát (ví dụ cả bài đọc để đọc to theo), có thanh tua.
Lời đọc dùng được đánh dấu đọc nhẹ {can}, {for}… (xem tts.py).
"""
import argparse
import base64
import hashlib
import html
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts import Giong, chu_thuan  # noqa: E402

TOC_DO_MAC_DINH = 0.85


def khoa(text: str, speed: float) -> str:
    return "a" + hashlib.sha1(f"{speed}|{text}".encode()).hexdigest()[:10]


def dung_trang(spec: dict, giong: Giong, cache: Path = None) -> str:
    clips = {}  # khoa -> base64 mp3
    tmp = Path(cache) if cache else Path(tempfile.mkdtemp())
    tmp.mkdir(parents=True, exist_ok=True)

    def audio(text: str, speed: float) -> str:
        k = khoa(text, speed)
        if k not in clips:
            p = tmp / f"{k}.mp3"
            if not p.exists():
                giong.mp3(text, p, speed=speed)
                print(f"  ✓ {chu_thuan(text)[:60]}", file=sys.stderr)
            clips[k] = base64.b64encode(p.read_bytes()).decode()
        return k

    e = html.escape
    khoi = []
    nhom_truoc = None
    for si, phan in enumerate(spec["phan"]):
        pid = phan.get("id") or f"p{si + 1}"
        kieu = phan.get("kieu", "chon")
        speed = float(phan.get("toc_do", spec.get("toc_do_mac_dinh", TOC_DO_MAC_DINH)))
        nhom = phan.get("nhom")
        if nhom and nhom != nhom_truoc:
            khoi.append(f'<h2 class="nhom">{e(nhom)}</h2>')
            nhom_truoc = nhom
        tieu_de = phan.get("tieu_de", "")
        out = [f'<section class="phan" data-id="{e(pid)}" data-kieu="{kieu}" data-ten="{e(tieu_de)}">',
               f"<h3>{e(tieu_de)}</h3>"]
        if phan.get("huong_dan"):
            out.append(f'<p class="hd">{e(phan["huong_dan"])}</p>')
        if kieu == "nghe":
            for m in phan["muc"]:
                k = audio(m["doc"], float(m.get("toc_do", speed)))
                nhan = e(m.get("nhan", ""))
                out.append(f'<div class="nghe"><span class="nhan">{nhan}</span>'
                           f'<audio controls preload="none" data-clip="{k}"></audio></div>')
        else:
            muc_lua_chon = [m.get("lua_chon", []) for m in phan["muc"]]
            ngan = kieu == "chon" and all(len(chu_thuan(x)) <= 6 for ds in muc_lua_chon for x in ds)
            out.append('<ol class="muc">')
            for mi, m in enumerate(phan["muc"]):
                so = mi + 1
                if kieu == "chon":
                    lua_chon = m["lua_chon"]
                    loi = m.get("doc") if "doc" in m else lua_chon[int(m["phat"])]
                else:
                    loi = m["doc"]
                k = audio(loi, float(m.get("toc_do", speed)))
                row = [f'<li data-so="{so}">',
                       f'<button class="play" type="button" data-clip="{k}" aria-label="Nghe câu {so}">'
                       f'<span class="ico" aria-hidden="true">▶</span><span>Nghe</span></button>',
                       f'<span class="so">{so}</span>']
                if kieu == "chon":
                    row.append('<div class="chon" role="radiogroup">')
                    for oi, opt in enumerate(m["lua_chon"]):
                        chu = chu_thuan(opt)
                        nhan = chu if ngan else f"{chr(65 + oi)}. {chu}"
                        gia_tri = chu if ngan else chr(65 + oi)
                        row.append(f'<label><input type="radio" name="{e(pid)}-{so}" value="{e(gia_tri)}">'
                                   f'<span>{e(nhan)}</span></label>')
                    row.append("</div>")
                else:
                    row.append(f'<input class="chep" type="text" autocomplete="off" autocapitalize="off" '
                               f'spellcheck="false" placeholder="Gõ câu bạn nghe được">')
                row.append('<span class="dem" aria-live="polite">0 lần</span></li>')
                out.append("".join(row))
            out.append("</ol>")
            if kieu == "chon" and phan.get("so_sanh"):
                out.append('<details class="sosanh"><summary>Nghe so sánh từng lựa chọn '
                           '(mở sau khi gia sư chấm)</summary><ol>')
                for mi, m in enumerate(phan["muc"]):
                    nut = []
                    for oi, opt in enumerate(m["lua_chon"]):
                        k = audio(opt, float(m.get("toc_do", speed)))
                        nut.append(f'<button class="play nho" type="button" data-clip="{k}">'
                                   f'<span class="ico" aria-hidden="true">▶</span>'
                                   f'<span>{chr(65 + oi)}. {e(chu_thuan(opt))}</span></button>')
                    out.append(f'<li>{"".join(nut)}</li>')
                out.append("</ol></details>")
        out.append("</section>")
        khoi.append("\n".join(out))

    data_js = json.dumps(clips)
    tieu_de = spec.get("tieu_de", "Audio bài tập")
    mo_ta = spec.get("mo_ta", "")
    ngay = spec.get("ngay", date.today().strftime("%d/%m/%Y"))
    return TRANG.replace("__TIEU_DE__", e(tieu_de)) \
                .replace("__MO_TA__", e(mo_ta)) \
                .replace("__NGAY__", e(ngay)) \
                .replace("__NOI_DUNG__", "\n".join(khoi)) \
                .replace("__CLIPS__", data_js)


TRANG = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TIEU_DE__</title>
<style>
:root{--bg:#f6f5f1;--surface:#fff;--text:#1d1d1f;--muted:#64625d;--line:#e2dfd8;--accent:#1f6f8b;--accent-ink:#fff;--chip:#eaf2f5;--chip-on:#1f6f8b;--chip-on-ink:#fff;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#141517;--surface:#1d1f22;--text:#ececec;--muted:#a3a3a3;--line:#34373b;--accent:#6cb4d4;--accent-ink:#0b1a22;--chip:#22313a;--chip-on:#6cb4d4;--chip-on-ink:#0b1a22;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
.wrap{max-width:760px;margin:0 auto;padding:20px 16px 48px}
header h1{font-size:1.45rem;line-height:1.25;margin:0 0 6px}
header p{margin:0 0 12px;color:var(--muted)}
.tocdo{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:8px 0 4px;color:var(--muted);font-size:.92rem}
.tocdo button{border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:999px;padding:4px 12px;font:inherit;cursor:pointer}
.tocdo button[aria-pressed=true]{background:var(--chip-on);color:var(--chip-on-ink);border-color:var(--chip-on)}
.luuy{background:var(--chip);border-radius:10px;padding:10px 12px;font-size:.92rem;margin:14px 0 4px}
h2.nhom{font-size:1.15rem;margin:30px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--line)}
.phan{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}
.phan h3{font-size:1.02rem;margin:0 0 4px}
.hd{margin:0 0 10px;color:var(--muted);font-size:.94rem}
ol.muc{list-style:none;margin:0;padding:0}
ol.muc li{display:grid;grid-template-columns:auto auto 1fr auto;gap:8px 12px;align-items:center;padding:10px 0;border-top:1px solid var(--line)}
ol.muc li:first-child{border-top:0}
.so{font-weight:600;color:var(--muted);min-width:1.4em;text-align:right}
button.play{display:inline-flex;align-items:center;gap:6px;border:0;border-radius:10px;background:var(--accent);color:var(--accent-ink);padding:8px 12px;font:inherit;font-weight:600;cursor:pointer;min-height:40px}
button.play.dang{outline:3px solid color-mix(in srgb,var(--accent) 35%,transparent)}
button.play.nho{background:var(--chip);color:var(--text);font-weight:500;min-height:36px;padding:6px 10px;margin:4px 8px 4px 0}
.chon{display:flex;flex-wrap:wrap;gap:6px}
.chon label{cursor:pointer}
.chon input{position:absolute;opacity:0;pointer-events:none}
.chon span{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:6px 12px;background:var(--bg)}
.chon input:checked+span{background:var(--chip-on);color:var(--chip-on-ink);border-color:var(--chip-on)}
.chon input:focus-visible+span{outline:2px solid var(--accent);outline-offset:2px}
input.chep{width:100%;font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--text)}
.dem{font-size:.85rem;color:var(--muted);white-space:nowrap}
.nghe{display:flex;flex-direction:column;gap:6px}
.nghe audio{width:100%}
.nhan{font-weight:600}
details.sosanh{margin-top:12px;border-top:1px dashed var(--line);padding-top:10px}
details.sosanh summary{cursor:pointer;color:var(--muted);font-size:.94rem}
details.sosanh ol{padding-left:1.4em;margin:8px 0 0}
.gui{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px;margin:24px 0}
.gui h2{font-size:1.05rem;margin:0 0 6px}
.gui textarea{width:100%;min-height:140px;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;padding:10px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--text);margin-top:10px}
.hang{display:flex;gap:8px;flex-wrap:wrap}
.hang button{border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:10px;padding:8px 14px;font:inherit;cursor:pointer}
.hang button.chinh{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);font-weight:600}
footer{color:var(--muted);font-size:.85rem;margin-top:28px}
@media (max-width:560px){ol.muc li .play{grid-row:1;grid-column:1}ol.muc li .so{grid-row:1;grid-column:2;text-align:left}ol.muc li .dem{grid-row:1;grid-column:4}ol.muc li .chon,ol.muc li input.chep{grid-row:2;grid-column:1/-1}}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>__TIEU_DE__</h1>
<p>__MO_TA__</p>
<div class="tocdo" role="group" aria-label="Tốc độ phát">Tốc độ phát:
<button type="button" data-rate="0.8" aria-pressed="false">Chậm 0.8×</button>
<button type="button" data-rate="1" aria-pressed="true">Bình thường 1×</button>
</div>
<div class="luuy">Trang này chỉ phát audio, không có đáp án. Làm phần nào gia sư giao trong chat; xong bấm <b>Tạo câu trả lời</b> ở cuối trang rồi dán vào chat. Mỗi câu nên nghe tối đa 3 lần — trang tự đếm.</div>
</header>
<main>
__NOI_DUNG__
<section class="gui">
<h2>Gửi kết quả cho gia sư</h2>
<div class="hang">
<button type="button" class="chinh" id="tao">Tạo câu trả lời</button>
<button type="button" id="chep">Chép</button>
</div>
<textarea id="kq" readonly placeholder="Câu trả lời sẽ hiện ở đây."></textarea>
</section>
</main>
<footer>Tạo ngày __NGAY__ bằng skill gia-su-tieng-anh · giọng đọc máy (Kokoro).</footer>
</div>
<script>
const CLIPS = __CLIPS__;
let rate = 1;
const player = new Audio();
let nutDang = null;
function src(k){ return "data:audio/mpeg;base64," + CLIPS[k]; }
function dungNut(){ if(nutDang){ nutDang.classList.remove("dang"); nutDang.querySelector(".ico").textContent = "▶"; nutDang = null; } }
player.addEventListener("ended", dungNut);
player.addEventListener("pause", dungNut);
document.querySelectorAll("audio[data-clip]").forEach(a => {
  a.src = src(a.dataset.clip);
  a.addEventListener("play", () => { player.pause(); a.playbackRate = rate; });
});
document.addEventListener("click", ev => {
  const nut = ev.target.closest("button.play");
  if(!nut) return;
  if(nutDang === nut && !player.paused){ player.pause(); return; }
  player.pause();
  document.querySelectorAll("audio[data-clip]").forEach(a => a.pause());
  player.src = src(nut.dataset.clip);
  player.playbackRate = rate;
  player.play().then(() => {
    nutDang = nut; nut.classList.add("dang"); nut.querySelector(".ico").textContent = "❚❚";
    const li = nut.closest("ol.muc > li");
    if(li){ const d = li.querySelector(".dem"); const n = (parseInt(li.dataset.nghe || "0", 10) + 1); li.dataset.nghe = n; d.textContent = n + " lần"; }
  }).catch(() => {});
});
document.querySelectorAll(".tocdo button").forEach(b => b.addEventListener("click", () => {
  rate = parseFloat(b.dataset.rate);
  document.querySelectorAll(".tocdo button").forEach(x => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
  player.playbackRate = rate;
  document.querySelectorAll("audio[data-clip]").forEach(a => a.playbackRate = rate);
}));
document.getElementById("tao").addEventListener("click", () => {
  const dong = [];
  document.querySelectorAll("section.phan").forEach(sec => {
    const kieu = sec.dataset.kieu;
    if(kieu === "nghe") return;
    const muc = [];
    let coLam = false;
    sec.querySelectorAll("ol.muc > li").forEach(li => {
      const n = li.dataset.nghe || "0";
      let tl = "—";
      if(kieu === "chon"){ const c = li.querySelector("input:checked"); if(c) tl = c.value; }
      else { const v = li.querySelector("input.chep").value.trim(); if(v) tl = v; }
      if(tl !== "—" || n !== "0") coLam = true;
      muc.push(li.dataset.so + ": " + tl + " (nghe " + n + " lần)");
    });
    if(!coLam) return;
    const nhom = (() => { let p = sec.previousElementSibling; while(p && !p.matches("h2.nhom")) p = p.previousElementSibling; return p ? p.textContent + " · " : ""; })();
    dong.push(nhom + sec.dataset.ten + "\n" + muc.join(kieu === "chep" ? "\n" : " · "));
  });
  document.getElementById("kq").value = dong.length ? dong.join("\n\n") : "Chưa làm câu nào.";
});
document.getElementById("chep").addEventListener("click", async () => {
  const t = document.getElementById("kq");
  if(!t.value) document.getElementById("tao").click();
  try { await navigator.clipboard.writeText(t.value); }
  catch(e){ t.select(); try { document.execCommand("copy"); } catch(_){} }
});
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="Dựng trang audio bài tập (HTML một file).")
    ap.add_argument("spec", help="File JSON mô tả các phần")
    ap.add_argument("--out", default="audio-bai-tap-tiep-theo.html")
    ap.add_argument("--cache", default=None, help="Thư mục giữ mp3 đã tạo để lần sau dựng lại nhanh")
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    trang = dung_trang(spec, Giong(), Path(a.cache) if a.cache else None)
    Path(a.out).write_text(trang, encoding="utf-8")
    kb = Path(a.out).stat().st_size // 1024
    print(f"Đã tạo {a.out} ({kb} KB)")


if __name__ == "__main__":
    main()
