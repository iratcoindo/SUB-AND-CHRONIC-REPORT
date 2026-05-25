import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(layout="wide")

st.title("📊 Hematology Analyzer (Raw Filter Mode)")

# ===============================
# 📥 UPLOAD
# ===============================
st.subheader("📥 Upload Excel File")

uploaded_file = st.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

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
# LOAD FUNCTION
# ===============================
def load_data_df(df, label):

    try:

        # ===============================
        # CLEAN COLUMN NAME
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

        # fallback
        if sample_col is None:
            df["Sample ID"] = df.index.astype(str)
            sample_col = "Sample ID"

        # ===============================
        # MATCH TARGET COLS
        # ===============================
        col_map = {c.strip(): c for c in df.columns}

        selected_cols = []

        for t in TARGET_COLS:
            if t in col_map:
                selected_cols.append(col_map[t])

        if len(selected_cols) == 0:
            st.error(f"❌ Tidak ada kolom hematologi ditemukan di {label}")
            return None

        # ===============================
        # FILTER
        # ===============================
        df_filtered = df[[sample_col] + selected_cols].copy()

        df_filtered = df_filtered.rename(
            columns={sample_col: "Sample ID"}
        )

        # numeric convert
        for c in selected_cols:
            df_filtered[c] = pd.to_numeric(
                df_filtered[c],
                errors="coerce"
            )

        # label
        df_filtered["Source"] = label

        # ===============================
        # OUTPUT
        # ===============================
        st.markdown(f"### 🧬 Filtered Hematology ({label})")

        st.dataframe(
            df_filtered,
            use_container_width=True
        )

        st.success(f"{label}: {df_filtered.shape[0]} rows loaded")

        return df_filtered

    except Exception as e:
        st.error(f"❌ Error loading {label}: {e}")
        return None

