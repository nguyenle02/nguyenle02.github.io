# E-E-A-T Checklist — PTE Magic

E-E-A-T **không phải** một yếu tố bạn "thêm" được. Đó là cách hệ thống đánh giá:
*trang này có đáng tin để đưa cho người dùng đang ra quyết định lớn không?*

## Bốn tầng, áp cho PTE Magic

| Tầng | Câu hỏi | PTE Magic có | Thiếu |
|---|---|---|---|
| **E**xperience | Người viết đã thật sự làm việc này? | trainer chấm hàng nghìn bài; học viên đạt 65/79/90 | **không có byline cho từng bài** |
| **E**xpertise | Có năng lực được công nhận? | đội PTE specialist; Pearson Elite Partner | không thấy hồ sơ tác giả |
| **A**uthoritativeness | Domain được công nhận? | 400.000+ học viên, Bett Asia, Edu 4.0, VN–Úc EdTech Alliance | **không được khai báo bằng schema** |
| **T**rustworthiness | Có thể tin không? | học viên nêu tên + điểm | trang refund thiếu, ngày cập nhật không thấy |

## Checklist chấm điểm mỗi bài (0–100)

### Experience — 25 điểm
- [ ] 15 — chi tiết chỉ người trong cuộc mới biết (không phải thứ SERP nào cũng có)
- [ ] 5 — ví dụ có tên/ngày/kết quả
- [ ] 5 — ảnh/video từ sản phẩm thật (màn hình score report)

### Expertise — 25 điểm
- [ ] 10 — tác giả có tên + chức danh + link profile
- [ ] 5 — tác giả có trang profile thật (không phải trang rỗng)
- [ ] 5 — chuyên môn khớp chủ đề (không để "SEO Team" viết bài điểm số)
- [ ] 5 — bài YMYL có `reviewer` (trainer/Head of Training)

### Authoritativeness — 25 điểm
- [ ] 10 — giải thưởng/partnership nêu **bằng text**, không chỉ ảnh, và có trong schema
- [ ] 5 — nguồn **sơ cấp** được nêu tên (Pearson, IRCC, Home Affairs)
- [ ] 5 — bài được bên khác trích (đo qua Ahrefs / tìm kiếm)
- [ ] 5 — `sameAs` về các hồ sơ chính chủ

### Trustworthiness — 25 điểm
- [ ] 10 — ngày cập nhật hiển thị + `dateModified` khớp
- [ ] 5 — HTTPS + chính sách refund/giải quyết tranh chấp **có trang riêng**
- [ ] 5 — assertion không chứng minh được → đã bỏ hoặc gắn nhãn
- [ ] 5 — không "đảm bảo", "chắc chắn", "100%" về kết quả thi/visa

**Cách đọc điểm:** <60 = đừng publish. 60–79 = publish nếu không phải YMYL.
≥80 = publish. **Bài YMYL phải ≥80, không ngoại lệ.**

## YMYL — định nghĩa rõ cho site này

PTE Magic là EdTech, nhưng nó có **rất nhiều** nội dung nằm sát ranh giới YMYL:
- ✅ **Là YMYL:** visa/định cư · học bổng · chi phí, vay du học · yêu cầu điểm cho đăng ký
  hành nghề y tá/điều dưỡng · "thay đổi chính sách của <nước>"
- ⚠️ **Vùng xám:** mẹo làm bài có ảnh hưởng quyết định thi/đỗ · chiến lược target band
- ❌ **Không phải YMYL:** tính năng sản phẩm, cách dùng platform, blog về văn hoá

Với YMYL, 4 thứ bắt buộc — `policy_gate.py` enforce 3 cái đầu:
1. author là người thật, có chức danh, có trang profile
2. ngày cập nhật ≤90 ngày
3. link tới nguồn chính thức của chính phủ/Pearson
4. không có câu hứa/cam kết về kết quả

## Vì sao "author" quan trọng với PTE hơn với site khác

Đối thủ PTE của bạn — E2, Alfa, Gurully, APEUni — **không có ai có 400.000+ học viên thật**
kết hợp với Pearson partnership. Nếu PTE Magic cũng không nêu người, bạn đang tự nguyện
cạnh tranh bằng điểm yếu nhất của mình.

Không có tên tác giả thật → bạn không khác gì farm content dùng AI.
Có tên trainer thật → bạn là chuyên gia duy nhất có dữ liệu đó.

## Quy trình nếu bạn không có người đủ điều kiện đứng tên

**Không** bịa "Sarah Johnson, PTE Specialist". **Không** dùng tài khoản chưa có.
Cả hai **đều** phát hiện được. Đúng là 1 trong 4:

1. Có trainer → để họ đứng tên, bạn là `reviewer`.
2. Có dữ liệu platform → đứng tên với tư cách người có quyền truy cập dữ liệu
   ("Data Analyst, PTE Magic — n=1.240 bài").
3. Không có ai → xuất bản dưới danh nghĩa tổ chức (`Organization` author), nhưng **giảm**
   số bài YMYL, đừng tăng.
4. Nội dung không người chịu trách nhiệm → **đừng đăng**.

## Kiểm tra nhanh "bài này có đáng tồn tại không"

Trả lời **có** ít nhất 2/3:
1. Người dùng có thể làm điều gì đó sau khi đọc mà họ không làm được trước đó?
2. Có ≥1 dữ kiện không có trong top 5 kết quả?
3. Nếu bạn xoá bài này, site có tệ đi không?

Không → `policy_gate.py` sẽ cảnh báo. Bạn đã có đủ lý do để không viết.
