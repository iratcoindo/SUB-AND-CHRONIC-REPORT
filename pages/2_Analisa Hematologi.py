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
        # ===============================
        # GROUP ASSIGNMENT
        # ===============================
        st.markdown("---")
        st.header("🧬 Group Assignment")
        
        # ===============================
        # SEX INPUT
        # ===============================
        st.subheader("Sex Assignment")
        
        male_input = st.text_input(
            "Nomor Jantan",
            placeholder="1,2,3,4"
        )
        
        female_input = st.text_input(
            "Nomor Betina",
            placeholder="5,6,7,8"
        )
        
        # default sex
        final_df["Sex"] = ""
        
        # assign male
        if male_input:
        
            male_numbers = [
                int(x.strip())
                for x in male_input.split(",")
                if x.strip().isdigit()
            ]
        
            final_df.loc[
                final_df["No"].isin(male_numbers),
                "Sex"
            ] = "Male"
        
        # assign female
        if female_input:
        
            female_numbers = [
                int(x.strip())
                for x in female_input.split(",")
                if x.strip().isdigit()
            ]
        
            final_df.loc[
                final_df["No"].isin(female_numbers),
                "Sex"
            ] = "Female"
        
        # ===============================
        # GROUP INPUT
        # ===============================
        st.subheader("Group Assignment")
        
        n_groups = st.number_input(
            "Jumlah Kelompok",
            min_value=1,
            value=2
        )
        
        group_data = {}
        
        for i in range(n_groups):
        
            col1, col2 = st.columns(2)
        
            with col1:
        
                group_name = st.text_input(
                    f"Nama Kelompok {i+1}",
                    key=f"group_name_{i}"
                )
        
            with col2:
        
                group_numbers = st.text_input(
                    f"Nomor Kelompok {i+1}",
                    placeholder="1,2,3",
                    key=f"group_number_{i}"
                )
        
            group_data[group_name] = group_numbers
        
        # ===============================
        # ASSIGN GROUP
        # ===============================
        final_df["Group"] = ""
        
        for group_name, number_text in group_data.items():
        
            if group_name.strip() == "":
                continue
        
            numbers = [
                int(x.strip())
                for x in number_text.split(",")
                if x.strip().isdigit()
            ]
        
            final_df.loc[
                final_df["No"].isin(numbers),
                "Group"
            ] = group_name
        
        # ===============================
        # OUTPUT TABLE
        # ===============================
        st.markdown("---")
        st.subheader("📋 Assigned Hematology Table")
        
        st.dataframe(
            final_df,
            use_container_width=True,
            height=800
        )

        else:

            st.warning(
                "Tidak ada data hematologi ditemukan"
            )

    except Exception as e:

        st.error(f"Error membaca file: {e}")
