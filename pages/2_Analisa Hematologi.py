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

# ===============================
# 🚀 LOAD ALL SHEETS
# ===============================
df_interim = None
df_final = None
df_sat = None

if uploaded_file is not None:

    try:

        sheets = pd.read_excel(
            uploaded_file,
            sheet_name=None,
            engine="openpyxl"
        )

        # ===============================
        # INTERIM
        # ===============================
        if "Interim" in sheets:
            df_interim = load_data_df(
                sheets["Interim"],
                "Interim"
            )

        # ===============================
        # FINAL
        # ===============================
        if "Final" in sheets:
            df_final = load_data_df(
                sheets["Final"],
                "Final"
            )

        # ===============================
        # SATELLITE
        # ===============================
        if "Satellite" in sheets:
            df_sat = load_data_df(
                sheets["Satellite"],
                "Satellite"
            )

    except Exception as e:
        st.error(f"❌ Error membaca Excel: {e}")

# ===============================
# 🔗 COMBINE
# ===============================
dfs = [d for d in [df_interim, df_final, df_sat] if d is not None]

if len(dfs) > 0:

    df_all = pd.concat(
        dfs,
        ignore_index=True
    )

    st.markdown("---")

else:
    st.info("📭 Upload minimal satu sheet")

# ===============================
# 🧬 GROUPING MAIN
# ===============================
st.markdown("---")

st.header("🧬 Group Assignment (Main Study)")

group_names_main = st.text_input(
    "Main Group (Interim + Final)",
    placeholder="Control, Dose1, Dose2"
)

replicate_main = st.number_input(
    "Ulangan per group (Main)",
    min_value=1,
    value=6
)

# pilih source
df_main_source = None

if df_interim is not None:
    df_main_source = df_interim.copy()

elif df_final is not None:
    df_main_source = df_final.copy()

if group_names_main and df_main_source is not None:

    groups = [
        g.strip()
        for g in group_names_main.split(",")
        if g.strip()
    ]

    labels = []

    for g in groups:
        labels += [g] * replicate_main

    samples = df_main_source["Sample ID"].tolist()

    if len(labels) != len(samples):

        st.warning(
            "⚠️ Jumlah data tidak cocok dengan grouping (Main)"
        )

    else:

        df_main_source["Group"] = labels

        st.success("✅ Main grouping berhasil")

        # mapping
        group_map = dict(
            zip(
                df_main_source["Sample ID"],
                df_main_source["Group"]
            )
        )

        if df_interim is not None:
            df_interim["Group"] = df_interim["Sample ID"].map(group_map)

        if df_final is not None:
            df_final["Group"] = df_final["Sample ID"].map(group_map)

        # tampilkan
        st.subheader("📋 Main Mapping")

        st.dataframe(
            df_main_source[["Sample ID", "Group"]],
            height=400
        )

        # combine main
        df_main = pd.concat(
            [
                d for d in [df_interim, df_final]
                if d is not None
            ],
            ignore_index=True
        )

        st.subheader("📊 Main Data (with Group)")

        st.dataframe(
            df_main,
            use_container_width=True,
            height=500
        )

# ===============================
# 🛰️ GROUPING SATELLITE
# ===============================
st.markdown("---")

st.header("🛰️ Group Assignment (Satellite)")

group_names_sat = st.text_input(
    "Satellite Group",
    placeholder="Control, Recovery"
)

replicate_sat = st.number_input(
    "Ulangan per group (Satellite)",
    min_value=1,
    value=5
)

if df_sat is not None and group_names_sat:

    groups = [
        g.strip()
        for g in group_names_sat.split(",")
        if g.strip()
    ]

    labels = []

    for g in groups:
        labels += [g] * replicate_sat

    samples = df_sat["Sample ID"].tolist()

    if len(labels) != len(samples):

        st.warning(
            "⚠️ Jumlah data tidak cocok dengan grouping (Satellite)"
        )

    else:

        df_sat["Group"] = labels

        st.success("✅ Satellite grouping berhasil")

        st.subheader("📋 Satellite Mapping")

        st.dataframe(
            df_sat[["Sample ID", "Group"]],
            height=400
        )

        st.subheader("📊 Satellite Data (with Group)")

        st.dataframe(
            df_sat,
            use_container_width=True,
            height=500
        )

# ===============================
# 📊 BOXPLOT + STATISTIK
# ===============================
st.markdown("---")

st.header("📊 Boxplot & Statistik")

param = st.selectbox(
    "Pilih parameter",
    TARGET_COLS
)

# ===============================
# FUNCTION PLOT + STATS
# ===============================
def plot_box_and_stats(df, title):

    if df is None or "Group" not in df.columns:
        st.info(f"{title} belum siap")
        return

    st.subheader(title)

    # ===============================
    # BOXPLOT
    # ===============================
    fig, ax = plt.subplots()

    groups = sorted(
        df["Group"].dropna().unique()
    )

    data = [
        df[df["Group"] == g][param].dropna()
        for g in groups
    ]

    ax.boxplot(
        data,
        labels=groups
    )

    ax.set_title(f"{param} - {title}")
    ax.set_ylabel(param)

    st.pyplot(fig)

    # ===============================
    # MEAN ± SD
    # ===============================
    summary = df.groupby("Group")[param].agg(
        ["mean","std","count"]
    )

    st.write("### Mean ± SD")

    st.dataframe(summary)

    # ===============================
    # ANOVA
    # ===============================
    if len(data) > 1:

        f_val, p_val = stats.f_oneway(*data)

        st.write("### ANOVA")

        st.write(f"F-value: {f_val:.3f}")
        st.write(f"p-value: {p_val:.5f}")

        if p_val < 0.05:
            st.warning("⚠️ Signifikan (p < 0.05)")
        else:
            st.success("✅ Tidak signifikan")

# ===============================
# 📊 INTERIM
# ===============================
plot_box_and_stats(
    df_interim,
    "Interim"
)

# ===============================
# 📊 FINAL
# ===============================
plot_box_and_stats(
    df_final,
    "Final"
)

# ===============================
# 📊 SATELLITE
# ===============================
plot_box_and_stats(
    df_sat,
    "Satellite"
)
