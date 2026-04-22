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
    # GROUP INPUT MANUAL
    # ===============================
    st.subheader("🧬 Group & Repetition Setup")

    samples = sorted(df_all["Sample"].unique())

    n_group = st.number_input("Jumlah Group", 1, 10, 2, key=f"{title}_ng")

    group_map = {}
    rep_map = {}

    for i in range(n_group):

        st.markdown(f"### Group {i+1}")

        col1, col2 = st.columns(2)

        gname = col1.text_input("Nama Group", f"Group {i+1}", key=f"{title}_g{i}")
        reps  = col2.number_input("Jumlah Repetisi", 1, 100, 5, key=f"{title}_r{i}")

        s_input = st.text_input(
            "Isi Sample (contoh: 1,2,3 atau S1,S2)",
            key=f"{title}_s{i}"
        )

        if s_input:
            items = [x.strip() for x in s_input.split(",")]

            for s in samples:
                for item in items:
                    if str(s).endswith(item):
                        group_map[s] = gname
                        rep_map[s] = reps

    df_all["Group"] = df_all["Sample"].map(group_map)
    df_all["Repetition"] = df_all["Sample"].map(rep_map)

    st.subheader("📋 Mapping")
    st.dataframe(df_all[["Sample","Group","Repetition"]].drop_duplicates())

    # ===============================
    # AUTO REFERENCE RANGE
    # ===============================
    st.subheader("📏 Auto Reference Range")

    groups = df_all["Group"].dropna().unique()

    if len(groups) == 0:
        st.warning("Isi group dulu")
        return

    ref_group = st.selectbox("Reference Group", groups, key=f"{title}_ref")

    parameters = df_all["Parameter"].unique()
    range_dict = {}

    results_range = []

    for param in parameters:

        vals = df_all[
            (df_all["Parameter"] == param) &
            (df_all["Group"] == ref_group)
        ]["Value"].dropna()

        if len(vals) > 0:
            low = vals.min()
            high = vals.max()
        else:
            low, high = None, None

        range_dict[param] = (low, high)

        results_range.append({
            "Parameter": param,
            "Min": low,
            "Max": high
        })

    st.dataframe(pd.DataFrame(results_range))

    # ===============================
    # OUT OF RANGE
    # ===============================
    st.subheader("🚨 Out of Range")

    results = []

    for param in parameters:

        low, high = range_dict.get(param, (None,None))
        if low is None:
            continue

        df_param = df_all[df_all["Parameter"] == param]

        for (g,tp), df_sub in df_param.groupby(["Group","Timepoint"]):

            vals = df_sub["Value"].dropna()
            if len(vals) == 0:
                continue

            below = (vals < low).sum()
            above = (vals > high).sum()

            results.append({
                "Parameter":param,
                "Group":g,
                "Timepoint":tp,
                "n":len(vals),
                "Out":below+above
            })

    if results:
        st.dataframe(pd.DataFrame(results))

    # ===============================
    # BOXPLOT
    # ===============================
    st.subheader("📦 Boxplot")

    groups = df_all["Group"].dropna().unique()

    for param in parameters:

        df_param = df_all[df_all["Parameter"] == param]

        data = []
        labels = []

        for g in groups:
            for tp in df_param["Timepoint"].unique():

                vals = df_param[
                    (df_param["Group"]==g) &
                    (df_param["Timepoint"]==tp)
                ]["Value"].dropna()

                if len(vals)>0:
                    data.append(vals)
                    labels.append(f"{g}-{tp}")

        if len(data)>0:
            fig, ax = plt.subplots()
            ax.boxplot(data)
            ax.set_xticklabels(labels, rotation=90)
            ax.set_title(param)
            st.pyplot(fig)


# ===============================
# LOAD DATA
# ===============================
df_list = []

df_interim = load_data(interim_file, "Interim")
df_final   = load_data(final_file, "Final")

for d in [df_interim, df_final]:
    if d is not None:
        df_list.append(d)

df_main = pd.concat(df_list, ignore_index=True) if len(df_list)>0 else None

df_sat = load_data(sat_file, "Satellite")

# ===============================
# RUN
# ===============================
run_analysis(df_main, "Main Study")
run_analysis(df_sat, "Satellite Study")
