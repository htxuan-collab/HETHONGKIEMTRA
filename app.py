import streamlit as st
import pandas as pd
import json
import os
import random
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ================= CẤU HÌNH ĐƯỜNG DẪN & FILE =================
CONFIG_FILE = "config.json"
RESULT_FILE = "ket_qua.csv"
DETAILED_DIR = "bai_thi_chi_tiet"

if not os.path.exists(DETAILED_DIR):
    os.makedirs(DETAILED_DIR)

DEFAULT_CONFIG = {
    "school": "SỞ GIÁO DỤC VÀ ĐÀO TẠO",
    "title": "KỲ THI KIỂM TRA THƯỜNG XUYÊN 2026",
    "subject": "TIN HỌC 12",
    "time": 45,
    "part1_count": 12,
    "part2_count": 4,
    "part3_count": 6,
    "bank": "questions.xlsx",
    "admin_password": "admin"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_json(CONFIG_FILE, DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                cfg.setdefault(k, v)
            return cfg
    except:
        return DEFAULT_CONFIG.copy()

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

config = load_config()

st.set_page_config(page_title="Hệ thống thi trực tuyến", layout="wide")

if "mode" not in st.session_state:
    st.session_state.mode = "student"

# ==============================================================================
# PHẦN 1: TRANG QUẢN TRỊ GIÁO VIÊN (ADMIN)
# ==============================================================================
if st.session_state.mode == "admin":
    st.title("⚙️ TRANG QUẢN TRỊ VÀ CẤU HÌNH HỆ THỐNG THI")

    if not st.session_state.get("admin_logged", False):
        col_pwd1, col_pwd2 = st.columns([1, 2])
        with col_pwd1:
            pwd = st.text_input("🔑 Nhập mật khẩu Quản trị viên:", type="password")
            if st.button("Đăng nhập", type="primary", use_container_width=True):
                if pwd == config.get("admin_password", "admin"):
                    st.session_state.admin_logged = True
                    st.rerun()
                else:
                    st.error("Mật khẩu không chính xác!")
            if st.button("⬅ Quay lại trang làm bài", use_container_width=True):
                st.session_state.mode = "student"
                st.rerun()
        st.stop()

    col_a, col_b = st.columns([8, 2])
    with col_b:
        if st.button("🚪 Đăng xuất Admin", type="secondary", use_container_width=True):
            st.session_state.admin_logged = False
            st.session_state.mode = "student"
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["🛠️ Cấu hình đề thi", "📋 Bảng điểm tổng hợp", "📝 Bài làm chi tiết"])

    with tab1:
        st.subheader("1. Cấu hình thông tin kỳ thi & Số lượng câu hỏi")
        with st.form("config_form"):
            col_cfg1, col_cfg2 = st.columns(2)
            with col_cfg1:
                school = st.text_input("Đơn vị / Trường học:", value=config.get("school"))
                title = st.text_input("Tên kỳ thi:", value=config.get("title"))
                subject = st.text_input("Tên môn học:", value=config.get("subject"))
                admin_password = st.text_input("Mật khẩu Admin mới:", value=config.get("admin_password"))

            with col_cfg2:
                duration = st.number_input("Thời gian làm bài (Phút):", min_value=1, max_value=180, value=int(config.get("time")))
                p1_c = st.number_input("Số câu PHẦN I (Trắc nghiệm 4 lựa chọn):", min_value=0, max_value=50, value=int(config.get("part1_count")))
                p2_c = st.number_input("Số câu PHẦN II (Đúng / Sai):", min_value=0, max_value=20, value=int(config.get("part2_count")))
                p3_c = st.number_input("Số câu PHẦN III (Trả lời ngắn):", min_value=0, max_value=20, value=int(config.get("part3_count")))

            save_btn = st.form_submit_button("💾 Lưu Cấu Hình", type="primary")
            if save_btn:
                config.update({
                    "school": school, "title": title, "subject": subject,
                    "time": duration, "part1_count": p1_c, "part2_count": p2_c,
                    "part3_count": p3_c, "admin_password": admin_password
                })
                save_json(CONFIG_FILE, config)
                st.success("Đã lưu cấu hình thành công!")
                st.rerun()

        st.divider()
        st.subheader("2. Cập nhật Ngân hàng câu hỏi (File Excel)")
        uploaded_bank = st.file_uploader("Tải file câu hỏi mới (.xlsx):", type=["xlsx"])
        if uploaded_bank is not None:
            bank_path = config.get("bank", "questions.xlsx")
            with open(bank_path, "wb") as f:
                f.write(uploaded_bank.getbuffer())
            st.success("Tải file câu hỏi thành công!")

    with tab2:
        st.subheader("Bảng điểm tổng hợp tất cả thí sinh")
        col_dl1, col_dl2 = st.columns([6, 3])
        with col_dl2:
            if st.button("🗑️ XÓA TOÀN BỘ BẢNG ĐIỂM & BÀI LÀM", type="primary", use_container_width=True):
                if os.path.exists(RESULT_FILE): os.remove(RESULT_FILE)
                if os.path.exists(DETAILED_DIR):
                    for f in os.listdir(DETAILED_DIR):
                        fp = os.path.join(DETAILED_DIR, f)
                        if os.path.isfile(fp): os.remove(fp)
                st.success("Đã làm mới dữ liệu thành công!")
                time.sleep(1)
                st.rerun()

        if os.path.exists(RESULT_FILE):
            df_res = pd.read_csv(RESULT_FILE)
            st.dataframe(df_res, use_container_width=True)
            csv_data = df_res.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("📥 Tải Bảng Điểm Tổng Hợp (CSV)", data=csv_data, file_name="Bang_Diem_Tong_Hop.csv", mime="text/csv")
        else:
            st.info("Chưa có lượt nộp bài nào.")

    with tab3:
        st.subheader("Chi tiết bài làm từng học sinh")
        detail_files = [f for f in os.listdir(DETAILED_DIR) if f.endswith('.xlsx')]
        if detail_files:
            selected_file = st.selectbox("Chọn bài làm học sinh:", detail_files)
            file_path = os.path.join(DETAILED_DIR, selected_file)
            df_detail = pd.read_excel(file_path)
            st.dataframe(df_detail, use_container_width=True)
            with open(file_path, "rb") as f:
                st.download_button(f"📥 Tải Bài Làm Chi Tiết ({selected_file})", data=f.read(), file_name=selected_file, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Chưa có file bài thi chi tiết nào.")

    st.stop()

# ==============================================================================
# PHẦN 2: TRANG ĐĂNG NHẬP THÍ SINH
# ==============================================================================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    col_top1, col_top2 = st.columns([8, 2])
    with col_top2:
        if st.button("⚙️ Cấu hình Giáo viên", key="btn_admin"):
            st.session_state.mode = "admin"
            st.rerun()

    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px;">
            <div style="font-size: 1.3rem; color: #166534; font-weight: bold; text-transform: uppercase;">{config.get('school')}</div>
            <div style="font-size: 2.2rem; color: #dc2626; font-weight: 900; margin-top: 5px;">{config.get('title')}</div>
            <div style="font-size: 1.2rem; color: #1e3a8a; font-weight: bold;">Môn: {config.get('subject')} | Thời gian: {config.get('time')} phút</div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align:center;'>ĐĂNG NHẬP THI TRỰC TUYẾN</h4>", unsafe_allow_html=True)
            name = st.text_input("👤 Họ và tên thí sinh:")
            lop = st.text_input("🏫 Lớp:")
            if st.button("🚀 BẮT ĐẦU LÀM BÀI", type="primary", use_container_width=True):
                if name.strip() and lop.strip():
                    st.session_state.login = True
                    st.session_state.name = name.strip()
                    st.session_state.lop = lop.strip()
                    st.session_state.start_time = datetime.now()
                    st.session_state.da_nop_bai = False
                    st.rerun()
                else:
                    st.error("⚠️ Vui lòng nhập đầy đủ Họ tên và Lớp!")
    st.stop()

# ==============================================================================
# PHẦN 3: GIAO DIỆN LÀM BÀI THI
# ==============================================================================
st_autorefresh(interval=1000, key="exam_timer")

if "answers" not in st.session_state: st.session_state.answers = {}

p1_count = int(config.get("part1_count", 12))
p2_count = int(config.get("part2_count", 4))
p3_count = int(config.get("part3_count", 6))
duration_min = int(config.get("time", 45))

con_lai_giay = max(0, (duration_min * 60) - int((datetime.now() - st.session_state.start_time).total_seconds()))
phut, giay = con_lai_giay // 60, con_lai_giay % 60
timer_str = f"{phut:02d}:{giay:02d}"

st.markdown("""
    <style>
    .part-header {
        font-weight: bold;
        color: #1e3a8a;
        background-color: #e0f2fe;
        padding: 4px 8px;
        border-radius: 4px;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# 1. BẢNG TIÊU ĐỀ HEADER HÀNG TRÊN CÙNG (Đã căn chỉnh đúng 3 vị trí)
st.markdown(f"""
    <div style="background-color: #f0fdf4; border: 2px solid #86efac; padding: 12px 20px; border-radius: 10px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <!-- BÊN TRÁI: HỌ TÊN HỌC SINH, LỚP -->
            <div style="text-align: left;">
                <div style="font-weight: bold; font-size: 1.1rem; color: #1e3a8a;">👤 Họ và tên: {st.session_state.name}</div>
                <div style="font-weight: bold; font-size: 1.0rem; color: #166534;">🏫 Lớp: {st.session_state.lop}</div>
            </div>
            <!-- Ở GIỮA: BÀI THI, MÔN THI -->
            <div style="text-align: center;">
                <div style="font-weight: 900; font-size: 1.3rem; color: #dc2626; text-transform: uppercase;">🏆 {config.get('title')}</div>
                <div style="font-weight: bold; font-size: 1.0rem; color: #1e3a8a;">Môn thi: {config.get('subject')}</div>
            </div>
            <!-- BÊN PHẢI: ĐỒNG HỒ ĐẾM NGƯỢC -->
            <div style="text-align: right;">
                <div style="background-color: #fef2f2; border: 2px solid #ef4444; color: #dc2626; border-radius: 8px; padding: 6px 16px; font-weight: bold; font-size: 1.4rem; display: inline-block;">
                    ⏳ {timer_str}
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

@st.cache_data
def load_quiz():
    file_path = config.get("bank", "questions.xlsx")
    if not os.path.exists(file_path): return None
    try:
        p1 = pd.read_excel(file_path, sheet_name="PHẦN I").rename(columns={'question': 'Câu hỏi', 'answer': 'Đáp án đúng'})
        p1['Phần'] = 1
        p1_list = p1.sample(n=min(p1_count, len(p1))).to_dict('records') if len(p1) > 0 else []
        for q in p1_list:
            opts = [str(q.get('A','')), str(q.get('B','')), str(q.get('C','')), str(q.get('D',''))]
            random.shuffle(opts)
            q['shuffled_map'] = {'A': opts[0], 'B': opts[1], 'C': opts[2], 'D': opts[3]}

        p2 = pd.read_excel(file_path, sheet_name="PHẦN II")
        for col in p2.columns:
            if 'câu hỏi' in str(col).lower(): p2 = p2.rename(columns={col: 'Câu hỏi'}); break
        p2['Phần'] = 2
        p2_list = p2.sample(n=min(p2_count, len(p2))).to_dict('records') if len(p2) > 0 else []

        p3 = pd.read_excel(file_path, sheet_name="PHẦN III").rename(columns={'question': 'Câu hỏi', 'Answer': 'Đáp án đúng'})
        p3['Phần'] = 3
        p3_list = p3.sample(n=min(p3_count, len(p3))).to_dict('records') if len(p3) > 0 else []

        return p1_list + p2_list + p3_list
    except Exception as e:
        return None

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = load_quiz()
    st.session_state.current_q = 0

if not st.session_state.quiz_data:
    st.error("Không thể đọc file đề thi `questions.xlsx`. Vui lòng vào Trang Quản Trị tải lên file đề thi hợp lệ.")
    st.stop()

def nop_bai():
    if st.session_state.get("da_nop_bai"): return
    raw_score, max_raw_score = 0.0, 0.0
    detailed_results = []

    for idx, q in enumerate(st.session_state.quiz_data):
        q_n = str(idx + 1)
        phan = q['Phần']
        u_ans = st.session_state.answers.get(q_n, "")
        correct_ans = str(q.get('Đáp án đúng', '')).strip()

        if phan == 1:
            max_raw_score += 0.25
            correct_content = str(q.get(correct_ans, '')).strip()
            is_correct = (str(u_ans).strip() == correct_content)
            if is_correct: raw_score += 0.25
            detailed_results.append({"Câu": q_n, "Phần": 1, "Nội dung": q.get('Câu hỏi',''), "Trả lời": u_ans, "Đáp án đúng": correct_content, "Kết quả": "Đúng" if is_correct else "Sai"})

        elif phan == 2:
            max_raw_score += 1.0
            true_list = [x.strip().lower() for x in correct_ans.split(',')]
            correct_sub = 0
            sub_details = []
            for i, s in enumerate(['a', 'b', 'c', 'd']):
                user_sub = str(st.session_state.answers.get(f"{q_n}_{s}", "")).strip().lower()
                target_sub = true_list[i] if i < len(true_list) else ""
                if user_sub == target_sub and user_sub != "": correct_sub += 1
                sub_details.append(f"{s}: {user_sub.upper() or 'Trống'} (Đúng: {target_sub.upper()})")
            p2_raw = {1: 0.1, 2: 0.25, 3: 0.5, 4: 1.0}.get(correct_sub, 0.0)
            raw_score += p2_raw
            detailed_results.append({"Câu": q_n, "Phần": 2, "Nội dung": q.get('Câu hỏi',''), "Trả lời": " | ".join(sub_details), "Đáp án đúng": correct_ans, "Điểm thô": p2_raw})

        elif phan == 3:
            max_raw_score += 0.5
            is_correct = (str(u_ans).strip().lower() == correct_ans.lower() and u_ans != "")
            if is_correct: raw_score += 0.5
            detailed_results.append({"Câu": q_n, "Phần": 3, "Nội dung": q.get('Câu hỏi',''), "Trả lời": u_ans, "Đáp án đúng": correct_ans, "Kết quả": "Đúng" if is_correct else "Sai"})

    final_score = round((raw_score / max_raw_score) * 10.0, 2) if max_raw_score > 0 else 0.0
    st.session_state.final_score = final_score
    st.session_state.da_nop_bai = True

    df_detail = pd.DataFrame(detailed_results)
    file_detail_path = os.path.join(DETAILED_DIR, f"{st.session_state.lop}_{st.session_state.name}.xlsx")
    df_detail.to_excel(file_detail_path, index=False)

    row_data = {"Họ tên": st.session_state.name, "Lớp": st.session_state.lop, "Điểm": st.session_state.final_score, "Điểm thô": f"{raw_score}/{max_raw_score}", "Thời gian": datetime.now().strftime("%H:%M:%S %d/%m/%Y")}
    if os.path.exists(RESULT_FILE):
        df_res = pd.read_csv(RESULT_FILE)
        df_res = pd.concat([df_res, pd.DataFrame([row_data])], ignore_index=True)
    else:
        df_res = pd.DataFrame([row_data])
    df_res.to_csv(RESULT_FILE, index=False, encoding="utf-8-sig")

if con_lai_giay <= 0 and not st.session_state.get("da_nop_bai"):
    nop_bai()
    st.rerun()

if st.session_state.get("da_nop_bai"):
    st.balloons()
    st.markdown(f"""
        <div style="text-align: center; padding: 30px; background-color: white; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <h1 style="color: #16a34a;">🎉 BẠN ĐÃ HOÀN THÀNH BÀI THI!</h1>
            <p style="font-size: 1.2rem; color: #475569;">Thí sinh: <b>{st.session_state.name}</b> - Lớp: <b>{st.session_state.lop}</b></p>
            <div style="font-size: 3.5rem; font-weight: 900; color: #dc2626; margin: 15px 0;">{st.session_state.final_score} / 10 Điểm</div>
            <p style="color: #64748b;">Kết quả bài làm đã được gửi về hệ thống của Giáo viên.</p>
        </div>
    """, unsafe_allow_html=True)
else:
    total_qs = len(st.session_state.quiz_data)
    curr_idx = st.session_state.current_q
    q = st.session_state.quiz_data[curr_idx]
    q_n = curr_idx + 1

    def is_q_answered(q_index):
        qn = q_index + 1
        q_obj = st.session_state.quiz_data[q_index]
        p = q_obj.get('Phần', 1)
        if p == 1 or p == 3:
            return bool(st.session_state.answers.get(str(qn)))
        elif p == 2:
            return any(bool(st.session_state.answers.get(f"{qn}_{sub}")) for sub in ['a','b','c','d'])
        return False

    # 2. PHÂN CHIA CÁC CÂU HỎI THEO PHẦN I, II, III
    p1_indices = [i for i, item in enumerate(st.session_state.quiz_data) if item.get('Phần') == 1]
    p2_indices = [i for i, item in enumerate(st.session_state.quiz_data) if item.get('Phần') == 2]
    p3_indices = [i for i, item in enumerate(st.session_state.quiz_data) if item.get('Phần') == 3]

    def render_nav_group(title, indices):
        if not indices: return
        st.markdown(f"<div class='part-header'>{title}</div>", unsafe_allow_html=True)
        cols = st.columns(min(len(indices), 15))
        for idx_col, idx_q in enumerate(indices):
            qn_num = idx_q + 1
            answered = is_q_answered(idx_q)
            is_active = (curr_idx == idx_q)
            
            label = f"✓{qn_num}" if answered else f"{qn_num}"
            
            with cols[idx_col % 15]:
                b_type = "primary" if is_active else "secondary"
                if answered and not is_active:
                    btn_clicked = st.button(f"🟢{qn_num}", key=f"qnav_{qn_num}", use_container_width=True)
                else:
                    btn_clicked = st.button(label, key=f"qnav_{qn_num}", type=b_type, use_container_width=True)

                if btn_clicked:
                    st.session_state.current_q = idx_q
                    st.rerun()

    render_nav_group("📌 PHẦN I: Trắc nghiệm 4 lựa chọn", p1_indices)
    render_nav_group("📌 PHẦN II: Trắc nghiệm Đúng / Sai", p2_indices)
    render_nav_group("📌 PHẦN III: Câu hỏi Trả lời ngắn", p3_indices)

    st.divider()

    # 3. HIỂN THỊ NỘI DUNG CÂU HỎI
    phan_hien_tai = q.get('Phần', 1)
    ten_phan_map = {1: "PHẦN I (Trắc nghiệm 4 lựa chọn)", 2: "PHẦN II (Đúng / Sai)", 3: "PHẦN III (Trả lời ngắn)"}
    
    st.markdown(f"### 📍 CÂU HỎI {q_n} / {total_qs} — <span style='color:#1d4ed8;'>{ten_phan_map.get(phan_hien_tai)}</span>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"#### {q.get('Câu hỏi', 'Nội dung câu hỏi...')}")

        if phan_hien_tai == 1:
            m = q.get('shuffled_map', {})
            opts = [f"A. {m.get('A','')}", f"B. {m.get('B','')}", f"C. {m.get('C','')}", f"D. {m.get('D','')}"]
            old_val = st.session_state.answers.get(str(q_n))
            idx = next((i for i, k in enumerate(['A','B','C','D']) if str(m.get(k)) == str(old_val)), None) if old_val else None
            choice = st.radio("Chọn đáp án:", opts, index=idx, key=f"r1_{q_n}")
            if choice: st.session_state.answers[str(q_n)] = choice.split(". ", 1)[-1]

        elif phan_hien_tai == 2:
            map_p2 = {'a': 'a_text', 'b': 'b_text', 'c': 'c_text', 'd': 'd_text'}
            for s in ['a', 'b', 'c', 'd']:
                k_sub = f"{q_n}_{s}"
                txt_y = q.get(map_p2[s]) or q.get(f"{s}_text") or ""
                col_txt, col_opt = st.columns([0.75, 0.25])
                with col_txt: st.markdown(f"<b>{s}.</b> {txt_y}", unsafe_allow_html=True)
                with col_opt:
                    old_s = st.session_state.answers.get(k_sub)
                    ans_choice = st.radio(f"R2_{k_sub}", ["Đúng", "Sai"], horizontal=True, key=f"r2_{k_sub}", index=None if old_s is None else (0 if old_s=="Đúng" else 1), label_visibility="collapsed")
                    if ans_choice: st.session_state.answers[k_sub] = ans_choice

        elif phan_hien_tai == 3:
            old_v = st.session_state.answers.get(str(q_n), "")
            ans_text = st.text_input("Nhập câu trả lời ngắn của bạn:", value=old_v, key=f"in3_{q_n}")
            st.session_state.answers[str(q_n)] = ans_text.strip()

    col_l, col_m, col_r = st.columns([1, 1, 1])
    with col_l:
        if st.button("⬅ Câu trước", use_container_width=True, disabled=(curr_idx == 0)):
            st.session_state.current_q -= 1
            st.rerun()
    with col_m:
        if st.button("🏁 NỘP BÀI THI", type="primary", use_container_width=True):
            nop_bai()
            st.rerun()
    with col_r:
        if st.button("Câu tiếp theo ➡", use_container_width=True, disabled=(curr_idx == total_qs - 1)):
            st.session_state.current_q += 1
            st.rerun()
