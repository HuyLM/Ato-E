# Anki và audio

Đọc file này trước khi tạo bộ thẻ Anki hoặc audio cho bài Nghe. Cần môi trường chạy code (Python, ffmpeg, tải được gói từ PyPI và model từ GitHub).

## 1. Deck và kiểu thẻ đang dùng — giữ đúng tuyệt đối

Người học đã có deck và hai kiểu thẻ này trong Anki. Anki nhận kiểu thẻ qua id: nếu tên trường, thứ tự trường hoặc tên mẫu thẻ khác, Anki tạo thêm một kiểu thẻ mới (tên dạng "TA – Từ vựng (đọc)-xxxx") và thẻ rơi vào đó; nếu bản trong file mới hơn (mod lớn hơn), Anki có thể ghi đè mẫu thẻ người học đang dùng. `scripts/tao_bo_the.py` đã đặt sẵn mọi giá trị dưới đây.

| Thứ | Giá trị |
|---|---|
| Deck | "Tiếng Anh công việc", id 2059400311 |
| Kiểu thẻ đọc | "TA – Từ vựng (đọc)", id 1749201163; trường: Word, IPA, Meaning, Example, ExampleMeaning, WordAudio, ExampleAudio; mẫu thẻ "Đọc → nghĩa" |
| Kiểu thẻ nghe | "TA – Nghe chép câu", id 1749201164; trường: Sentence, Audio, WordCount, Focus, Meaning; mẫu thẻ "Nghe → chép câu" |
| mod của cả hai kiểu thẻ | 1791737271 (đặt sau khi đóng gói, trong collection.anki2 → bảng col → cột models) |

Mẫu thẻ gốc nằm trong tieng-anh-cong-viec-01.apkg. Script dùng mẫu thẻ tạm cùng tên trường, tên mẫu thẻ và mod, nên khi nhập Anki giữ mẫu thẻ cũ. Lần đầu dùng mẫu tạm là bộ 04 (18/10/2026): nếu người học báo sau khi nhập có kiểu thẻ mới tên "TA – …-…", ghi vào tien-do.md và kiểm tra lại tên, thứ tự trường.

## 2. Quy ước nội dung

- Sentence (thẻ nghe): in đậm từ trọng tâm bằng `<b>…</b>`.
- WordCount: chỉ ghi số (script tự đếm).
- Focus: mỗi ý một dòng, nối bằng `<br>` (script tự nối từ danh sách).
- Tag: `bo-the-NN` + `nghe` hoặc `doc`.
- Tên audio: câu nghe `tacv_sNN.mp3`, đánh số tiếp theo số đã dùng (ghi trong tien-do.md); từ vựng `tacv_w_<tên>.mp3` và `tacv_w_<tên>_ex.mp3`, `<tên>` không trùng danh sách tên đã dùng trong tien-do.md.
- File: `tieng-anh-cong-viec-NN.apkg`, NN = số bộ tiếp theo.
- Giọng Kokoro `af_heart`; tốc độ: câu nghe 0.78, từ 0.8, câu ví dụ 0.85.
- Mỗi bộ chỉ chứa thứ người học chọn (gợi ý 5–8 mục/buổi). Anki chỉ chứa từ người học chưa biết.

## 3. Dạng đọc nhẹ và viết tắt

Giọng máy đọc rõ từng từ ("can" thành /kæn/, có lúc "for" thành /fɔːr/), còn người thật đọc nhẹ /kən/, /fɚ/, /ənd/. Người học từng nhầm can/can't vì giọng máy đọc "can" quá rõ. Vì vậy đánh dấu từ cần đọc nhẹ bằng ngoặc nhọn trong lời đọc: `You {can} skip this ad.` Bảng dạng nhẹ có sẵn trong `scripts/tts.py` (can, for, and, to, at, of, from, was, are, them, his…); từ khác thì tự cho phiên âm: `{can|kən}`. Chữ trên thẻ và trên trang không có ngoặc.

Viết tắt đọc từng chữ cái (ASAP, EOD): Kokoro đọc "EOD" đứng một mình thành một từ (/aʊd/) nhưng đánh vần đúng khi có từ khác đứng trước. Với thẻ từ vựng, đặt `"doc_tu": "E. O. D."` để chắc chắn.

## 4. Tạo bộ thẻ

```bash
pip install --break-system-packages genanki kokoro-onnx soundfile   # cần thêm ffmpeg
python scripts/tao_bo_the.py the.json --out tieng-anh-cong-viec-05.apkg
```

`the.json`:

```json
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
     "nghia_vi_du": "Nhóm sẽ xem xét lỗi crash."}
  ]
}
```

Lần chạy đầu, `scripts/tts.py` tự tải model Kokoro (kokoro-v1.0.onnx khoảng 325 MB, voices-v1.0.bin khoảng 28 MB) từ GitHub releases của thewh1teagle/kokoro-onnx (bản model-files-v1.0) vào `$KOKORO_DIR` (mặc định `~/.cache/kokoro`). Script in ra các kiểu thẻ trong file (tên, id, mod, trường, mẫu thẻ) để kiểm tra, cùng số câu nghe và tên audio vừa dùng: ghi các số đó vào tien-do.md.

Không chạy được (không có code, không tải được model): không gửi thẻ thiếu audio cho thẻ nghe. Ghi các mục vào "Từ chờ đưa vào Anki" trong tien-do.md để buổi sau tạo.

## 5. Dặn người học nhập thẻ

1. Tải file .apkg, mở bằng Anki trên máy tính (nhấp đúp file, hoặc File → Import).
2. Thẻ vào deck "Tiếng Anh công việc"; giữ 5 thẻ mới mỗi ngày.
3. Bấm Sync để ôn trên AnkiWeb (iPhone).
4. Thấy kiểu thẻ mới tên "TA – …-…" sau khi nhập → báo gia sư.

## 6. Trang audio cho bài tập

Bài Nghe cần audio tự tạo (luyện tai A/B, phân loại âm, chép chính tả giọng máy, đọc to theo bài đọc) đặt chung trong một trang `audio-bai-tap-tiep-theo.html`, dựng lại mỗi khi hàng đợi bài thay đổi:

```bash
python scripts/tao_trang_audio.py spec.json --out audio-bai-tap-tiep-theo.html --cache .audio-cache
```

`spec.json` lấy từ khối "Spec audio" ở cuối `bai-tap-tiep-theo.md`: sửa khối đó trước, rồi dựng trang từ nó, để file bài tập luôn đủ thông tin dựng lại trang. Định dạng các kiểu phần (`chon`, `chep`, `nghe`) mô tả ở đầu `scripts/tao_trang_audio.py`. Trang chạy offline, không chứa đáp án; người học bấm "Tạo câu trả lời" rồi dán vào chat, kèm số lần nghe mỗi câu.

Trang không đặt "ngày" thì lấy ngày của máy chạy script (thường là giờ UTC): đặt `"ngay": "dd/mm/yyyy"` theo giờ Việt Nam trong spec.
