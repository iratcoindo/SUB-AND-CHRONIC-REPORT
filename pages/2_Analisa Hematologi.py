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

        # DEBUG COLUMN
        st.write(f"📋 Detected Columns ({label})")
        st.write(df.columns.tolist())

        # ===============================
        # DETECT SAMPLE ID
        # ===============================
        possible_ids = [
            "Sample ID",
            "Sample",
            "ID",
            "Patient ID",
            "Animal ID",
            "No"
        ]

        sample_col = None

        for c in df.columns:

            for p in possible_ids:

                if str(c).strip().lower() == p.lower():

                    sample_col = c
                    break

            if sample_col is not None:
                break

        # fallback
        if sample_col is None:

            df["Sample ID"] = df.index.astype(str)
            sample_col = "Sample ID"

        # ===============================
        # MATCH TARGET COLS
        # ===============================
        selected_cols = []

        for t in TARGET_COLS:

            found = False

            for c in df.columns:

                c_clean = str(c).strip()

                # exact match
                if c_clean == t:

                    selected_cols.append(c)
                    found = True
                    break

                # partial match
                elif c_clean.startswith(t):

                    selected_cols.append(c)
                    found = True
                    break

            if not found:
                st.warning(f"Kolom tidak ditemukan: {t}")

        # ===============================
        # VALIDASI
        # ===============================
        if len(selected_cols) == 0:

            st.error(
                f"❌ Tidak ada kolom hematologi ditemukan di {label}"
            )

            return None

        # ===============================
        # FILTER DATA
        # ===============================
        df_filtered = df[
            [sample_col] + selected_cols
        ].copy()

        # rename sample id
        df_filtered = df_filtered.rename(
            columns={
                sample_col: "Sample ID"
            }
        )

        # ===============================
        # TAMBAH NO
        # ===============================
        df_filtered.insert(
            0,
            "No",
            range(1, len(df_filtered) + 1)
        )

        # ===============================
        # CONVERT NUMERIC
        # ===============================
        for c in selected_cols:

            df_filtered[c] = pd.to_numeric(
                df_filtered[c],
                errors="coerce"
            )

        # ===============================
        # URUTAN KOLOM
        # ===============================
        ordered_cols = [
            "No",
            "Sample ID"
        ] + selected_cols

        df_filtered = df_filtered[
            ordered_cols
        ]

        # ===============================
        # LABEL
        # ===============================
        df_filtered["Source"] = label

        # ===============================
        # OUTPUT
        # ===============================
        st.markdown(
            f"## 🧬 Filtered Hematology ({label})"
        )

        st.dataframe(
            df_filtered,
            use_container_width=True,
            height=500
        )

        st.success(
            f"✅ {label}: {df_filtered.shape[0]} rows loaded"
        )

        return df_filtered

    except Exception as e:

        st.error(
            f"❌ Error loading {label}: {e}"
        )

        return None

# ===============================
# 🚀 LOAD ALL SHEETS
# ===============================
all_dfs = []

df_interim = None
df_final = None
df_sat = None

if uploaded_file is not None:

    try:

        # ===============================
        # READ EXCEL
        # ===============================
        sheets = pd.read_excel(
            uploaded_file,
            sheet_name=None,
            engine="openpyxl",
            header=0
        )

        st.write("📑 Detected Sheets:")
        st.write(list(sheets.keys()))

        # ===============================
        # PROCESS ALL SHEETS
        # ===============================
        for sheet_name, sheet_df in sheets.items():

            df_temp = load_data_df(
                sheet_df,
                sheet_name
            )

            if df_temp is not None:

                all_dfs.append(df_temp)

                # mapping
                if sheet_name.lower() == "interim":
                    df_interim = df_temp

                elif sheet_name.lower() == "final":
                    df_final = df_temp

                elif sheet_name.lower() == "satellite":
                    df_sat = df_temp

        # ===============================
        # COMBINE
        # ===============================
        if len(all_dfs) > 0:

            df_all = pd.concat(
                all_dfs,
                ignore_index=True
            )

            st.markdown("---")

            st.subheader("📊 Combined Data")

            st.dataframe(
                df_all,
                use_container_width=True,
                height=600
            )

            st.success(
                f"✅ Total loaded rows: {len(df_all)}"
            )

        else:

            st.warning(
                "⚠️ Tidak ada data hematologi yang berhasil dibaca"
            )

    except Exception as e:

        st.error(f"❌ Error membaca Excel: {e}")

# ===============================
# GROUPING MAIN
# ===============================
st.markdown("---")

st.header("🧬 Group Assignment (Main Study)")

group_names_main = st.text_input(
    "Main Group (Interim + Final)",
    placeholder="Control,Dose1,Dose2"
)

replicate_main = st.number_input(
    "Ulangan per group (Main)",
    min_value=1,
    value=6
)

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
            "⚠️ Jumlah data tidak cocok dengan grouping"
        )

    else:

        df_main_source["Group"] = labels

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

        st.success("✅ Grouping berhasil")

# ===============================
# BOXPLOT
# ===============================
st.markdown("---")

st.header("📊 Boxplot & Statistik")

param = st.selectbox(
    "Pilih Parameter",
    TARGET_COLS
)

def plot_box_and_stats(df, title):

    if df is None:
        return

    if "Group" not in df.columns:
        return

    st.subheader(title)

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

    st.pyplot(fig)

    # mean sd
    summary = df.groupby("Group")[param].agg(
        ["mean","std","count"]
    )

    st.dataframe(summary)

    # anova
    if len(data) > 1:

        f_val, p_val = stats.f_oneway(*data)

        st.write(f"F-value: {f_val:.3f}")
        st.write(f"p-value: {p_val:.5f}")

        if p_val < 0.05:
            st.warning("⚠️ Signifikan")
        else:
            st.success("✅ Tidak signifikan")

# ===============================
# SHOW PLOT
# ===============================
plot_box_and_stats(df_interim, "Interim")
plot_box_and_stats(df_final, "Final")
plot_box_and_stats(df_sat, "Satellite")
