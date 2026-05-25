import streamlit as st
import pandas as pd

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(layout="wide")

st.title("📊 Hematology Data Filter")

# ===============================
# UPLOAD
# ===============================
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# ===============================
# TARGET PARAMETER
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
def process_sheet(df):

    # ===============================
    # CLEAN COLUMN
    # ===============================
    df.columns = df.columns.astype(str).str.strip()

    # ===============================
    # SAMPLE ID DETECTION
    # ===============================
    possible_ids = [
        "Sample ID",
        "Sample",
        "ID",
        "Patient ID",
        "Animal ID"
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
    # FIND TARGET COLUMN
    # ===============================
    selected_cols = []

    for t in TARGET_COLS:

        for c in df.columns:

            c_clean = str(c).strip()

            # exact
            if c_clean == t:

                selected_cols.append(c)
                break

            # partial
            elif c_clean.startswith(t):

                selected_cols.append(c)
                break

    # ===============================
    # VALIDATION
    # ===============================
    if len(selected_cols) == 0:

        st.error("Tidak ada parameter hematologi ditemukan")

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
    # ADD NUMBER
    # ===============================
    df_filtered.insert(
        0,
        "No",
        range(1, len(df_filtered)+1)
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
    # ORDER COLUMN
    # ===============================
    ordered_cols = [
        "No",
        "Sample ID"
    ] + selected_cols

    df_filtered = df_filtered[
        ordered_cols
    ]

    return df_filtered

# ===============================
# PROCESS EXCEL
# ===============================
if uploaded_file is not None:

    try:

        # ===============================
        # READ ALL SHEETS
        # ===============================
        sheets = pd.read_excel(
            uploaded_file,
            sheet_name=None,
            engine="openpyxl"
        )

        all_data = []

        # ===============================
        # PROCESS EACH SHEET
        # ===============================
        for sheet_name, sheet_df in sheets.items():

            df_result = process_sheet(sheet_df)

            if df_result is not None:

                all_data.append(df_result)

        # ===============================
        # COMBINE ALL
        # ===============================
        if len(all_data) > 0:

            final_df = pd.concat(
                all_data,
                ignore_index=True
            )

            st.success(
                f"Loaded {len(final_df)} rows"
            )

            st.dataframe(
                final_df,
                use_container_width=True,
                height=700
            )

        else:

            st.warning(
                "Tidak ada data hematologi ditemukan"
            )

    except Exception as e:

        st.error(f"Error membaca file: {e}")
