import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout="wide")
st.title("📊 Hematology Analyzer (Main + Satellite)")

# ===============================
# 📥 UPLOAD MAIN DATA
# ===============================
st.subheader("📥 Main Study Data")

col1, col2 = st.columns(2)
interim_file = col1.file_uploader("Interim", type=["xlsx","csv"])
final_file   = col2.file_uploader("Final", type=["xlsx","csv"])

# ===============================
# 📥 SATELLITE DATA
# ===============================
st.markdown("---")
st.subheader("🛰️ Satellite Data (Separate)")

sat_file = st.file_uploader("Satellite Upload", type=["xlsx","csv"])

df_interim = load_data(interim_file, "Interim") if interim_file else None
df_final   = load_data(final_file, "Final") if final_file else None
df_sat     = load_data(sat_file, "Satellite") if sat_file else None

# ===============================
# FUNCTION LOAD (FIXED - HORIZONTAL FORMAT)
# ===============================
def load_data(file, label):
    if file is None:
        return None
    
    # LOAD FILE
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file, engine="openpyxl")
    else:
        df = pd.read_csv(file)

    # ===============================
    # PREVIEW RAW
    # ===============================
    st.markdown(f"### 📄 Raw Data ({label})")
    st.dataframe(df.head())

    # ===============================
    # DETECT KOLOM
    # ===============================
    df.columns = df.columns.astype(str).str.strip()

    # kolom metadata (kalau ada)
    meta_cols = ["Sample ID", "Sample", "ID", "Patient ID", "Patient"]
    meta_cols_exist = [c for c in meta_cols if c in df.columns]

    # pastikan ada kolom sample
    if "Sample ID" in df.columns:
        sample_col = "Sample ID"
    elif "Sample" in df.columns:
        sample_col = "Sample"
    else:
        # fallback: pakai index
        df["Sample"] = df.index.astype(str)
        sample_col = "Sample"

    # parameter = semua kolom selain metadata
    param_cols = [c for c in df.columns if c not in meta_cols_exist]

    # buang kolom sample dari parameter
    if sample_col in param_cols:
        param_cols.remove(sample_col)

    # ===============================
    # MELT
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
    # PREVIEW STRUCTURE
    # ===============================
    st.markdown(f"### 🧬 Structured Data ({label})")
    st.dataframe(df_long.head())

    st.caption(f"{label}: {df_long.shape[0]} rows loaded")

    return df_long


# ===============================
# ANALYSIS FUNCTION
# ===============================
def run_analysis(df_all, title="Study"):

    if df_all is None or len(df_all) == 0:
        st.info(f"Tidak ada data {title}")
        return

    st.markdown("---")
    st.header(f"🧬 {title}")

    # ===============================
    # 🧬 GROUP INPUT (SIMPLE MODEL)
    # ===============================
    st.subheader("🧬 Group Setup")
    
    group_names = st.text_input(
        "Group names (pisahkan koma)",
        placeholder="Control, Dose1, Dose2",
        key=f"{title}_groups"
    )
    
    rows_per_group = st.number_input(
        "Rows per group",
        value=6,
        min_value=1,
        key=f"{title}_rows"
    )
    
    if group_names:
    
        groups = [g.strip() for g in group_names.split(",") if g.strip()]
    
        labels = []
        for g in groups:
            labels += [g] * rows_per_group
    
        # ===============================
        # VALIDASI
        # ===============================
        if len(labels) != df_all["Sample"].nunique():
            st.warning(
                f"⚠️ Jumlah data ({df_all['Sample'].nunique()}) "
                f"tidak cocok dengan group ({len(labels)})"
            )
        else:
            # mapping berdasarkan urutan sample
            sample_order = sorted(df_all["Sample"].unique())
    
            group_map = dict(zip(sample_order, labels))
    
            df_all["Group"] = df_all["Sample"].map(group_map)
    
            st.success("✅ Group berhasil di-assign")
    
            st.subheader("📋 Group Mapping")
            st.dataframe(df_all[["Sample","Group"]].drop_duplicates())

    
