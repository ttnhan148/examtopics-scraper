import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import random
import csv
from datetime import datetime
from io import StringIO
import json
import os

# ==========================================
# CẤU HÌNH BIẾN CHUNG & CACHING (LỊCH SỬ)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# Tạo thư mục tự động nếu chưa có
os.makedirs(DATA_DIR, exist_ok=True)

def load_history():
    """Tải lịch sử file JSON"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    """Lưu lịch sử xuống file JSON"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def clean_storage_and_history():
    """Tự động dọn dẹp file CSV vượt dung lượng (max 10GB) và xoá lịch sử (quá 90 ngày)"""
    history = load_history()
    now = datetime.now()
    valid_history = []
    deleted_fps = set()
    
    # 1. Dọn dẹp quá 90 ngày
    for r in history:
        try:
            r_ts = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
            if (now - r_ts).days <= 90:
                valid_history.append(r)
            else:
                if os.path.exists(r["file_path"]):
                    try:
                        os.remove(r["file_path"])
                        deleted_fps.add(r["file_path"])
                    except:
                        pass
        except ValueError:
            valid_history.append(r)
            
    # 2. Ngưỡng 10GB
    MAX_SIZE_BYTES = 10 * 1024 * 1024 * 1024
    
    def get_dir_size():
        try:
            return sum(os.path.getsize(os.path.join(DATA_DIR, f)) for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f)))
        except:
            return 0
            
    if get_dir_size() > MAX_SIZE_BYTES:
        csv_files = []
        for f in os.listdir(DATA_DIR):
            if f.endswith(".csv"):
                fp = os.path.join(DATA_DIR, f)
                csv_files.append((fp, os.path.getmtime(fp)))
        
        csv_files.sort(key=lambda x: x[1]) # Tăng dần tuổi thọ (Cũ nhất lên đầu)
        
        for fp, _ in csv_files:
            if get_dir_size() <= MAX_SIZE_BYTES:
                break
            try:
                os.remove(fp)
                deleted_fps.add(fp)
            except:
                pass
                
        valid_history = [r for r in valid_history if r.get("file_path") not in deleted_fps]
        
    # Lưu xuống Disk nếu có bất kì thay đổi nào (xoá quá 90 ngày hoặc xoá quá dung lượng)
    if len(valid_history) != len(history) or len(deleted_fps) > 0:
        save_history(valid_history)

# Kích hoạt dọn dẹp rác chạy ngầm
clean_storage_and_history()

def check_cache(vendor, start_page, end_page):
    """Kiểm tra xem quét trang đã có trong lịch sử chưa (end_page phải bằng hoặc lớn hơn)"""
    history = load_history()
    # Tìm tất cả lịch sử ứng với vendor, và khoảng trang được bao trọn
    valid_records = [
        r for r in history
        if r['vendor'] == vendor and r['start_page'] <= start_page and r['end_page'] >= end_page
    ]
    if valid_records:
        # Lấy bản ghi sát / mới nhất đáp ứng nhu cầu này
        return valid_records[-1] 
    return None

# ==========================================
# CẤU HÌNH SCRAPER TỪNG TRANG
# ==========================================

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0',
]

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=2,
        status_forcelist=(403, 429, 500, 502, 503, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_internal_links(session, base_url, page_number):
    url = base_url.format(page_number)
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/',
    }
    try:
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()  
    except requests.exceptions.RequestException as e:
        return [], str(e)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if '-exam-' in href and href.startswith('/'):
            links.add(f"https://www.examtopics.com{href}")
            
    return list(links), None

# ==========================================
# GIAO DIỆN STREAMLIT
# ==========================================
# ==========================================
st.set_page_config(page_title="ExamTopics Scraper", layout="wide")

# SIDEBAR LỊCH SỬ CHẠY
st.sidebar.title("Quản lý hệ thống")
history_data = load_history()

with st.sidebar.expander("📜 Lịch sử chạy", expanded=False):
    if history_data:
        for r in reversed(history_data):
            col_info, col_btn = st.columns([3, 2])
            with col_info:
                st.markdown(f"**{r['vendor'].upper()}**")
                st.caption(f"Trang {r['start_page']}-{r['end_page']} • {r['total_links']} links<br>{r['timestamp']}", unsafe_allow_html=True)
            with col_btn:
                st.write("")
                if os.path.exists(r['file_path']):
                    with open(r['file_path'], 'rb') as f:
                        file_data = f.read()
                    dl_name = f"examtopic-{r['vendor']}-{r['end_page']}.csv"
                    st.download_button(
                        "Tải về", 
                        data=file_data, 
                        file_name=dl_name, 
                        key=f"dl_{r['file_path']}_{r['timestamp']}",
                        use_container_width=True
                    )
                else:
                    st.button("Đã xoá", disabled=True, key=f"del_{r['timestamp']}", use_container_width=True)
            st.divider()
    else:
        st.info("Chưa có lịch sử chạy nào.")
    

# VÙNG CHÍNH TIẾN TRÌNH
st.title("ExamTopics Scraper")
st.markdown("Hệ thống tự động lưu trữ dữ liệu. **Vui lòng nhập thông tin để bắt đầu.**")

col1, col2 = st.columns(2)
with col1:
    vendor = st.selectbox(
        "Hãng", 
        ["Microsoft", "Cisco", "Amazon", "Oracle", "Google", "CompTIA", "Palo-Alto-Networks", "VMware", "Salesforce"]
    )
with col2:
    vendor_lower = vendor.lower()
    url = f"https://www.examtopics.com/discussions/{vendor_lower}/"
    st.markdown(f"<div style='margin-bottom: 6px; font-size: 14px; font-weight: 400; color: inherit;'>Format URL</div>"
                f"<div style='padding: 8px 14px; background-color: rgba(128, 128, 128, 0.1); border-radius: 8px;'>"
                f"<a href='{url}' target='_blank' style='text-decoration: none;'>{url}</a></div>", 
                unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    start_page = st.number_input("Trang bắt đầu", min_value=1, value=1)
with col4:
    end_page = st.number_input("Trang kết thúc", min_value=start_page, value=max(start_page, 10))

start_btn = st.button("Bắt đầu tiến trình", use_container_width=True, type="primary")

if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None
if 'total_links' not in st.session_state:
    st.session_state.total_links = 0
if 'logs' not in st.session_state:
    st.session_state.logs = []

output_placeholder = st.empty()

if start_btn:
    st.session_state.process_complete = False
    st.session_state.logs = []
    st.divider()
    
    cached_record = check_cache(vendor_lower, start_page, end_page)
    
    if cached_record and os.path.exists(cached_record['file_path']):
        # TRÚNG CACHE - LẤY NGAY KHÔNG CẦN CHỜ
        st.success(f"Sử dụng bộ nhớ đệm (thời gian quét: {cached_record['timestamp']}, đến trang {cached_record['end_page']}).")
        
        with open(cached_record['file_path'], 'r', encoding='utf-8') as f:
            csv_data = f.read()
            
        today_str = datetime.now().strftime("%d%m%Y")
        file_name = f"examtopic-{vendor_lower}-{end_page}-{today_str}.csv"
        
        st.session_state.csv_data = csv_data
        st.session_state.file_name = file_name
        st.session_state.total_links = cached_record.get('total_links', 0)
        st.session_state.logs = [f"Tải từ bộ nhớ đệm thành công. Dữ liệu hoàn tất tới trang {cached_record['end_page']}."]
        st.session_state.process_complete = True
        st.rerun()
        
    else:
        # DO KHÔNG TRÚNG LIỀN, TIẾN HÀNH QUÉT MỚI MẠNG
        session = create_session()
        all_links = set()
        base_URL = f"https://www.examtopics.com/discussions/{vendor_lower}/{{}}/"
        total_pages = end_page - start_page + 1
        
        with output_placeholder.container():
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Setup 3 columns row
            col_m, col_t, col_d = st.columns(3)
            with col_m:
                links_count_metric = st.empty()
            with col_t:
                countdown_text = st.empty()
            with col_d:
                st.empty() # empty padding cho download button lúc sau render
                
            log_view = st.empty()
            log_messages = []

            for idx, page in enumerate(range(start_page, end_page + 1)):
                status_text.markdown(f"**Đang xử lý trang {page} / {end_page}...**")
                
                links, err = get_internal_links(session, base_URL, page)
                
                if err:
                    log_messages.insert(0, f"Lỗi tại trang {page}: {err}")
                else:
                    all_links.update(links)
                    log_messages.insert(0, f"Hoàn thành trang {page}: Tìm thấy {len(links)} liên kết mới.")
                
                links_count_metric.metric("Số liên kết trích xuất", f"{len(all_links)}")
                
                log_html = "<div style='height: 200px; overflow-y: auto; background-color: #0E1117; padding: 10px; border-radius: 5px; font-family: monospace; line-height: 1.5; border: 1px solid #333; margin-bottom: 20px;'>"
                log_html += "<br>".join(log_messages)
                log_html += "</div>"
                log_view.markdown(log_html, unsafe_allow_html=True)
                
                progress = (idx + 1) / total_pages
                progress_bar.progress(progress)
                
                if page < end_page:
                    delay = random.uniform(2.5, 5.0)
                    steps = int(delay * 10)
                    for step in range(steps, 0, -1):
                        time_left = step / 10.0
                        countdown_text.metric("Thời gian chờ", f"{time_left:.1f}s")
                        time.sleep(0.1)
                    countdown_text.empty() 

            status_text.success(f"Quá trình hoàn tất. Dữ liệu đã trích xuất đến trang {end_page} và được lưu trữ an toàn.")
            
        # 2. XỬ LÝ KẾT QUẢ: LƯU FILE SERVER LOCAL VÀ GIAO TỚI KHÁCH HÀNG TẢI QUA WEB
        if all_links:
            # Ghi ra Ram Buffer cho người dùng tải trưc tiếp
            csv_buffer = StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["Link"])
            for link in all_links:
                writer.writerow([link])
                
            csv_data = csv_buffer.getvalue()
            
            # Ghi trưc tiep vao ổ đĩa server folder /data để dùng cho lần sau
            timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
            server_file_name = f"{vendor_lower}_{start_page}_{end_page}_{timestamp_str}.csv"
            server_file_path = os.path.join(DATA_DIR, server_file_name)
            
            with open(server_file_path, "w", encoding="utf-8", newline="") as f:
                f.write(csv_data)
                
            # Lưu lịch sử (metadata json)
            history_record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "vendor": vendor_lower,
                "start_page": start_page,
                "end_page": end_page,
                "total_links": len(all_links),
                "file_path": server_file_path
            }
            history_data.append(history_record)
            save_history(history_data)
            
            today_str = datetime.now().strftime("%d%m%Y")
            user_file_name = f"examtopic-{vendor_lower}-{end_page}-{today_str}.csv"
            
            st.session_state.csv_data = csv_data
            st.session_state.file_name = user_file_name
            st.session_state.total_links = len(all_links)
            st.session_state.logs = log_messages
            st.session_state.process_complete = True
            st.rerun()
        else:
            st.warning("Không có dữ liệu để lưu trữ.")

if st.session_state.get('process_complete') and st.session_state.get('csv_data'):
    with output_placeholder.container():
        st.divider()
        col_m, col_t, col_d = st.columns(3)
        col_m.metric("Số liên kết trích xuất", f"{st.session_state.get('total_links', 0)}")
        col_t.metric("Trạng thái", "Hoàn thành")
        
        with col_d:
            st.write("") # Tạo khoảng trống để button align thẳng hàng với text ở trên
            st.download_button(
                label=f"Tải về máy ({st.session_state.file_name})",
                data=st.session_state.csv_data,
                file_name=st.session_state.file_name,
                mime='text/csv',
                use_container_width=True,
                type="primary"
            )
            
        if st.session_state.get('logs'):
            log_html = "<div style='height: 200px; overflow-y: auto; background-color: #0E1117; padding: 10px; border-radius: 5px; font-family: monospace; line-height: 1.5; border: 1px solid #333;'>"
            log_html += "<br>".join(st.session_state.logs)
            log_html += "</div>"
            st.markdown(log_html, unsafe_allow_html=True)
