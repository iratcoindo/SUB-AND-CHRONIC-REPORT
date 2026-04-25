import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Hematology Analyzer (Filtered + Sample ID)")

# ===============================
# 📥 UPLOAD
# ===============================
uploaded_file = st.file_uploader("Upload Data", type=["xlsx","csv"])

# ===============================
# 🎯 TARGET KOLOM
# ===============================
TARGET_COLS = [
    "WBC","Neu#","Lym#","Mon#","Eos#","Bas#",
    "Neu%","Lym%","Mon%","Eos%","Bas%",
    "RBC","HGB","HCT","MCV","MCH","MCHC",
    "RDW-CV","RDW-SD",
    "PLT","MPV","PDW","PCT"
]

# ===============================
# 📦 LOAD + FILTER
# ===============================
def load_filtered(file):
    if file is None:
        return None

    try:
        # ===============================
        # LOAD FILE
        # ===============================
        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            df = pd.read_csv(file)

        # ===============================
        # CLEAN KOLOM
        # ===============================
        df.columns = df.columns.astype(str).str.strip()

        # ===============================
        # DETECT SAMPLE ID
        # ===============================
        possible_ids = ["Sample ID", "Sample", "ID", "Patient ID"]

        sample_col = None
        for c in possible_ids:
            if c in df.columns:
                sample_col = c
                break

        # fallback → pakai index
        if sample_col is None:
            df["Sample ID"] = df.index.astype(str)
            sample_col = "Sample ID"

        # ===============================
        # MATCH KOLOM TARGET
        # ===============================
        col_map = {c.strip(): c for c in df.columns}

        selected_cols = []
        for t in TARGET_COLS:
            if t in col_map:
                selected_cols.append(col_map[t])

        if len(selected_cols) == 0:
            st.error("❌ Kolom hematologi tidak ditemukan")
            return None

        # ===============================
        # BUILD FINAL DATA
        # ===============================
        df_final = df[[sample_col] + selected_cols].copy()
        df_final = df_final.rename(columns={sample_col: "Sample ID"})

        # convert numeric
        for c in selected_cols:
            df_final[c] = pd.to_numeric(df_final[c], errors="coerce")

        # ===============================
        # OUTPUT
        # ===============================
        st.success("✅ Filtered hematology siap dianalisa")
        st.dataframe(df_final.head())

        st.write("### 📈 Info")
        st.write("Jumlah sampel:", df_final.shape[0])
        st.write("Jumlah parameter:", len(selected_cols))

        return df_final

    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None


# ===============================
# 🚀 RUN
# ===============================
df_filtered = load_filtered(uploaded_file)

if df_filtered is None:
    st.info("📭 Upload file untuk memulai")
