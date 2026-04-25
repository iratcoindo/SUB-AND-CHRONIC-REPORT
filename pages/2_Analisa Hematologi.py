import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Hematology Analyzer (Main + Satellite)")

# ===============================
# 📥 UPLOAD
# ===============================
st.subheader("📥 Upload Data")

col1, col2 = st.columns(2)
interim_file = col1.file_uploader("Interim", type=["xlsx","csv"])
final_file   = col2.file_uploader("Final", type=["xlsx","csv"])

sat_file = st.file_uploader("Satellite", type=["xlsx","csv"])

# ===============================
# 📦 FUNCTION LOAD
# ===============================
def load_data(file, label):
    if file is None:
        return None
    
    try:
        # ===============================
        # LOAD
        # ===============================
        if file.name.endswith(".xlsx"):
            df = pd.read_excel(file, engine="openpyxl")
        else:
            df = pd.read_csv(file)

        st.markdown(f"### 📄 Raw Data ({label})")
        st.dataframe(df.head())

        # ===============================
        # CLEAN COLUMN
        # ===============================
        df.columns = df.columns.astype(str).str.strip()

        # ===============================
        # DETECT SAMPLE COLUMN
        # ===============================
        possible_sample_cols = ["Sample ID", "Sample", "ID", "Patient ID"]
        
        sample_col = None
        for c in possible_sample_cols:
            if c in df.columns:
                sample_col = c
                break

        if sample_col is None:
            df["Sample"] = df.index.astype(str)
            sample_col = "Sample"

        # ===============================
        # PARAMETER COLUMNS
        # ===============================
        param_cols = [c for c in df.columns if c != sample_col]

        # ===============================
        # MELT → LONG FORMAT
        # ===============================
        df_long = df.melt(
            id_vars=[sample_col],
            value_vars=param_cols,
            var_name="Parameter",
            value_name="Value"
        )

        df_long = df_long.rename(columns={sample_col: "Sample"})
        df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
        df_long["Timepoint"] = label

        # ===============================
        # OUTPUT
        # ===============================
        st.markdown(f"### 🧬 Structured Data ({label})")
        st.dataframe(df_long.head())

        st.success(f"{label}: {df_long.shape[0]} rows ready")

        return df_long

    except Exception as e:
        st.error(f"❌ Error loading {label}: {e}")
        return None


# ===============================
# 🚀 LOAD ALL (SAFE)
# ===============================
df_interim = load_data(interim_file, "Interim") if interim_file else None
df_final   = load_data(final_file, "Final") if final_file else None
df_sat     = load_data(sat_file, "Satellite") if sat_file else None

# ===============================
# 🔗 COMBINE DATA
# ===============================
dfs = [df for df in [df_interim, df_final, df_sat] if df is not None]

if len(dfs) > 0:

    df_all = pd.concat(dfs, ignore_index=True)

    st.markdown("---")
    st.header("📊 Combined Data (Siap Analisa)")

    st.dataframe(df_all.head())

    st.write("### 📈 Summary")
    st.write("Total rows:", df_all.shape[0])
    st.write("Total samples:", df_all["Sample"].nunique())
    st.write("Parameters:", df_all["Parameter"].nunique())
    st.write("Timepoints:", df_all["Timepoint"].unique())

else:
    st.info("📭 Silakan upload minimal 1 file untuk memulai")
