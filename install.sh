#!/bin/bash
# ==============================================================================
# Script cài đặt tự động ExamTopics Scraper Web App cho máy chủ Linux
# Hỗ trợ (Ubuntu/Debian) và các hệ điều hành dùng Systemd
# ==============================================================================

echo "🚀 Bắt đầu cài đặt ExamTopics Scraper Web App trên Linux Server..."

APP_DIR=$(pwd)

# 1. Cài đặt Python3, Pip và Virtualenv
echo "📦 [1/4] Đang kiểm tra và cài đặt Python3, Pip, Virtualenv..."
if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv
elif [ -x "$(command -v yum)" ]; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip
else
    echo "⚠️ Không tìm thấy apt-get hoặc yum. Vui lòng tự cài Python3."
fi

# 2. Tạo Môi trường ảo (Virtual Environment)
echo "🐍 [2/4] Đang thiết lập Môi trường ảo (Virtual environment) cách ly..."
python3 -m venv venv
source venv/bin/activate

# 3. Cài đặt thư viện Streamlit và Scraper
echo "📚 [3/4] Đang cài đặt thư viện nền tảng (Streamlit, BeautifulSoup...)..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Tạo Auto-Start Service (Systemd) chạy ngầm 24/7 bảo vệ sập
echo "⚙️  [4/4] Đang cấu hình Systemd Service để Web App luôn chạy ngầm 24/7..."
SERVICE_FILE=/etc/systemd/system/examtopics.service

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=ExamTopics Scraper Streamlit Web App
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/streamlit run $APP_DIR/app.py --server.port 8000 --server.address 0.0.0.0
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Tải cấu hình Systemd và cho phép ứng dụng khởi động lại cùng máy chủ
sudo systemctl daemon-reload
sudo systemctl enable examtopics
sudo systemctl restart examtopics

# 5. Mở Port 8000 xuyên qua Tường lửa (Tùy chọn)
if [ -x "$(command -v ufw)" ]; then
    sudo ufw allow 8000/tcp  > /dev/null 2>&1
    echo "🔓 Đã tự động mở port 8000 xuyên Tường Nhạy UFW."
fi

echo ""
echo "=========================================================="
echo "✅ HOÀN TẤT TỰ ĐỘNG CÀI ĐẶT!"
echo "=========================================================="
echo "🌐 Ứng dụng hiện đang được mở tại: http://<IP_MAY_CHU_CUA_BAN>:8000"
echo ""
echo "--- Các câu lệnh Control Web App nhanh cho bạn ---"
echo "🛑 Dừng app  : sudo systemctl stop examtopics"
echo "▶️ Chạy lại   : sudo systemctl start examtopics"
echo "📜 Xem Log   : sudo journalctl -u examtopics -f"
echo "=========================================================="
