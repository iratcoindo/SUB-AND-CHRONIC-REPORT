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

def load_data(file, label):
    if file is None:
        return None
    
    # ===============================
    # LOAD FILE
    # ===============================
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
    # PARAMETER LIST
    # ===============================
    hematology_params = [
        "WBC (10^9/L)", "Neu # (10^9/L)", "Lym # (10^9/L)", 
        "Mon # (10^9/L)", "Eos # (10^9/L)", "Bas # (10^9/L)", 
        "Neu % ( )", "Lym % ( )", "Mon % ( )", "Eos % ( )", 
        "Bas % ( )", "RBC (10^12/L)", "HGB (g/L)", "HCT ( )", 
        "MCV (fL)", "MCH (pg)", "MCHC (g/L)", "RDW-CV ( )", 
        "RDW-SD (fL)", "PLT (10^9/L)", "MPV (fL)", "PDW ( )", 
        "PCT (mL/L)"
    ]

    # ===============================
    # CLEAN PARAMETER
    # ===============================
    df.iloc[:,0] = df.iloc[:,0].astype(str).str.strip()

    # ===============================
    # FILTER
    # ===============================
    df_filtered = df[df[df.columns[0]].isin(hematology_params)]

    if df_filtered.empty:
        return None

    # ===============================
    # MELT (LONG FORMAT)
    # ===============================
    df_long = df_filtered.melt(
        id_vars=df_filtered.columns[0],
        var_name="Sample",
        value_name="Value"
    )

    df_long.columns = ["Parameter","Sample","Value"]
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    df_long["Timepoint"] = label

    # ===============================
    # STRUCTURE PREVIEW
    # ===============================
    st.markdown(f"### 🧬 Structured Data ({label})")
    st.dataframe(df_long.head())

    return df_long

