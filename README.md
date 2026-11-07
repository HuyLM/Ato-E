# LearnEnglish — học tiếp với Claude ở tài khoản khác

Thư mục này đủ để một Claude mới (tài khoản khác) dạy tiếp đúng chỗ đang học, không cần gì từ tài khoản cũ.

| File | Là gì |
|---|---|
| `gia-su-tieng-anh.zip` | Skill gia sư — file để tải lên Claude |
| `gia-su-tieng-anh.skill` | Cùng nội dung với file .zip (định dạng .skill) |
| `gia-su-tieng-anh/` | Nội dung skill để xem hoặc sửa: SKILL.md, lộ trình, kịch bản buổi học, Anki, script |
| `tien-do.md` | Tiến độ: trình độ, lỗi cần luyện, Anki, nhật ký các buổi. Gia sư đọc đầu buổi, ghi lại cuối buổi |
| `bai-tap-tiep-theo.md` | Bài soạn sẵn cho các buổi tới, có đáp án (bạn không cần đọc). Dùng lâu dài: mỗi buổi gia sư cập nhật theo khuôn trong file |
| `audio-bai-tap-tiep-theo.html` | Audio cho bài Nghe — mở bằng Chrome hoặc Edge khi gia sư bảo |

## Cài lên tài khoản mới (một lần)

1. **Bật chạy code:** Settings → Capabilities → bật "Code execution and file creation" (giao diện Settings mới gọi là "Create and edit files"). Skill cần mục này.
2. **Tải skill lên:** Customize → Skills → nút "+" → "+ Create skill" → "Upload a skill" → chọn `gia-su-tieng-anh.zip` → bật công tắc của skill.
3. **Tạo Project "English"** (khuyên dùng): dán khối "Hướng dẫn cho Project" bên dưới vào phần Instructions, rồi tải `tien-do.md` và `bai-tap-tiep-theo.md` lên Project.
   Không dùng Project thì mỗi lần học đính kèm 2 file này vào chat.
4. **Bắt đầu:** mở chat mới trong Project, nhắn "Bắt đầu buổi học".

Nếu dùng app Claude trên máy tính, có thể thêm thẳng thư mục này vào chat (nút "+" cạnh ô nhắn tin → "Add folder") để gia sư đọc và ghi file trực tiếp, khỏi tải lên tải xuống.

## Hướng dẫn cho Project (dán vào Instructions)

```text
Bạn là gia sư tiếng Anh của mình. Mình mới bắt đầu, chỉ cần Đọc và Nghe để dùng trong công việc lập trình game Unity.
- Dùng skill gia-su-tieng-anh. Đầu mỗi buổi đọc tien-do.md và bai-tap-tiep-theo.md trong Project; cuối buổi cập nhật lại cả hai file.
- Bám theo lộ trình trong skill (references/lo-trinh.md); nếu chưa rõ mình đang ở giai đoạn nào thì hỏi trước.
- Giải thích bằng tiếng Việt, ví dụ lấy từ bối cảnh làm game.
- Khi mình đưa một câu hoặc đoạn tiếng Anh, đừng dịch ngay (trừ khi mình ghi "dịch luôn"): hỏi mình đoán nghĩa trước, rồi mới chỉ ra cấu trúc câu và chỗ sai.
- Bài đọc, bài nghe, bài tập tạo cho mình phải vừa trình độ hiện tại (hiểu được khoảng 90%).
- Gửi bài tập từng phần: làm xong phần nào mới gửi phần tiếp theo.
```

## Mỗi buổi học

- Gia sư đọc 2 file → hỏi học buổi nào → gửi bài từng phần trong chat.
- Nhắn "lưu tiến độ" bất cứ lúc nào để lưu ngay.
- Cuối buổi gia sư cập nhật `tien-do.md` và `bai-tap-tiep-theo.md`. Ghi thẳng được vào Project hay thư mục thì xong; nếu gia sư gửi file mới cho bạn tải về → thay file cũ trong thư mục này (và tải lại lên Project).
- Luôn giữ các file trong thư mục này đi cùng nhau: mang thư mục sang tài khoản nào cũng học tiếp được.

## Anki

Không đổi gì: Anki trên máy tính và AnkiWeb không gắn với tài khoản Claude. Bộ thẻ mới gia sư gửi (.apkg) → mở bằng Anki trên máy tính → Sync.

Nguồn cách cài skill: [Use skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).
