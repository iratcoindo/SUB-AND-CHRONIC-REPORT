import numpy as np
import pandas as pd
import streamlit as st

from scipy.stats import mannwhitneyu

st.markdown("## 📋 Input Data Organ & Berat Badan")

# =========================
# SETUP STRUKTUR
# =========================
doses = [5, 50, 300, 2000, 5000]
rows_per_dose = 5

dose_list = []
animal_ids = []

for d in doses:
    for i in range(1, rows_per_dose+1):
        dose_list.append(d)
        animal_ids.append(i)

n_rows = len(dose_list)

# =========================
# TEMPLATE DATAFRAME
# =========================
df_input = pd.DataFrame({
    "Dose (mg/kgBB)": dose_list,
    "ID Hewan": animal_ids,
    "Jantung": [None]*n_rows,
    "Paru-paru": [None]*n_rows,
    "Hati": [None]*n_rows,
    "Ginjal Kanan": [None]*n_rows,
    "Ginjal Kiri": [None]*n_rows,
    "Limpa": [None]*n_rows,
    "Berat Badan": [None]*n_rows
})

# =========================
# DATA EDITOR (LOCK COLUMN)
# =========================
edited_df = st.data_editor(
    df_input,
    num_rows="fixed",
    use_container_width=True,
    column_config={
        "Dose (mg/kgBB)": st.column_config.NumberColumn(
            "Dose (mg/kgBB)",
            disabled=True
        ),
        "ID Hewan": st.column_config.NumberColumn(
            "ID Hewan",
            disabled=True
        )
    }
)

st.markdown("## ⚖️ Relative Organ Weight (%BB)")

organs = [ "Jantung", "Paru-paru","Hati", "Ginjal Kanan", "Ginjal Kiri","Limpa" ]

df_calc = edited_df.copy()

# convert ke numeric
for col in ["Berat Badan"] + organs:
    df_calc[col] = pd.to_numeric(df_calc[col], errors="coerce")

# hitung %
for organ in organs:
    df_calc[f"{organ} (%)"] = (df_calc[organ] / df_calc["Berat Badan"]) * 100

st.dataframe(df_calc, use_container_width=True)

st.markdown("## 📊 Summary (Mean ± SD per Dose)")

summary_table = []

# reference dose (control)
control_dose = min(df_calc["Dose (mg/kgBB)"].dropna().unique())

for d in sorted(df_calc["Dose (mg/kgBB)"].unique()):

    row = {"Kelompok": f"{int(d)} mg/kg BB"}

    for organ in organs:

        vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna()

        mean = np.mean(vals)
        std = np.std(vals)

        text = f"{mean:.2f} ± {std:.2f}"

        # =========================
        # SIGNIFICANCE vs CONTROL
        # =========================
        if d != control_dose:

            control_vals = df_calc[df_calc["Dose (mg/kgBB)"] == control_dose][f"{organ} (%)"].dropna()

            if len(vals) > 1 and len(control_vals) > 1:
                _, p = mannwhitneyu(control_vals, vals)

                if p >= 0.05:
                    text += " ns"
                else:
                    text += " *"

        row[organ] = text

    summary_table.append(row)

df_summary = pd.DataFrame(summary_table)

st.dataframe(df_summary, use_container_width=True)

from scipy.stats import kruskal, mannwhitneyu

st.markdown("## 📈 Statistical Analysis")

control_dose = min(df_calc["Dose (mg/kgBB)"].dropna().unique())
st.write(f"Reference (control): {control_dose} mg/kgBB")

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

for organ in organs:

    st.markdown(f"### {organ}")

    groups_data = []
    dose_labels = []

    for d in sorted(df_calc["Dose (mg/kgBB)"].unique()):
        vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna()

        if len(vals) > 0:
            groups_data.append(vals)
            dose_labels.append(d)

    if len(groups_data) >= 2:

        H, p_kw = kruskal(*groups_data)
        kruskal_p = p_kw
        st.write(f"Kruskal-Wallis p = {p_kw:.4f}")

        results = []

        control_vals = df_calc[df_calc["Dose (mg/kgBB)"] == control_dose][f"{organ} (%)"].dropna()

        for d in dose_labels:
            if d == control_dose:
                continue

            test_vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna()

            if len(control_vals) > 1 and len(test_vals) > 1:
                _, p = mannwhitneyu(control_vals, test_vals)

                results.append({
                    "Dose": d,
                    "p-value": round(p,4),
                    "Significance": get_significance(p)
                })

                signif_dict = {r["Dose"]: r["Significance"] for r in results}

        st.dataframe(pd.DataFrame(results))

import matplotlib.pyplot as plt
from scipy.stats import pearsonr

st.markdown("## 📉 OECD Style Plot")

from scipy.stats import pearsonr

for organ in organs:

    st.markdown(f"### {organ}")

    fig, ax = plt.subplots(figsize=(4,3.5), dpi=500)

    means = []
    stds = []
    doses_sorted = sorted(df_calc["Dose (mg/kgBB)"].unique())

    for d in doses_sorted:
        vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna()

        means.append(np.mean(vals))
        stds.append(np.std(vals))

    x = np.arange(len(doses_sorted))

    # =========================
    # STATISTICS PER ORGAN (WAJIB DI SINI)
    # =========================
    groups_data = []
    dose_labels = []
    
    for d in doses_sorted:
        vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna()
        if len(vals) > 0:
            groups_data.append(vals)
            dose_labels.append(d)
    
    # Kruskal
    if len(groups_data) >= 2:
        H, kruskal_p = kruskal(*groups_data)
    else:
        kruskal_p = np.nan
    
    # Pairwise vs control
    control_dose = min(doses_sorted)
    control_vals = df_calc[df_calc["Dose (mg/kgBB)"] == control_dose][f"{organ} (%)"].dropna()
    
    signif_dict = {}
    
    for d in dose_labels:
        if d == control_dose:
            continue
    
        test_vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna()
    
        if len(control_vals) > 1 and len(test_vals) > 1:
            _, p = mannwhitneyu(control_vals, test_vals)
            signif_dict[d] = get_significance(p)
        else:
            signif_dict[d] = "ns"

    
    # =========================
    # PLOT
    # =========================
    ax.errorbar(
        x,
        means,
        yerr=stds,
        fmt='o-',
        capsize=5
    )

    # =========================
    # ADD SIGNIFICANCE LABEL
    # =========================
    for i, d in enumerate(doses_sorted):
    
        if d == control_dose:
            continue
    
        signif = signif_dict.get(d, "ns")
    
        
        ax.text(
            x[i],
            means[i] + stds[i] + 0.02 * max(means),
            signif,
            ha='center',
            va='bottom',
            fontsize=10
        )

    # =========================
    # JITTER RAW DATA
    # =========================
    for i, d in enumerate(doses_sorted):
    
        vals = df_calc[df_calc["Dose (mg/kgBB)"] == d][f"{organ} (%)"].dropna().values
    
        if len(vals) > 0:
    
            # jitter posisi x
            x_jitter = np.random.normal(loc=x[i], scale=0.05, size=len(vals))
    
            ax.scatter(
                x_jitter,
                vals,
                s=20,
                alpha=0.7,        # 🔥 RECOMMENDED
                color="gray",
                edgecolors="none"
            )

    # =========================
    # R² (GGpubr STYLE)
    # =========================
    x_num = np.array(doses_sorted, dtype=float)
    y_num = np.array(means, dtype=float)

    mask = ~np.isnan(x_num) & ~np.isnan(y_num)

    if np.sum(mask) > 1 and len(np.unique(y_num[mask])) > 1:
        r, p_val = pearsonr(x_num[mask], y_num[mask])
        r2 = r**2

        label = f"Kruskal p = {kruskal_p:.3f}\nR² = {r2:.3f}"

        ax.text(
            0.05, 1.2,
            label,
            transform=ax.transAxes,
            verticalalignment='top',
            fontsize=10,
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
        )

    # =========================
    # AXIS
    # =========================
    ax.set_xticks(x)
    ax.set_xticklabels(doses_sorted)
    ax.set_xlabel("Dosis (mg/kgBB)")
    ax.set_ylabel(f"{organ} (%BB)")

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    
