<div align="center">
  <h1>ExamTopics Scraper</h1>
  <p>Một ứng dụng tải nội dung từ ExamTopics qua giao diện web tối giản sử dụng <b>Streamlit</b>. Tích hợp sẵn cơ chế cache an toàn, hiển thị tiến trình thời gian thực và tự động tối ưu hóa hiệu suất.</p>
</div>

---

## ✨ Tính Năng Nổi Bật
- **Quét liên kết siêu tốc:** Tự động trích xuất cấu trúc đường dẫn các câu hỏi thuộc những hãng công nghệ lớn (Microsoft, Cisco, CompTIA, AWS,...).
- **Hệ Thống Tránh Block (Anti-ban Engine):** Cơ chế Sleep tự động theo nhịp ngẫu nhiên và quản lý Session/Retry chặt chẽ qua `urllib3`.
- **Smart Cache Hit:** Hệ thống thông minh ngay lập tức phản hồi file kết quả dữ liệu trong mili-giây nếu dữ liệu đã được cào trước đó.
- **Tự Động Dọn Dẹp (Auto-Clean):** Tích hợp engine dọn dẹp âm thầm (xoá cache cũ trên 90 ngày hoặc dọn files khi server vượt 10GB).
- **Trải Nghiệm Hoàn Hảo:** Gọn gàng từ thiết kế đến báo cáo Log (sắp xếp mới nhất). Xuất trực tiếp định dạng Excel/CSV.

## 🚀 Hướng Dẫn Sử Dụng (Walkthrough)
1. **Truy cập web app:** Mở web sau khi khởi chạy hoàn tất theo các hướng dẫn phía dưới.
2. **Cấu hình trích xuất:** Lựa chọn tên Hãng, quy định trang xuất phát và trang kết thúc.
3. **Thực thi:** Máy quét sẽ làm việc hoàn toàn song song kèm đồng hồ đếm ngược với nhật ký siêu gọn.
4. **Tải file:** Nhận về ngay tập tin CSV chuẩn với format `{hãng}-{trang}-{ngày_tháng}.csv` qua 1 thao tác click duy nhất.

---

## 🛠 Hướng Dẫn Triển Khai (Deployment)

Dự án này là mã nguồn mở hỗ trợ linh hoạt 2 nền tảng máy chủ Linux và kiến trúc Azure Cloud App.

### 1. Triển Khai Tự Động (All-in-One) Trên Linux
Bạn có máy chủ Ubuntu, CentOS hay Debian? Hệ thống cung cấp sẵn một chuỗi mã lệnh kích hoạt động bao hàm mọi cấu hình môi trường, tải script tĩnh ngầm và cấu hình Systemd tự động.

Chạy duy nhất các lệnh sau trên Linux Terminal của bạn:

```bash
# Clone dự án về máy
git clone https://github.com/your-username/examtopics-scraper.git
cd examtopics-scraper

# Cấp quyền và chạy công cụ khởi tạo siêu tốc
chmod +x install.sh
./install.sh
```
Sau 1 phút, project sẽ vận hành độc lập bằng dịch vụ khởi động ngầm (`systemd`) ở **Cổng 8000** ổn định 24/7.


### 2. Triển Khai Lên Azure App Service
Nếu bạn quyết định tin dùng năng lượng đám mây (Cloud), kiến trúc này phù hợp nhất với **Azure Web App Linux**.

**Cài đặt qua Portal:**
- Runtime stack: **Python 3.11 / 3.12**
- Operating System: **Linux**

**Cấu hình Startup Engine:**
Vào mục nhánh **Configuration** > **General settings**, gán dòng Startup Command sau cho Azure biết cách kích hoạt Server backend:
```bash
python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0
```

**Đẩy Mã Nguồn Lên Tương Tác:**
```bash
git remote add azure <LinkGitAzureUrl>
git push azure main
```
Hệ sinh thái Microsoft Azure sẽ tự động tải các gói phụ thuộc Python trong file `requirements.txt` và khởi động UI ra internet toàn cầu một cách trơn tru!

---

<br>
<div align="center">
  <i>made by Nhan with love ❤️ powered by Antigravity</i>
</div>
