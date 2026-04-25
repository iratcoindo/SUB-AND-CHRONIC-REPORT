import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Hematology Analyzer (Raw Filter Mode)")

# ===============================
# 📥 UPLOAD
# ===============================
st.subheader("📥 Upload Data")

col1, col2 = st.columns(2)
interim_file = col1.file_uploader("Interim", type=["xlsx","csv"])
final_file   = col2.file_uploader("Final", type=["xlsx","csv"])

sat_file = st.file_uploader("Satellite", type=["xlsx","csv"])

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

def load_data(file, label):
    if file is None:
        return None

    try:
        # LOAD
        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            df = pd.read_csv(file)

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

        # fallback kalau tidak ada
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
            st.error(f"❌ Tidak ada kolom hematologi ditemukan di {label}")
            return None

        # ===============================
        # FILTER + SUSUN KOLOM
        # ===============================
        df_filtered = df[[sample_col] + selected_cols].copy()
        df_filtered = df_filtered.rename(columns={sample_col: "Sample ID"})

        # convert numeric
        for c in selected_cols:
            df_filtered[c] = pd.to_numeric(df_filtered[c], errors="coerce")

        # tambahkan label
        df_filtered["Source"] = label

        # ===============================
        # OUTPUT (HANYA FILTERED)
        # ===============================
        st.markdown(f"### 🧬 Filtered Hematology ({label})")
        st.dataframe(df_filtered.head())

        st.success(f"{label}: {df_filtered.shape[0]} rows loaded")

        return df_filtered

    except Exception as e:
        st.error(f"❌ Error loading {label}: {e}")
        return None
    
# ===============================
# 🚀 LOAD ALL
# ===============================
df_interim = load_data(interim_file, "Interim") if interim_file else None
df_final   = load_data(final_file, "Final") if final_file else None
df_sat     = load_data(sat_file, "Satellite") if sat_file else None

# ===============================
# 🔗 COMBINE
# ===============================
dfs = [d for d in [df_interim, df_final, df_sat] if d is not None]

if len(dfs) > 0:
    df_all = pd.concat(dfs, ignore_index=True)

    st.markdown("---")
    st.header("📊 Combined Data (Filtered)")

    st.dataframe(df_all.head())

    st.write("### 📈 Info")
    st.write("Total rows:", df_all.shape[0])
    st.write("Columns:", list(df_all.columns))

else:
    st.info("📭 Upload minimal satu file")
