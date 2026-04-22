import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.title("📊 Hematology Data Input")

# ===============================
# UPLOAD SECTION
# ===============================
st.subheader("📥 Upload Data")

col1, col2, col3 = st.columns(3)

baseline_file = col1.file_uploader("Baseline (Day 0)", type=["xlsx","csv"])
midline_file  = col2.file_uploader("Midline", type=["xlsx","csv"])
endline_file  = col3.file_uploader("Endline", type=["xlsx","csv"])

# ===============================
# FUNCTION LOAD
# ===============================

def load_data(file, label):
    if file is None:
        return None
    
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    # ===============================
    # 🔥 FILTER PARAMETER HEMATOLOGI
    # ===============================
    hematology_params = ["	WBC","	Neu#","	Lym#","	Mon#","	Eos#","	Bas#","	Neu%","	Lym%","	Mon%","	Eos%","	Bas%","	RBC",
                         "	HGB","	HCT","	MCV","	MCH","	MCHC","	RDW-CV","	RDW-SD","	PLT","	MPV","	PDW","	PCT"]

    df = df[df[df.columns[0]].isin(hematology_params)]

    # ===============================
    # TRANSFORM KE LONG
    # ===============================
    df_long = df.melt(
        id_vars=df.columns[0],
        var_name="Sample",
        value_name="Value"
    )
    
    df_long.columns = ["Parameter", "Sample", "Value"]
    
    # ===============================
    # 🔥 CLEAN VALUE
    # ===============================
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    
    # ===============================
    # ADD TIMEPOINT
    # ===============================
    df_long["Timepoint"] = label
    
    return df_long

# ===============================
# LOAD ALL
# ===============================
df_list = []

df_baseline = load_data(baseline_file, "Baseline")
df_midline  = load_data(midline_file, "Midline")
df_endline  = load_data(endline_file, "Endline")

for df in [df_baseline, df_midline, df_endline]:
    if df is not None:
        df_list.append(df)

# ===============================
# COMBINE
# ===============================
if len(df_list) > 0:

    df_all = pd.concat(df_list, ignore_index=True)

    # ===============================
    # 🧬 GROUP ASSIGNMENT (RANGE INPUT)
    # ===============================
    
    unique_samples = sorted(df_all["Sample"].unique())
    
    # fungsi parser
    def parse_range(text):
        samples = []
        parts = text.split(",")
    
        for p in parts:
            p = p.strip()
            if "-" in p:
                start, end = p.split("-")
                samples += [str(i) for i in range(int(start), int(end)+1)]
            elif p != "":
                samples.append(p)
        return samples
    
    # jumlah group
    n_group = st.number_input("Jumlah kelompok", 1, 10, 2)
    
    group_map = {}
    
    for i in range(n_group):
        col1, col2 = st.columns(2)
    
        with col1:
            gname = st.text_input(f"Nama Group {i+1}", f"Group {i+1}", key=f"gname{i}")
    
        with col2:
            grange = st.text_input(
                f"Range Sample (contoh: 1-5 atau 1-3,5,7-9)",
                key=f"grange{i}"
            )
    
        try:
            parsed = parse_range(grange)
    
            for p in parsed:
                # 🔥 cocokkan dengan sample name
                for s in unique_samples:
                    if s.endswith(str(p)):   # fleksibel (S1, ID_1, dll)
                        group_map[s] = gname
    
        except:
            st.warning(f"Format salah di Group {i+1}")
    
    # ===============================
    # APPLY GROUP
    # ===============================
    df_all["Group"] = df_all["Sample"].map(group_map)
    
    # ===============================
    # PREVIEW
    # ===============================
    st.subheader("📋 Group Mapping")
    st.dataframe(df_all[["Sample","Group"]].drop_duplicates())

    # ===============================
    # INFO DETECTION
    # ===============================
    st.subheader("🔍 Detected Structure")

    st.write("Jumlah sample:", df_all["Sample"].nunique())
    st.write("Jumlah parameter:", df_all["Parameter"].nunique())
    st.write("Timepoints:", df_all["Timepoint"].unique())

    # ===============================
    # 📏 COMPACT RANGE (1 INPUT)
    # ===============================
    st.markdown("---")
    st.subheader("📏 Reference Range")
    
    parameters = df_all["Parameter"].unique()
    
    range_dict = {}
    
    cols_per_row = 4
    
    # parser function
    def parse_range(text):
        try:
            low, high = text.split("-")
            return float(low), float(high)
        except:
            return None, None
    
    for i in range(0, len(parameters), cols_per_row):
    
        subset = parameters[i:i+cols_per_row]
        cols = st.columns(len(subset))
    
        for j, param in enumerate(subset):
    
            with cols[j]:
    
                st.markdown(f"**{param}**")
    
                val = st.text_input(
                    "range",
                    value="",
                    key=f"range_{param}",
                    label_visibility="collapsed"
                )
    
                low, high = parse_range(val)
    
                range_dict[param] = (low, high)
    # ===============================
    # 🚨 OUT OF RANGE SUMMARY (FINAL)
    # ===============================
    st.markdown("---")
    st.subheader("🚨 Out of Range Summary")
    
    results = []
    
    for param in df_all["Parameter"].unique():
    
        low, high = range_dict.get(param, (None, None))
        if low is None or high is None:
            continue
    
        df_param = df_all[df_all["Parameter"] == param]
    
        for (g, tp), df_sub in df_param.groupby(["Group", "Timepoint"]):
    
            vals = df_sub["Value"].dropna()
    
            if len(vals) == 0:
                continue
    
            below = (vals < low).sum()
            above = (vals > high).sum()
            n = len(vals)
    
            results.append({
                "Parameter": param,
                "Group": g,
                "Timepoint": tp,
                "n": n,
                "Below": below,
                "Above": above,
                "Out of Range": below + above,
                "Below (%)": round(below/n*100, 2),
                "Above (%)": round(above/n*100, 2),
            })
    
    # ===============================
    # DISPLAY
    # ===============================
    if len(results) > 0:
    
        result_df = pd.DataFrame(results)
    
        result_df = result_df.sort_values(
            ["Parameter", "Group", "Timepoint"]
        )
    
        st.dataframe(result_df, use_container_width=True)
    
    else:
        st.info("Belum ada data atau range belum diisi")

    # ===============================
    # 📊 STATISTICAL TEST (BASELINE)
    # ===============================
    from scipy.stats import kruskal, mannwhitneyu
    
    st.markdown("---")
    st.subheader("📊 Statistical Test (Baseline)")
    
    # filter baseline saja
    df_base = df_all[df_all["Timepoint"] == "Baseline"]
    
    if df_base.empty:
        st.info("Tidak ada data baseline")
    else:
    
        # pilih reference group
        groups = sorted(df_base["Group"].dropna().unique())
        ref_group = st.selectbox("Reference Group", groups)
    
        results = []
    
        for param in df_base["Parameter"].unique():
    
            df_param = df_base[df_base["Parameter"] == param]
    
            # kumpulkan data per group
            group_data = []
            group_labels = []
    
            for g in groups:
                vals = df_param[df_param["Group"] == g]["Value"].dropna()
                if len(vals) > 0:
                    group_data.append(vals)
                    group_labels.append(g)
    
            # ===============================
            # KRUSKAL WALLIS
            # ===============================
            if len(group_data) >= 2:
    
                try:
                    stat, p_kw = kruskal(*group_data)
                except:
                    p_kw = np.nan
    
                # ===============================
                # POSTHOC vs REFERENCE
                # ===============================
                posthoc_results = {}
    
                if p_kw < 0.05:
    
                    ref_vals = df_param[df_param["Group"] == ref_group]["Value"].dropna()
    
                    for g in group_labels:
                        if g == ref_group:
                            continue
    
                        vals = df_param[df_param["Group"] == g]["Value"].dropna()
    
                        if len(vals) > 0 and len(ref_vals) > 0:
                            try:
                                _, p_post = mannwhitneyu(ref_vals, vals, alternative='two-sided')
                            except:
                                p_post = np.nan
    
                            # ⭐ SIGNIFICANCE STAR
                            if p_post < 0.001:
                                star = "***"
                            elif p_post < 0.01:
                                star = "**"
                            elif p_post < 0.05:
                                star = "*"
                            else:
                                star = ""
    
                            posthoc_results[g] = f"{p_post:.4f} {star}"
    
                results.append({
                    "Parameter": param,
                    "Kruskal p": round(p_kw, 4) if not np.isnan(p_kw) else np.nan,
                    "Posthoc vs " + ref_group: posthoc_results
                })
        
        # ===============================
        # DISPLAY
        # ===============================
        if len(results) > 0:
        
            result_df = pd.DataFrame(results)
        
            st.dataframe(result_df, use_container_width=True)
        
        else:
            st.info("Tidak ada data yang bisa dianalisis")

    # ===============================
    # 📦 MINI BOXPLOT (CLEAN STYLE)
    # ===============================
    st.markdown("---")
    st.subheader("📦 Hematology Boxplot")
    
    parameters = df_all["Parameter"].unique()
    groups_unique = df_all["Group"].dropna().unique()
    
    colors = {
        "Baseline": "#3b82f6",
        "Midline": "#10b981",
        "Endline": "#ef4444"
    }
    
    cols_per_row = 5
    
    for i in range(0, len(parameters), cols_per_row):
    
        subset_params = parameters[i:i+cols_per_row]
        cols = st.columns(len(subset_params))
    
        for j, param in enumerate(subset_params):
    
            with cols[j]:
    
                df_param = df_all[df_all["Parameter"] == param]
    
                box_data = []
                box_colors = []
                positions = []
                group_positions = []
    
                pos = 1
    
                for g in groups_unique:
    
                    start = pos
                    count = 0
    
                    for tp in ["Baseline", "Midline", "Endline"]:
    
                        vals = df_param[
                            (df_param["Group"] == g) &
                            (df_param["Timepoint"] == tp)
                        ]["Value"].dropna()
    
                        if len(vals) > 0:
                            box_data.append(vals.values)
                            box_colors.append(colors.get(tp, "gray"))
                            positions.append(pos)
    
                            pos += 1
                            count += 1
    
                    if count > 0:
                        group_positions.append((start + pos - 1) / 2)
    
                    pos += 1  # spacing antar group
    
                # ===============================
                # PLOT
                # ===============================
                if len(box_data) > 0:
    
                    fig, ax = plt.subplots(figsize=(2.5,2.2))
    
                    bp = ax.boxplot(
                        box_data,
                        positions=positions,
                        widths=0.6,
                        patch_artist=True
                    )
                    low, high = range_dict.get(param, (None, None))

                    if low is not None and high is not None:
                        ax.axhline(low, linestyle="--", linewidth=1)
                        ax.axhline(high, linestyle="--", linewidth=1)
    
                    # warna berdasarkan waktu
                    for patch, color in zip(bp["boxes"], box_colors):
                        patch.set_facecolor(color)
    
                    # X-axis hanya group
                    ax.set_xticks(group_positions)
                    ax.set_xticklabels(groups_unique, fontsize=6)
    
                    ax.set_title(param, fontsize=8)
                    ax.tick_params(axis='y', labelsize=6)
    
                    ax.spines['top'].set_visible(False)
                    ax.spines['right'].set_visible(False)
    
                    st.pyplot(fig)
        

    else:
        st.info("Silakan upload minimal data baseline")
