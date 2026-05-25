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
            
            # copy dataframe
            assigned_df = final_df.copy()
            
            # ===============================
            # FUNCTION PARSE NUMBER
            # SUPPORT:
            # 1,2,3
            # 1-10
            # 1-10,21-30
            # ===============================
            def parse_numbers(text):
            
                numbers = []
            
                if text.strip() == "":
                    return numbers
            
                for item in text.split(","):
            
                    item = item.strip()
            
                    # RANGE
                    if "-" in item:
            
                        try:
            
                            start, end = item.split("-")
            
                            start = int(start.strip())
                            end = int(end.strip())
            
                            numbers.extend(
                                range(start, end + 1)
                            )
            
                        except:
                            pass
            
                    # SINGLE NUMBER
                    else:
            
                        if item.isdigit():
            
                            numbers.append(int(item))
            
                return numbers
            
            # ===============================
            # SEX ASSIGNMENT
            # ===============================
            st.subheader("Sex Assignment")
            
            male_text = st.text_input(
                "Nomor Jantan",
                value="1-10, 21-30, 41-50, 61-70"
            )
            
            female_text = st.text_input(
                "Nomor Betina",
                value="11-20, 31-40, 51-60, 71-80"
            )
            
            # default
            assigned_df["Sex"] = ""
            
            # male
            male_numbers = parse_numbers(male_text)
            
            assigned_df.loc[
                assigned_df["No"].isin(male_numbers),
                "Sex"
            ] = "Male"
            
            # female
            female_numbers = parse_numbers(female_text)
            
            assigned_df.loc[
                assigned_df["No"].isin(female_numbers),
                "Sex"
            ] = "Female"
            
            # ===============================
            # GROUP ASSIGNMENT
            # ===============================
            st.subheader("Kelompok")
            
            n_group = st.number_input(
                "Jumlah Kelompok",
                min_value=1,
                value=2
            )
            
            assigned_df["Group"] = ""
            
            for i in range(int(n_group)):
            
                st.markdown(f"### Kelompok {i+1}")
            
                group_name = st.text_input(
                    f"Nama Kelompok {i+1}",
                    key=f"group_name_{i}"
                )
            
                group_numbers = st.text_input(
                    f"Nomor Hewan {i+1}",
                    placeholder="1-10, 21-30",
                    key=f"group_numbers_{i}"
                )
            
                # parse number
                number_list = parse_numbers(group_numbers)
            
                # assign
                if group_name.strip() != "":
            
                    assigned_df.loc[
                        assigned_df["No"].isin(number_list),
                        "Group"
                    ] = group_name
            
            # ===============================
            # OUTPUT
            # ===============================
            st.markdown("---")
            st.subheader("📋 Assigned Table")
            
            st.dataframe(
                assigned_df,
                use_container_width=True,
                height=800
            )

            # ===============================
            # VISUALIZATION
            # ===============================
            import numpy as np
            import matplotlib.pyplot as plt
            from scipy import stats
            
            st.markdown("---")
            st.header("📊 Statistical Visualization")
            
            # ===============================
            # JCO COLOR PALETTE
            # ===============================
            JCO_COLORS = [
                "#0073C2FF",  # blue
                "#EFC000FF",  # yellow
                "#868686FF",  # gray
                "#CD534CFF",  # red
                "#7AA6DCFF",  # light blue
                "#003C67FF",  # navy
                "#8F7700FF",  # olive
            ]
            
            # ===============================
            # PARAMETER SELECT
            # ===============================
            param = st.selectbox(
                "Select Parameter",
                TARGET_COLS
            )
            
            # ===============================
            # PREPARE DATA
            # ===============================
            plot_df = assigned_df.copy()
            
            plot_df = plot_df.dropna(
                subset=[param, "Group", "Sex"]
            )
            
            # ===============================
            # FACET SEX
            # ===============================
            sexes = ["Male", "Female"]
            
            fig, axes = plt.subplots(
                1,
                2,
                figsize=(14,6),
                sharey=True
            )
            
            # ===============================
            # LOOP SEX
            # ===============================
            for ax, sex in zip(axes, sexes):
            
                df_sex = plot_df[
                    plot_df["Sex"] == sex
                ]
            
                if len(df_sex) == 0:
            
                    ax.set_title(f"{sex} (No Data)")
                    continue
            
                groups = sorted(
                    df_sex["Group"].dropna().unique()
                )
            
                # ===============================
                # DATA GROUP
                # ===============================
                data_groups = []
            
                for g in groups:
            
                    vals = df_sex[
                        df_sex["Group"] == g
                    ][param].dropna()
            
                    data_groups.append(vals)
            
                # ===============================
                # BOXPLOT
                # ===============================
                bp = ax.boxplot(
                    data_groups,
                    patch_artist=True,
                    widths=0.55,
                    showfliers=False
                )
            
                # ===============================
                # STYLE BOX
                # ===============================
                for i, box in enumerate(bp["boxes"]):
            
                    box.set(
                        facecolor=JCO_COLORS[i % len(JCO_COLORS)],
                        edgecolor="black",
                        linewidth=1.5,
                        alpha=0.35
                    )
            
                for whisker in bp["whiskers"]:
            
                    whisker.set(
                        color="black",
                        linewidth=1.2
                    )
            
                for cap in bp["caps"]:
            
                    cap.set(
                        color="black",
                        linewidth=1.2
                    )
            
                for median in bp["medians"]:
            
                    median.set(
                        color="black",
                        linewidth=2.2
                    )
            
                # ===============================
                # JITTER POINT
                # ===============================
                for i, vals in enumerate(data_groups):
            
                    x = np.random.normal(
                        i + 1,
                        0.045,
                        size=len(vals)
                    )
            
                    ax.scatter(
                        x,
                        vals,
                        color=JCO_COLORS[i % len(JCO_COLORS)],
                        edgecolors="black",
                        linewidths=0.6,
                        alpha=0.8,
                        s=42,
                        zorder=5
                    )
            
                # ===============================
                # MAIN TEST
                # ===============================
                p_main = None
                test_name = ""
            
                try:
            
                    normal = True
            
                    for vals in data_groups:
            
                        if len(vals) >= 3:
            
                            _, p_norm = stats.shapiro(vals)
            
                            if p_norm < 0.05:
                                normal = False
            
                    _, p_lev = stats.levene(*data_groups)
            
                    equal_var = p_lev >= 0.05
            
                    # ===============================
                    # PARAMETRIC
                    # ===============================
                    if normal and equal_var:
            
                        if len(groups) == 2:
            
                            _, p_main = stats.ttest_ind(
                                data_groups[0],
                                data_groups[1]
                            )
            
                            test_name = "T-test"
            
                        else:
            
                            _, p_main = stats.f_oneway(
                                *data_groups
                            )
            
                            test_name = "ANOVA"
            
                    # ===============================
                    # NON PARAMETRIC
                    # ===============================
                    else:
            
                        if len(groups) == 2:
            
                            _, p_main = stats.mannwhitneyu(
                                data_groups[0],
                                data_groups[1]
                            )
            
                            test_name = "Mann-Whitney"
            
                        else:
            
                            _, p_main = stats.kruskal(
                                *data_groups
                            )
            
                            test_name = "Kruskal-Wallis"
            
                except:
            
                    p_main = None
            
                # ===============================
                # TITLE
                # ===============================
                if p_main is not None:
            
                    ax.set_title(
                        f"{sex}\n{test_name} p = {p_main:.4f}",
                        fontsize=13,
                        fontweight="bold"
                    )
            
                else:
            
                    ax.set_title(
                        sex,
                        fontsize=13,
                        fontweight="bold"
                    )
            
                # ===============================
                # POST HOC VS CONTROL
                # ===============================
                if len(groups) >= 2:
            
                    control = groups[0]
            
                    control_vals = df_sex[
                        df_sex["Group"] == control
                    ][param].dropna()
            
                    ymax = df_sex[param].max()
                    ymin = df_sex[param].min()
            
                    yrange = ymax - ymin
            
                    line_y = ymax + (yrange * 0.10)
            
                    for idx, g in enumerate(groups[1:]):
            
                        vals = df_sex[
                            df_sex["Group"] == g
                        ][param].dropna()
            
                        try:
            
                            if normal and equal_var:
            
                                _, p_post = stats.ttest_ind(
                                    control_vals,
                                    vals
                                )
            
                            else:
            
                                _, p_post = stats.mannwhitneyu(
                                    control_vals,
                                    vals
                                )
            
                            # significance
                            if p_post < 0.0001:
                                sig = "****"
            
                            elif p_post < 0.001:
                                sig = "***"
            
                            elif p_post < 0.01:
                                sig = "**"
            
                            elif p_post < 0.05:
                                sig = "*"
            
                            else:
                                sig = "ns"
            
                            x1 = 1
                            x2 = idx + 2
            
                            y = line_y + (idx * yrange * 0.07)
            
                            # line
                            ax.plot(
                                [x1, x1, x2, x2],
                                [y, y+(yrange*0.02),
                                 y+(yrange*0.02), y],
                                lw=1.3,
                                c="black"
                            )
            
                            # text
                            ax.text(
                                (x1+x2)/2,
                                y+(yrange*0.03),
                                sig,
                                ha="center",
                                va="bottom",
                                fontsize=12,
                                fontweight="bold"
                            )
            
                        except:
                            pass
            
                # ===============================
                # AXIS STYLE
                # ===============================
                ax.set_xticks(
                    range(1, len(groups)+1)
                )
            
                ax.set_xticklabels(
                    groups,
                    rotation=45,
                    fontsize=10
                )
            
                ax.set_ylabel(
                    param,
                    fontsize=11,
                    fontweight="bold"
                )
            
                # clean theme
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
            
                ax.grid(
                    False
                )
            
            # ===============================
            # FINAL TITLE
            # ===============================
            fig.suptitle(
                f"{param} by Sex",
                fontsize=17,
                fontweight="bold"
            )
            
            plt.tight_layout()
            
            st.pyplot(fig)

        
        else:

            st.warning(
                "Tidak ada data hematologi ditemukan"
            )

    except Exception as e:

        st.error(f"Error membaca file: {e}")
