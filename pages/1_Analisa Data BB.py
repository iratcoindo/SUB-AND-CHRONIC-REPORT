import streamlit as st
import pandas as pd
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import kruskal, mannwhitneyu
import itertools
from scipy.stats import spearmanr, pearsonr

# PAGE CONFIG
st.set_page_config(
    page_title="",
    page_icon="logo.png",
    layout="wide"
)

# HEADER
col1, col2 = st.columns([8,2])
with col1:
    st.title("📈 Template Data Berat Badan-iRATco")
with col2:
    st.image("logo_iratco.png", width=250)
    

# =========================
# INPUT
# =========================
raw_text = st.text_area("Paste your table", height=300)

# =========================
# PARSER
# =========================
def parse_table(text):
    lines = text.strip().split("\n")
    data = []
    for line in lines:
        nums = re.findall(r"\d+\.?\d*", line)
        if len(nums) > 1:
            data.append([float(x) for x in nums])
    return pd.DataFrame(data)

# =========================
# MAIN PROCESS (SAFE)
# =========================
if raw_text:

    df = parse_table(raw_text)

    # =========================
    # COLUMN LABEL
    # =========================
    col_labels = st.text_input("Column labels", "isikan waktu, pisahkan dengan koma")
    if col_labels:
        cols = [c.strip() for c in col_labels.split(",")]
        if len(cols) == df.shape[1]:
            df.columns = cols

    # =========================
    # GROUP
    # =========================
    group_names = st.text_input(
        "Group names",
        "isikan kelompok, pisahkan dengan koma"
    )

    rows_per_group = st.number_input("Rows per group", value=6, min_value=1)

    if group_names:
        groups = [g.strip() for g in group_names.split(",")]
        labels = []
        for g in groups:
            labels += [g] * rows_per_group

        if len(labels) == len(df):
            df["Group"] = labels

    # =========================
    # SAMPLE ID INPUT
    # =========================
    id_mode = st.radio(
        "Sample ID mode",
        ["Auto", "Manual"]
    )

    if id_mode == "Auto":
        df["Sample_ID"] = [f"S{i+1}" for i in range(len(df))]

    elif id_mode == "Manual":

        manual_ids = st.text_area(
            "Input Sample IDs (pisahkan dengan koma / baris)",
            placeholder="S1,S2,S3,..."
        )
    
        if manual_ids:
            ids = [i.strip() for i in manual_ids.replace("\n", ",").split(",")]
    
            if len(ids) == len(df):
                df["Sample_ID"] = ids
            else:
                st.warning("Jumlah ID tidak sesuai jumlah sampel")

    if "Sample_ID" not in df.columns:
        st.warning("Sample ID belum diisi")
    
    # =========================
    # LONG FORMAT (INTERNAL ONLY)
    # =========================
    if "Group" in df.columns:

        df_long = df.melt(
            id_vars=["Group", "Sample_ID"],
            var_name="Day",
            value_name="Value"
        )
        # =========================
        # DOWNLOAD
        # =========================
        st.download_button(
            "⬇️ Download Data CSV",
            df_long.to_csv(index=False).encode("utf-8"),
            "data.csv",
            "text/csv"
        )

        # =========================
        # SUMMARY
        # =========================
        summary = df_long.groupby(["Group","Day"]).agg(
            mean=("Value","mean"),
            std=("Value","std"),
            count=("Value","count")
        ).reset_index()

        summary["sem"] = summary["std"] / np.sqrt(summary["count"])

        # =========================
        # OPTIONS
        # =========================
        col1, col2, col3 = st.columns(3)

        with col1:
            error_type = st.selectbox(
                "Error bar",
                ["SD", "SEM"]
            )
        with col2:
            y_min = st.number_input("Y min", value=float(df_long["Value"].min()))
        with col3:
            y_max = st.number_input("Y max", value=float(df_long["Value"].max()))

        # =========================
        # COLORS
        # =========================
        def get_colors(n):
            base = ["#0073C2", "#E63946", "#2A9D8F", "#F4A261", "#6A4C93", "#264653", "#8D99AE"]
            return base[:n]

        # =========================
        # PLOT + OPTIONS
        # =========================
        
        # ---------- BASIC OPTIONS ----------
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_label = st.text_input("X-axis label", "Day")
        
        with col2:
            y_label = st.text_input("Y-axis label", "Value")
        
        with col3:
            use_jitter = st.checkbox("Show jitter", value=False)
        
        # ---------- STYLE OPTIONS ----------
        col4, col5, col6 = st.columns(3)
        
        with col4:
            point_size = st.number_input("Jitter point size", value=20, min_value=1)
        
        with col5:
            line_width = st.slider("Line width", 1.0, 5.0, 2.0)
        
        with col6:
            use_line_palette = st.checkbox("Use line style palette", value=False)
        
        col7, col8 = st.columns(2)
        
        with col7:
            use_marker_palette = st.checkbox("Use marker palette", value=False)
        
        with col8:
            palette_name = st.selectbox(
                "Color palette",
                ["Prism", "JCO", "NPG", "Lancet","AAAS","BW","iRATco Style"]
            )
        
        # =========================
        # COLOR PALETTE
        # =========================
        def get_colors(n, palette):
            if palette == "Prism":
                base = ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B2","#937860","#DA8BC3"]
            elif palette == "JCO":
                base = ["#0073C2","#EFC000","#868686","#CD534C","#7AA6DC","#003C67","#8F7700"]
            elif palette == "NPG":
                base = ["#E64B35","#4DBBD5","#00A087","#3C5488","#F39B7F","#8491B4","#91D1C2"]
            elif palette == "Lancet":
                base = ["#00468B","#ED0000","#42B540","#0099B4","#925E9F","#FDAF91","#AD002A"]
            elif palette == "AAAS":
                base = ["#3B4992","#EE0000","#008B45","#631879","#008280","#BB0021","#5F559B"]
            elif palette == "BW":
                base = ["#000000", "#444444", "#777777", "#AAAAAA", "#CCCCCC"]
            elif palette == "iRATco Style":
                base = ["#0073C2", "#E63946", "#2A9D8F", "#F4A261", "#6A4C93", "#264653", "#8D99AE"]
            else:
                base = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b"]
            return base[:n]

        
        # =========================
        # STYLE PALETTE
        # =========================
        marker_styles = ['o', 's', '^', 'D', 'P', 'X']
        line_styles = ['-', '--', '-.', ':']

        # =========================
        # PLOT
        # =========================
        fig, ax = plt.subplots(figsize=(7,5))
        
        groups = [g.strip() for g in group_names.split(",")]
        groups = [g for g in groups if g in summary["Group"].unique()]
        
        colors = get_colors(len(groups), palette_name)
        
        for i, g in enumerate(groups):
            sub = summary[summary["Group"] == g].copy()
        
            sub["Day"] = pd.Categorical(sub["Day"], categories=cols, ordered=True)
            sub = sub.sort_values("Day")
        
            x = [float(d) for d in sub["Day"]]
            y = sub["mean"].values
        
            yerr = sub["std"].values if error_type=="SD" else sub["sem"].values
        
            # =========================
            # STYLE CONTROL
            # =========================
            marker = marker_styles[i % len(marker_styles)] if use_marker_palette else 'o'
            linestyle = line_styles[i % len(line_styles)] if use_line_palette else '-'
        
            # =========================
            # LINE + ERRORBAR
            # =========================
            ax.plot(
                x, y,
                marker=marker,
                linestyle=linestyle,
                linewidth=line_width,
                color=colors[i],
                label=g
            )
        
            ax.errorbar(
                x, y,
                yerr=yerr,
                capsize=4,
                color=colors[i],
                linestyle='none'
            )
        
            # =========================
            # JITTER
            # =========================
            if use_jitter:
                raw = df_long[df_long["Group"] == g]
        
                for d in cols:
                    vals = raw[raw["Day"] == d]["Value"].values
        
                    if len(vals) > 0:
                        x_center = float(d)
                        x_jitter = x_center + np.random.uniform(-0.05, 0.05, size=len(vals))
        
                        ax.scatter(
                            x_jitter,
                            vals,
                            s=point_size,
                            alpha=0.5,
                            color=colors[i],
                            marker=marker,
                            edgecolors="none"
                        )
        
        # =========================
        # AXIS
        # =========================
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        
        ax.set_xticks([float(d) for d in cols])
        ax.set_xticklabels(cols)
        
        ax.set_ylim(y_min, y_max)
        
        # =========================
        # LEGEND
        # =========================
        ax.legend(
            loc='center left',
            bbox_to_anchor=(1, 0.5),
            frameon=False
        )
        
        plt.tight_layout(rect=[0, 0, 0.8, 1])
        
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("## 📈 R² Value Summary Table")

        # =========================
        # PREP
        # =========================
        df_long["Day_num"] = df_long["Day"].astype(float)
        unique_days = [float(c) for c in cols]
        
        r2_table = []

        for g in groups:
            sub = df_long[df_long["Group"] == g].copy()
        
            row = {"Group": g}
        
            sub = sub.sort_values(["Day_num"]).reset_index(drop=True)
        
            x = sub["Day_num"].values
            y = sub["Value"].values
        
            mask = ~np.isnan(x) & ~np.isnan(y)
            x_clean = x[mask]
            y_clean = y[mask]
        
            if len(x_clean) > 1 and len(np.unique(y_clean)) > 1:
                r, _ = pearsonr(x_clean, y_clean)
                row["R (ggpubr style)"] = round(r, 4)
            else:
                row["R (ggpubr style)"] = np.nan
        
            r2_table.append(row)
        
        df_r2 = pd.DataFrame(r2_table)
        st.dataframe(df_r2, use_container_width=True)
        
        # =========================
        # STATISTICS
        # =========================
        st.markdown("## 📊 Statistics")

        stat_day = st.selectbox("Select day", cols)

        data_by_group = []
        labels = []

        for g in groups:
            vals = df_long[
                (df_long["Group"] == g) &
                (df_long["Day"] == stat_day)
            ]["Value"].values

            if len(vals) > 0:
                data_by_group.append(vals)
                labels.append(g)

        if len(data_by_group) >= 2:

            H, p = kruskal(*data_by_group)

            st.write(f"**Kruskal-Wallis p = {p:.4f}**")

            results = []

            for (g1, v1), (g2, v2) in itertools.combinations(zip(labels, data_by_group), 2):
                _, p_pair = mannwhitneyu(v1, v2, alternative='two-sided')

                def get_significance(p):
                    if p < 0.0001:
                        return "****"
                    elif p < 0.001:
                        return "***"
                    elif p < 0.01:
                        return "**"
                    elif p < 0.05:
                        return "*"
                    else:
                        return "ns"
                
                results.append({
                    "Group 1": g1,
                    "Group 2": g2,
                    "p-value": round(p_pair,4),
                    "P.signif": get_significance(p_pair)
                })

            st.dataframe(pd.DataFrame(results))

        # =========================
        # DELTA CALCULATION
        # =========================
        st.markdown("## 🔄 Delta (Δ) Mean ± SD Table")
        
        baseline = cols[0]
        
        delta_records = []
        
        for g in groups:
            sub = df_long[df_long["Group"] == g].copy()
        
            # pivot biar per sample
            pivot = sub.pivot(index="Sample_ID", columns="Day", values="Value")
        
            if baseline not in pivot.columns:
                continue
        
            base_vals = pivot[baseline]
        
            row = {"Group": g}
        
            for d in cols:
                if d in pivot.columns:
        
                    delta = pivot[d] - base_vals
        
                    mean = np.nanmean(delta)
                    sd = np.nanstd(delta)
        
                    row[d] = f"{mean:.2f} ± {sd:.2f}"
        
            delta_records.append(row)
        
        df_delta = pd.DataFrame(delta_records)
        
        st.dataframe(df_delta, use_container_width=True)

        # =========================
        # DELTA LONG (FOR BOXPLOT)
        # =========================
        delta_long = []
        
        for g in groups:
            sub = df_long[df_long["Group"] == g].copy()
        
            pivot = sub.pivot(index="Sample_ID", columns="Day", values="Value")
        
            if baseline not in pivot.columns:
                continue
        
            base_vals = pivot[baseline]
        
            for d in cols:
                if d in pivot.columns:
        
                    delta_vals = pivot[d] - base_vals
        
                    for val in delta_vals:
                        if not np.isnan(val):
                            delta_long.append({
                                "Group": g,
                                "Day": d,
                                "Delta": val
                            })
        
        delta_long = pd.DataFrame(delta_long)

        # =========================
        # DELTA BOXPLOT PER TIME (HIGH QUALITY + STATS)
        # =========================
        st.markdown("## 📦 Delta Boxplot + Statistics (Per Time)")
        
        # pilih reference group
        ref_group = st.selectbox("Reference group", groups)
        
        colors = get_colors(len(groups), palette_name)
        color_map = {g: colors[i] for i, g in enumerate(groups)}
        
        def get_significance(p):
            if p < 0.0001:
                return "****"
            elif p < 0.001:
                return "***"
            elif p < 0.01:
                return "**"
            elif p < 0.05:
                return "*"
            else:
                return "ns"
        
        for d in cols:
        
            st.markdown(f"### Day {d}")
        
            fig, ax = plt.subplots(figsize=(4,3), dpi=500)
        
            data_plot = []
            labels_plot = []
        
            for g in groups:
                vals = delta_long[
                    (delta_long["Day"] == d) &
                    (delta_long["Group"] == g)
                ]["Delta"].dropna().values
        
                if len(vals) > 0:
                    data_plot.append(vals)
                    labels_plot.append(g)
        
            if len(data_plot) == 0:
                st.warning("No data available")
                continue
        
            # =========================
            # BOXPLOT
            # =========================
            bp = ax.boxplot(
                data_plot,
                widths=0.6,
                patch_artist=True
            )
        
            for patch, g in zip(bp['boxes'], labels_plot):
                patch.set_facecolor(color_map[g])
        
            # =========================
            # AXIS
            # =========================
            ax.set_xticklabels(labels_plot, rotation=0, ha='right')
            ax.set_ylabel("Δ Berat Badan (gr)")
        
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
            # =========================
            # STATISTICS (FINAL FIX - POSITION SAFE)
            # =========================
            
            # mapping group → data
            group_data = {}
            group_positions = {}
            
            for i, g in enumerate(labels_plot):
                group_data[g] = data_plot[i]
                group_positions[g] = i   # 🔥 posisi REAL di plot
            
            # pastikan reference ada
            if ref_group in group_data:
            
                ref_vals = group_data[ref_group]
            
                y_max = max([np.max(v) for v in group_data.values() if len(v) > 0])
                y_min = min([np.min(v) for v in group_data.values() if len(v) > 0])
                y_offset = (y_max - y_min) * 0.15
            
                current_y = y_max + y_offset
            
                for g in labels_plot:
            
                    if g == ref_group:
                        continue
            
                    vals = group_data[g]
            
                    if len(vals) > 1 and len(ref_vals) > 1:
            
                        _, p_val = mannwhitneyu(ref_vals, vals, alternative='two-sided')
                        signif = get_significance(p_val)
            
                        if signif != "ns":
            
                            x1 = group_positions[ref_group] + 1
                            x2 = group_positions[g] + 1
            
                            # bracket
                            ax.plot(
                                [x1, x1, x2, x2],
                                [current_y, current_y+0.1, current_y+0.1, current_y],
                                lw=1.5,
                                color='black'
                            )
            
                            # label
                            ax.text(
                                (x1 + x2) / 2,
                                current_y + 0.1,
                                signif,
                                ha='center',
                                va='bottom',
                                fontsize=12,
                                fontweight='bold'
                            )
            
                            current_y += y_offset

            # =========================
            # KRUSKAL-WALLIS (GLOBAL)
            # =========================
            from scipy.stats import kruskal
            
            all_groups = [v for v in group_data.values() if len(v) > 1]
            
            if len(all_groups) >= 2:
                H, p_kw = kruskal(*all_groups)
            
                ax.text(
                    0.05, 1.2,
                    f"Kruskal p = {p_kw:.4f}",
                    transform=ax.transAxes,
                    ha='left',
                    va='top',
                    fontsize=11,
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
                )
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

else:
    st.info("👉 Paste data terlebih dahulu untuk memulai")

st.markdown("---")

st.markdown("""
© 2026 Mawar Subangkit  
**Template Data Berat Badan iRATco**  

If you use this software, please cite:

**Subangkit**, MAWAR (2026)  
**Template Data Berat Badan iRATco**  
Available at: https://iratco-invivo.streamlit.app/
""")
