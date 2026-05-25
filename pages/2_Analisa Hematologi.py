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
            # JCO COLOR
            # ===============================
            JCO_COLORS = [
                "#0073C2FF",
                "#EFC000FF",
                "#868686FF",
                "#CD534CFF",
                "#7AA6DCFF",
                "#003C67FF"
            ]
            
            # ===============================
            # PARAMETER
            # ===============================
            param = st.selectbox(
                "Select Parameter",
                TARGET_COLS
            )
            
            # ===============================
            # DATA
            # ===============================
            plot_df = assigned_df.copy()
            
            plot_df = plot_df.dropna(
                subset=[param, "Group", "Sex"]
            )
            
            # ===============================
            # FIGURE
            # ===============================
            fig, axes = plt.subplots(
                1,
                2,
                figsize=(16,7)
            )
            
            sexes = ["Male", "Female"]
            
            # ===============================
            # LOOP SEX
            # ===============================
            for ax, sex in zip(axes, sexes):
            
                df_sex = plot_df[
                    plot_df["Sex"] == sex
                ].copy()
            
                if len(df_sex) == 0:
            
                    ax.set_title(f"{sex} (No Data)")
                    continue
            
                groups = list(
                    df_sex["Group"]
                    .dropna()
                    .drop_duplicates()
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
                # MAIN TEST
                # ===============================
                p_main = np.nan
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
            
                    # parametric
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
            
                    # non parametric
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
                    pass
            
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
                        facecolor=JCO_COLORS[i],
                        alpha=0.55,
                        edgecolor="black",
                        linewidth=1.6
                    )
            
                for median in bp["medians"]:
            
                    median.set(
                        color="black",
                        linewidth=2.3
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
            
                # ===============================
                # JITTER
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
                        color="gray",
                        edgecolors="black",
                        linewidths=0.7,
                        s=50,
                        alpha=0.7,
                        zorder=5
                    )
            
                # ===============================
                # CONTROL RANGE
                # ===============================
                control_vals = data_groups[0]
            
                control_min = np.min(control_vals)
                control_max = np.max(control_vals)
            
                lower_range = control_min * 0.90
                upper_range = control_max * 1.10
            
                # lower line
                ax.axhline(
                    lower_range,
                    color="red",
                    linestyle="--",
                    linewidth=1.5
                )
            
                # upper line
                ax.axhline(
                    upper_range,
                    color="red",
                    linestyle="--",
                    linewidth=1.5
                )
            
                # text range
                ax.text(
                    0.55,
                    upper_range,
                    f"Upper range\n{upper_range:.2f}",
                    color="red",
                    fontsize=10
                )
            
                ax.text(
                    0.55,
                    lower_range,
                    f"Lower range\n{lower_range:.2f}",
                    color="red",
                    fontsize=10
                )
            
                # ===============================
                # POST HOC
                # ===============================
                ymax = df_sex[param].max()
                ymin = df_sex[param].min()
            
                yrange = ymax - ymin
            
                start_y = ymax + (yrange * 0.20)
            
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
            
                        y = start_y + (idx * yrange * 0.09)
            
                        # line
                        ax.plot(
                            [x1, x1, x2, x2],
                            [y, y+(yrange*0.02),
                             y+(yrange*0.02), y],
                            lw=1.4,
                            c="black"
                        )
            
                        # text
                        ax.text(
                            (x1+x2)/2,
                            y+(yrange*0.03),
                            sig,
                            ha="center",
                            fontsize=13,
                            fontweight="bold"
                        )
            
                    except:
                        pass
            
                # ===============================
                # OUT OF RANGE
                # ===============================
                or_counts = []
            
                for vals in data_groups:
            
                    out_count = np.sum(
                        (vals < lower_range) |
                        (vals > upper_range)
                    )
            
                    or_counts.append(out_count)
            
                # ===============================
                # LABEL OR
                # ===============================
                xtick_labels = []
            
                for g, orv in zip(groups, or_counts):
            
                    label = f"{g}\n\nOR = {orv}"
            
                    xtick_labels.append(label)
            
                ax.set_xticks(
                    range(1, len(groups)+1)
                )
            
                ax.set_xticklabels(
                    xtick_labels,
                    fontsize=14
                )
            
                # ===============================
                # TITLE
                # ===============================
                ax.set_title(
                    f"{sex}\n{test_name} p = {p_main:.4f}",
                    fontsize=17,
                    fontweight="bold"
                )
            
                # ===============================
                # AXIS
                # ===============================
                ax.set_ylabel(
                    param,
                    fontsize=14,
                    fontweight="bold"
                )
            
                # independent y scale
                ax.set_ylim(
                    ymin - (yrange*0.25),
                    ymax + (yrange*0.45)
                )
            
                # remove top/right
                ax.spines["top"].set_visible(False)
                ax.spines["right"].set_visible(False)
            
            # ===============================
            # GLOBAL TITLE
            # ===============================
            fig.suptitle(
                f"{param} by Sex",
                fontsize=24,
                fontweight="bold"
            )
            
            plt.tight_layout()
            
            st.pyplot(fig)

# ============================================
            # ===============================
            # POST HOC TABLE
            # ===============================
            st.markdown("---")
            st.subheader("📋 Post Hoc Comparison")
            
            posthoc_results = []
            
            # ===============================
            # DESCRIPTIVE TABLE
            # ===============================
            desc_results = []
            
            # ===============================
            # COMPACT LETTER DISPLAY
            # ===============================
            letter_results = []
            
            # ===============================
            # LOOP SEX
            # ===============================
            for sex in sexes:
            
                df_sex = plot_df[
                    plot_df["Sex"] == sex
                ].copy()
            
                if len(df_sex) == 0:
                    continue
            
                groups = list(
                    df_sex["Group"]
                    .dropna()
                    .drop_duplicates()
                )
            
                # ===============================
                # CONTROL RANGE
                # ===============================
                control_vals = df_sex[
                    df_sex["Group"] == groups[0]
                ][param].dropna()
            
                control_min = np.min(control_vals)
                control_max = np.max(control_vals)
            
                lower_range = control_min * 0.9
                upper_range = control_max * 1.10
            
                # ===============================
                # DESCRIPTIVE
                # ===============================
                for g in groups:
            
                    vals = df_sex[
                        df_sex["Group"] == g
                    ][param].dropna()
            
                    mean_val = np.mean(vals)
                    sd_val = np.std(vals, ddof=1)
            
                    # out of range
                    or_count = np.sum(
                        (vals < lower_range) |
                        (vals > upper_range)
                    )
            
                    desc_results.append({
                        "Sex": sex,
                        "Group": g,
                        "Mean ± SD":
                            f"{mean_val:.2f} ± {sd_val:.2f}",
                        "N": len(vals),
                        "OR": int(or_count)
                    })
            
                # ===============================
                # PAIRWISE WILCOXON
                # ===============================
                group_letters = {}
            
                alphabet = list("abcdefghijklmnopqrstuvwxyz")
            
                for i, g1 in enumerate(groups):
            
                    vals1 = df_sex[
                        df_sex["Group"] == g1
                    ][param].dropna()
            
                    current_letter = alphabet[i]
            
                    group_letters[g1] = current_letter
            
                    for j, g2 in enumerate(groups):
            
                        if j <= i:
                            continue
            
                        vals2 = df_sex[
                            df_sex["Group"] == g2
                        ][param].dropna()
            
                        try:
            
                            # ===============================
                            # WILCOXON / MANN WHITNEY
                            # ===============================
                            _, pval = stats.mannwhitneyu(
                                vals1,
                                vals2,
                                alternative="two-sided"
                            )
            
                            # ===============================
                            # SIGNIFICANCE
                            # ===============================
                            if pval < 0.0001:
                                sig = "****"
            
                            elif pval < 0.001:
                                sig = "***"
            
                            elif pval < 0.01:
                                sig = "**"
            
                            elif pval < 0.05:
                                sig = "*"
            
                            else:
                                sig = "ns"
            
                            # ===============================
                            # LETTER GROUPING
                            # ===============================
                            if pval >= 0.05:
            
                                group_letters[g2] = current_letter
            
                            else:
            
                                if g2 not in group_letters:
                                    group_letters[g2] = alphabet[j]
            
                            # ===============================
                            # SAVE RESULT
                            # ===============================
                            posthoc_results.append({
                                "Sex": sex,
                                "Parameter": param,
                                "Comparison": f"{g1} vs {g2}",
                                "P-value": round(pval,5),
                                "Significance": sig
                            })
            
                        except:
                            pass
            
                # ===============================
                # LETTER TABLE
                # ===============================
                for g in groups:
            
                    vals = df_sex[
                        df_sex["Group"] == g
                    ][param].dropna()
            
                    mean_val = np.mean(vals)
            
                    letter_results.append({
                        "Sex": sex,
                        "Group": g,
                        "Mean": round(mean_val,2),
                        "Letter": group_letters[g]
                    })
            
            # ===============================
            # SHOW DESCRIPTIVE
            # ===============================
            st.markdown("## 📊 Descriptive Statistics")
            
            desc_df = pd.DataFrame(
                desc_results
            )
            
            st.dataframe(
                desc_df,
                use_container_width=True
            )
            
            # ===============================
            # SHOW POST HOC
            # ===============================
            st.markdown("## 📋 Pairwise Wilcoxon Post Hoc")
            
            posthoc_df = pd.DataFrame(
                posthoc_results
            )
            
            st.dataframe(
                posthoc_df,
                use_container_width=True
            )
            
# ============================================
        else:

            st.warning(
                "Tidak ada data hematologi ditemukan"
            )

    except Exception as e:

        st.error(f"Error membaca file: {e}")
