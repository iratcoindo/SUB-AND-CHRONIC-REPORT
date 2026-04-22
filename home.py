import streamlit as st

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="iRATco Platform",
    page_icon="logo.png",
    layout="wide"
)

# =========================
# USER DATA
# =========================
USERS = {
    "admin": "iratcolab1",
    "lab": "iratcolab5"
}

# =========================
# SESSION INIT
# =========================
st.session_state.setdefault("authenticated", False)

# =========================
# LOGIN PAGE
# =========================
if not st.session_state.authenticated:

    # 🔒 HIDE SIDEBAR
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([7,2])

    with col1:
        st.markdown("""
        <h1 style="color:#4b5563;">🔒 Login to: iRATco Sci Data Analysis Platform</h1>
        <div style="color:#9ca3af;">
        Advanced Laboratory Analysis Platform
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.image("logo_iratco.png", width=230)

    # 🔥 FORM (STABIL)
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username in USERS and USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password")

    # FOOTER
    st.markdown("""
    © 2026 Mawar Subangkit  
    **Data Statistical Analysis Platform**  
    
    If you use this software, please cite:
    
    **Subangkit**, MAWAR (2026)  
    iRATco Data Statistical Analysis Platform
    """)
    st.stop()
    

# ===============================
# MAIN APP (SETELAH LOGIN)
# ===============================

# HEADER
col1, col2 = st.columns([8,2])
with col1:
    st.title("📊 iRATco in-Vivo Platform")
with col2:
    st.image("logo_iratco.png", width=250)

st.markdown("""
Designed for researchers, iRATco Data Analysis Platform streamlines statistical workflows and enhances data interpretation with precision and clarity
""")

st.markdown("---")
st.markdown("""
Software ini dikembangkan oleh iRATco Laboratory untuk meningkatkan efektivitas dan efisiensi dalam pengolahan data. Metode yang digunakan telah mengikuti protokol baku yang terstandarisasi guna memastikan konsistensi dan keandalan hasil analisis.

Aplikasi ini dirancang khusus untuk penggunaan internal dan tidak diperuntukkan untuk distribusi umum. Apabila terdapat kebutuhan penggunaan lebih lanjut, kolaborasi, atau informasi tambahan, silakan menghubungi iRATco Laboratory melalui email: office-indo@iratco.co.id
</div>

<style>
@keyframes bounce {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(-6px); }
}
</style>
""", unsafe_allow_html=True)

# LOGOUT
if st.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()
