#!/usr/bin/env python3
"""Đóng gói bộ thẻ Anki (.apkg) vào deck "Tiếng Anh công việc" với đúng hai kiểu thẻ đang dùng.

    python tao_bo_the.py the.json [--out tieng-anh-cong-viec-05.apkg]

the.json:
{
  "bo": "05",
  "so_cau_nghe_bat_dau": 20,
  "the": [
    {"kieu": "nghe",
     "cau": "I <b>worked on</b> the menu.",
     "focus": ["worked on: -ed đọc /t/, nối sang on", "không phải works on"],
     "nghia": "Tôi đã làm phần menu."},
    {"kieu": "doc",
     "tu": "look into", "ten": "look_into", "ipa": "/lʊk ˈɪntuː/",
     "nghia": "xem xét, tìm hiểu (một vấn đề)",
     "vi_du": "The team will <b>look into</b> the crash.",
     "nghia_vi_du": "Nhóm sẽ xem xét lỗi crash.",
     "doc_tu": "look into"}
  ]
}

- "cau", "vi_du": in đậm từ trọng tâm bằng <b>…</b>; đánh dấu đọc nhẹ bằng {can}, {for}…
  (chỉ ảnh hưởng audio, chữ trên thẻ không có ngoặc).
- "ten": phần tên file audio tacv_w_<ten>.mp3 — không trùng tên đã dùng (xem tien-do.md).
- "doc_tu": cách đọc từ nếu khác chữ viết (viết tắt: "E. O. D.").
- Câu nghe đặt tên tacv_sNN theo thứ tự, bắt đầu từ so_cau_nghe_bat_dau.

Script giữ đúng id deck/kiểu thẻ, tên trường, tên mẫu thẻ và đặt mod kiểu thẻ = 1791737271
để khi nhập, Anki dùng lại kiểu thẻ người học đang có (không tạo kiểu mới, không ghi đè mẫu thẻ).
"""
import argparse
import json
import re
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tts import Giong, bo_danh_dau, chu_thuan  # noqa: E402

DECK_ID = 2059400311
DECK_TEN = "Tiếng Anh công việc"
MOD_KIEU_THE = 1791737271

ID_DOC = 1749201163
TEN_DOC = "TA – Từ vựng (đọc)"
TRUONG_DOC = ["Word", "IPA", "Meaning", "Example", "ExampleMeaning", "WordAudio", "ExampleAudio"]
MAU_DOC = "Đọc → nghĩa"

ID_NGHE = 1749201164
TEN_NGHE = "TA – Nghe chép câu"
TRUONG_NGHE = ["Sentence", "Audio", "WordCount", "Focus", "Meaning"]
MAU_NGHE = "Nghe → chép câu"

TOC_DO = {"nghe": 0.78, "tu": 0.8, "vi_du": 0.85}

# Mẫu thẻ chỉ dùng khi bộ sưu tập chưa có kiểu thẻ này. Có rồi thì Anki giữ mẫu cũ (nhờ mod).
CSS = """.card{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:20px;text-align:center;color:#1d1d1f;background:#fff;line-height:1.5;padding:12px}
.nightMode .card{color:#ececec;background:#1d1f22}
.word{font-size:30px;font-weight:600}.ipa{color:#6b6b6b}.meaning{font-size:22px;margin:8px 0}
.example{margin-top:14px}.exmeaning,.focus{color:#6b6b6b;font-size:17px}.hint{color:#6b6b6b;font-size:16px}
.sentence{font-size:24px;margin:8px 0}"""
QFMT_DOC = '<div class="word">{{Word}}</div>{{WordAudio}}'
AFMT_DOC = ('{{FrontSide}}<hr id=answer><div class="ipa">{{IPA}}</div><div class="meaning">{{Meaning}}</div>'
            '<div class="example">{{Example}} {{ExampleAudio}}</div><div class="exmeaning">{{ExampleMeaning}}</div>')
QFMT_NGHE = '<div class="hint">Nghe và chép lại câu ({{WordCount}} từ)</div>{{Audio}}'
AFMT_NGHE = ('{{FrontSide}}<hr id=answer><div class="sentence">{{Sentence}}</div>'
             '<div class="focus">{{Focus}}</div><div class="meaning">{{Meaning}}</div>')


def dem_tu(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-]*", chu_thuan(text)))


def dat_mod(apkg: Path, mod: int, ids) -> None:
    """Sửa trường mod của các kiểu thẻ trong collection.anki2 của file .apkg."""
    with zipfile.ZipFile(apkg) as z:
        members = [(i, z.read(i.filename)) for i in z.infolist()]
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "collection.anki2"
        db.write_bytes(dict((i.filename, d) for i, d in members)["collection.anki2"])
        con = sqlite3.connect(db)
        models = json.loads(con.execute("select models from col").fetchone()[0])
        for mid, m in models.items():
            if int(mid) in ids:
                m["mod"] = mod
        con.execute("update col set models = ?", (json.dumps(models),))
        con.commit()
        con.close()
        moi = db.read_bytes()
    with zipfile.ZipFile(apkg, "w", zipfile.ZIP_DEFLATED) as z:
        for info, data in members:
            z.writestr(info.filename, moi if info.filename == "collection.anki2" else data)


def kiem_tra(apkg: Path) -> list:
    """Đọc lại file: trả về [(tên kiểu thẻ, id, mod, trường, mẫu thẻ, số thẻ)]."""
    with zipfile.ZipFile(apkg) as z, tempfile.TemporaryDirectory() as td:
        db = Path(td) / "c.anki2"
        db.write_bytes(z.read("collection.anki2"))
        con = sqlite3.connect(db)
        models = json.loads(con.execute("select models from col").fetchone()[0])
        so_the = dict(con.execute("select mid, count(*) from notes group by mid").fetchall())
        con.close()
    return [(m["name"], int(mid), m["mod"], [f["name"] for f in m["flds"]],
             [t["name"] for t in m["tmpls"]], so_the.get(int(mid), 0)) for mid, m in models.items()]


def main():
    import genanki

    ap = argparse.ArgumentParser(description="Tạo bộ thẻ Anki .apkg cho deck Tiếng Anh công việc.")
    ap.add_argument("spec", help="File JSON mô tả bộ thẻ")
    ap.add_argument("--out", help="File .apkg đầu ra (mặc định tieng-anh-cong-viec-<bo>.apkg)")
    ap.add_argument("--thu-muc-audio", default=None, help="Nơi để file mp3 (mặc định thư mục tạm)")
    a = ap.parse_args()

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    bo = str(spec["bo"]).zfill(2)
    out = Path(a.out or f"tieng-anh-cong-viec-{bo}.apkg")
    audio_dir = Path(a.thu_muc_audio or tempfile.mkdtemp())
    audio_dir.mkdir(parents=True, exist_ok=True)

    kieu_doc = genanki.Model(ID_DOC, TEN_DOC, fields=[{"name": f} for f in TRUONG_DOC],
                             templates=[{"name": MAU_DOC, "qfmt": QFMT_DOC, "afmt": AFMT_DOC}], css=CSS)
    kieu_nghe = genanki.Model(ID_NGHE, TEN_NGHE, fields=[{"name": f} for f in TRUONG_NGHE],
                              templates=[{"name": MAU_NGHE, "qfmt": QFMT_NGHE, "afmt": AFMT_NGHE}], css=CSS)
    deck = genanki.Deck(DECK_ID, DECK_TEN)
    giong = Giong()
    media, so = [], int(spec.get("so_cau_nghe_bat_dau", 1))
    dau_nghe = so
    ten_tu = []

    for t in spec["the"]:
        if t["kieu"] == "nghe":
            ten = f"tacv_s{so:02d}.mp3"
            giong.mp3(chu_thuan_giu_dau(t["cau"]), audio_dir / ten, speed=TOC_DO["nghe"])
            media.append(str(audio_dir / ten))
            focus = t.get("focus", [])
            focus = "<br>".join(focus) if isinstance(focus, list) else focus
            fields = [bo_danh_dau(t["cau"]), f"[sound:{ten}]", str(dem_tu(t["cau"])), focus, t.get("nghia", "")]
            deck.add_note(genanki.Note(model=kieu_nghe, fields=fields, tags=[f"bo-the-{bo}", "nghe"]))
            print(f"  nghe  {ten}  {chu_thuan(t['cau'])}")
            so += 1
        elif t["kieu"] == "doc":
            ten = t["ten"]
            f_tu, f_vd = f"tacv_w_{ten}.mp3", f"tacv_w_{ten}_ex.mp3"
            giong.mp3(t.get("doc_tu") or chu_thuan(t["tu"]), audio_dir / f_tu, speed=TOC_DO["tu"])
            giong.mp3(chu_thuan_giu_dau(t["vi_du"]), audio_dir / f_vd, speed=TOC_DO["vi_du"])
            media += [str(audio_dir / f_tu), str(audio_dir / f_vd)]
            fields = [bo_danh_dau(t["tu"]), t.get("ipa", ""), t.get("nghia", ""), bo_danh_dau(t["vi_du"]),
                      t.get("nghia_vi_du", ""), f"[sound:{f_tu}]", f"[sound:{f_vd}]"]
            deck.add_note(genanki.Note(model=kieu_doc, fields=fields, tags=[f"bo-the-{bo}", "doc"]))
            ten_tu.append(ten)
            print(f"  đọc   {f_tu}  {chu_thuan(t['tu'])}")
        else:
            sys.exit(f"Kiểu thẻ không hợp lệ: {t['kieu']} (chỉ 'nghe' hoặc 'doc')")

    genanki.Package(deck, media_files=media).write_to_file(str(out))
    dat_mod(out, MOD_KIEU_THE, {ID_DOC, ID_NGHE})

    print(f"\nĐã tạo {out} — {len(spec['the'])} thẻ, {len(media)} file audio.")
    for ten_kieu, mid, mod, truong, mau, n in kiem_tra(out):
        print(f"  kiểu thẻ '{ten_kieu}' id={mid} mod={mod} trường={truong} mẫu={mau} số thẻ={n}")
    if so > dau_nghe:
        print(f"Câu nghe dùng tacv_s{dau_nghe:02d}–tacv_s{so - 1:02d}. Lần sau bắt đầu từ {so}.")
    if ten_tu:
        print("Tên audio từ vựng vừa dùng: " + ", ".join(ten_tu))
    print("Ghi các số này vào tien-do.md, mục Anki.")


def chu_thuan_giu_dau(text: str) -> str:
    """Bỏ thẻ HTML nhưng giữ đánh dấu {…} để audio đọc nhẹ đúng chỗ."""
    return re.sub(r"<[^>]+>", "", text)


if __name__ == "__main__":
    main()
