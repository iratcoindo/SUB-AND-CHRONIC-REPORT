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

    st.markdown(f"### 📄 Raw Data Preview ({label})")
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

    st.write(f"🔍 Unique parameter ({label}):")
    st.write(df.iloc[:,0].unique())

    # ===============================
    # FILTER
    # ===============================
    df = df[df[df.columns[0]].isin(hematology_params)]

    if df.empty:
        st.error(f"❌ Data kosong setelah filter ({label})")
        return None

    # ===============================
    # MELT (LONG FORMAT)
    # ===============================
    df_long = df.melt(
        id_vars=df.columns[0],
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

    st.write(f"📊 Jumlah parameter: {df_long['Parameter'].nunique()}")
    st.write(f"🧪 Jumlah sample: {df_long['Sample'].nunique()}")

    return df_long

# ===============================
# 🔁 REUSABLE ANALYSIS FUNCTION
# ===============================
def run_analysis(df_all, title="Main Study"):

    if df_all is None or len(df_all) == 0:
        st.info(f"Tidak ada data {title}")
        return

    st.markdown("---")
    st.header(f"🧬 {title}")

    # ===============================
    # GROUP MAPPING
    # ===============================
    unique_samples = sorted(df_all["Sample"].unique())

    def parse_range(text):
        samples = []
        parts = text.split(",")
        for p in parts:
            p = p.strip()
            if "-" in p:
                a, b = p.split("-")
                samples += [str(i) for i in range(int(a), int(b)+1)]
            elif p != "":
                samples.append(p)
        return samples

    n_group = st.number_input(f"Jumlah kelompok ({title})", 1, 10, 2, key=title)

    group_map = {}

    for i in range(n_group):
        col1, col2 = st.columns(2)

        gname = col1.text_input(f"Nama Group {i+1}", f"Group {i+1}", key=f"{title}_g{i}")
        grange = col2.text_input("Range Sample", key=f"{title}_r{i}")

        try:
            parsed = parse_range(grange)
            for p in parsed:
                for s in unique_samples:
                    if s.endswith(str(p)):
                        group_map[s] = gname
        except:
            st.warning("Format salah")

    df_all["Group"] = df_all["Sample"].map(group_map)

    st.subheader("📋 Mapping")
    st.dataframe(df_all[["Sample","Group"]].drop_duplicates())

    # ===============================
    # 📏 AUTO REFERENCE RANGE (FROM GROUP)
    # ===============================
    st.subheader("📏 Auto Reference Range (From Group)")
    
    # pilih reference group
    groups_available = df_all["Group"].dropna().unique()
    
    if len(groups_available) == 0:
        st.warning("Belum ada group mapping")
        return
    
    ref_group = st.selectbox("Pilih Reference Group", groups_available, key=f"{title}_ref")
    
    parameters = df_all["Parameter"].unique()
    range_dict = {}
    
    range_preview = []
    
    for param in parameters:
    
        df_param = df_all[
            (df_all["Parameter"] == param) &
            (df_all["Group"] == ref_group)
        ]
    
        vals = df_param["Value"].dropna()
    
        if len(vals) > 0:
            low = vals.min()
            high = vals.max()
        else:
            low, high = None, None
    
        range_dict[param] = (low, high)
    
        range_preview.append({
            "Parameter": param,
            "Min": low,
            "Max": high
        })
    
    # tampilkan
    st.dataframe(pd.DataFrame(range_preview))

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
# LOAD MAIN
# ===============================
df_list = []

df_interim = load_data(interim_file, "Interim")
df_final   = load_data(final_file, "Final")

for d in [df_interim, df_final]:
    if d is not None:
        df_list.append(d)

df_main = pd.concat(df_list, ignore_index=True) if len(df_list)>0 else None

# ===============================
# LOAD SATELLITE
# ===============================
df_sat = load_data(sat_file, "Satellite")

# ===============================
# RUN
# ===============================
run_analysis(df_main, "Main Study")
run_analysis(df_sat, "Satellite Study")
