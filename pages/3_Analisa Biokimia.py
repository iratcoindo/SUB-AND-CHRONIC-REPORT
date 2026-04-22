import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy import stats
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scikit_posthocs as sp
import pingouin as pg

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="iRATco Platform",
    page_icon="logo.png",
    layout="wide"
)

# =========================
# USER DATA
# =========================
USERS = {
    "admin": "iratcolab1",
    "lab": "iratcolab5"
}

# =========================
# SESSION INIT
# =========================
st.session_state.setdefault("authenticated", False)

# =========================
# LOGIN PAGE
# =========================
if not st.session_state.authenticated:

    # 🔒 HIDE SIDEBAR
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([7,2])

    with col1:
        st.markdown("""
        <h1 style="color:#4b5563;">🔒 Login to: iRATco Sci Data Analysis Platform</h1>
        <div style="color:#9ca3af;">
        Advanced Laboratory Analysis Platform
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.image("logo_iratco.png", width=230)

    # 🔥 FORM (STABIL)
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if username in USERS and USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.stop()   # 🔥 INI KUNCINYA

# ===============================
# HEADER
# ===============================
col1, col2 = st.columns([8,2])
with col1:
    st.title("📊 Barplot Analysis")
with col2:
    st.image("logo_iratco.png", width=250)

# ===============================
# STYLE
# ===============================
def apply_prism_style():
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "black",
        "axes.linewidth": 1.5,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans"]
    })

def get_palette(name, n):
    palettes = {
        "Prism": ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B2","#937860","#DA8BC3"],
        "JCO": ["#0073C2","#EFC000","#868686","#CD534C","#7AA6DC","#003C67","#8F7700"],
        "NPG": ["#E64B35","#4DBBD5","#00A087","#3C5488","#F39B7F","#8491B4","#91D1C2"],
        "Lancet": ["#00468B","#ED0000","#42B540","#0099B4","#925E9F","#FDAF91","#AD002A"],
        "AAAS": ["#3B4992","#EE0000","#008B45","#631879","#008280","#BB0021","#5F559B"],
        "BW": ["#000000", "#444444", "#777777", "#AAAAAA", "#CCCCCC"],
        "All Black": ["#000000", "#000000", "#000000", "#000000", "#000000"],
        "All Gray": ["#CCCCCC", "#CCCCCC", "#CCCCCC", "#CCCCCC", "#CCCCCC"],
        "iRATco Style": ["#0073C2", "#E63946", "#2A9D8F", "#F4A261", "#6A4C93", "#264653", "#8D99AE"]
    }

    base = palettes.get(name, palettes["Prism"])
    return [base[i % len(base)] for i in range(n)]

# ===============================
# HELPER
# ===============================
def p_to_star(p):
    try:
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
    except:
        return ""

def format_p(p):
    try:
        if p < 0.0001:
            return "p < 0.0001"
        elif p < 0.001:
            return f"p = {p:.3e}"
        else:
            return f"p = {p:.4f}"
    except:
        return "p = NA"

# ===============================
# INIT SESSION STATE
# ===============================
if "groups" not in st.session_state:
    st.session_state.groups = [{"name": "Group 1", "data": ""}]

# 🔥 FIX STRUCTURE (penting untuk multipage)
for i, g in enumerate(st.session_state.groups):
    if "data" not in g:
        combined = []
        if "subgroups" in g:
            for sub in g["subgroups"]:
                if sub.get("data"):
                    combined.append(sub["data"])

        st.session_state.groups[i] = {
            "name": g.get("name", f"Group {i+1}"),
            "data": " ".join(combined)
        }

# ===============================
# INPUT UI
# ===============================
if st.button("➕ Add Group"):
    st.session_state.groups.append({
        "name": f"Group {len(st.session_state.groups)+1}",
        "data": ""
    })

all_data = []

for i, g in enumerate(st.session_state.groups):

    st.markdown(f"### Group {i+1}")
    col1, col2 = st.columns([1,2])

    with col1:
        name = st.text_input("Name", g["name"], key=f"name{i}")
    with col2:
        data = st.text_area("Data (contoh: 10 11 12)", g["data"], key=f"data{i}")

    st.session_state.groups[i]["name"] = name
    st.session_state.groups[i]["data"] = data

    if data.strip():
        try:
            vals = [float(x) for x in data.split()]
            for v in vals:
                all_data.append({"Group": name, "Value": v})
        except:
            st.error(f"Error in group {i+1}")

# ===============================
# ANALYSIS
# ===============================
if all_data:

    df = pd.DataFrame(all_data)

    group_order = [g["name"] for g in st.session_state.groups if g["data"].strip()]
    df["Group"] = pd.Categorical(df["Group"], categories=group_order, ordered=True)

    st.dataframe(df, use_container_width=True)

    grouped = df.groupby("Group")["Value"]
    group_values = [grouped.get_group(g).values for g in group_order]

    # ===============================
    # NORMALITY (SHAPIRO-WILK)
    # ===============================
    st.markdown("### 🧪 Normality Test (Shapiro-Wilk)")

    normality_results = []
    normal_flags = []

    for g in group_order:
        values = grouped.get_group(g)

        stat, p = stats.shapiro(values)

        normal = p > 0.05
        normal_flags.append(normal)

        normality_results.append({
            "Group": g,
            "W statistic": round(stat, 4),
            "p-value": round(p, 4),
            "Normal": "Normal" if normal else "Not Normal"
        })

    normality_df = pd.DataFrame(normality_results)
    st.dataframe(normality_df, use_container_width=True)

    all_normal = all(normal_flags)

    # ===============================
    # VARIANCE
    # ===============================
    st.markdown("### ⚖️ Variance Homogeneity Test")

    if len(group_values) == 2:
        # F-test
        var1 = np.var(group_values[0], ddof=1)
        var2 = np.var(group_values[1], ddof=1)

        F = var1 / var2 if var1 > var2 else var2 / var1

        # pendekatan kasar (rule of thumb)
        var_equal = F < 4

        st.write(f"F statistic: {round(F,4)}")
        st.write(f"Equal variance: {'Equal' if var_equal else 'Unequal'}")

    else:
        # Bartlett test
        stat, p = stats.bartlett(*group_values)

        var_equal = p > 0.05

        st.write(f"Bartlett statistic: {round(stat,4)}")
        if p < 0.0001:
            st.write("p-value: < 0.0001")
        else:
            st.write(f"p-value: {round(p,4)}")
        st.write(f"Equal variance: {'Equal' if var_equal else 'Unequal'}")

    # ===============================
    # TEST SELECTION
    # ===============================
    k = len(group_values)

    if k == 2:
        if all_normal and var_equal:
            test = "t-test"
            stat, p_value = stats.ttest_ind(*group_values)
        elif all_normal:
            test = "Welch t-test"
            stat, p_value = stats.ttest_ind(*group_values, equal_var=False)
        else:
            test = "Mann-Whitney"
            stat, p_value = stats.mannwhitneyu(*group_values)
        posthoc_df = None

    else:
        if all_normal and var_equal:
            test = "ANOVA"
            stat, p_value = stats.f_oneway(*group_values)
            posthoc = pairwise_tukeyhsd(df["Value"], df["Group"])
            posthoc_df = pd.DataFrame(data=posthoc.summary().data[1:], columns=posthoc.summary().data[0])

        elif all_normal:
            test = "Welch ANOVA"
            res = pg.welch_anova(dv="Value", between="Group", data=df)

            # aman untuk berbagai versi / kondisi
            if "p-unc" in res.columns:
                p_value = res["p-unc"].values[0]
            elif "p-uncorrected" in res.columns:
                p_value = res["p-uncorrected"].values[0]
            else:
                st.warning("Welch ANOVA gagal, fallback ke Kruskal")
                stat, p_value = stats.kruskal(*group_values)
                test = "Kruskal Wallis"
            posthoc_df = pg.pairwise_gameshowell(dv="Value", between="Group", data=df)

        else:
            test = "Kruskal Wallis"
            stat, p_value = stats.kruskal(*group_values)
            posthoc_df = sp.posthoc_dunn(df, val_col="Value", group_col="Group", p_adjust="fdr_bh")

    st.write(f"### 🧠 Test Used: {test}")
    st.write(f"p-value: {round(p_value,5)}")
    
    if posthoc_df is not None: 
        # ===============================
        # AUTO LABEL POSTHOC TEST
        # ===============================
        if test == "ANOVA":
            posthoc_label = "Tukey HSD"
        elif test == "Welch ANOVA":
            posthoc_label = "Games-Howell"
        elif test == "Kruskal Wallis":
            posthoc_label = "Dunn Test"
        elif test in ["t-test", "Welch t-test", "Mann-Whitney"]:
            posthoc_label = "Pairwise Comparison"
        else:
            posthoc_label = "Post-hoc"
        
        st.write(f"### 📌 Post-hoc Result ({posthoc_label})")
        # ===============================
        # GANTI HEDGES → P.SIGNIF
        # ===============================
        df_posthoc = posthoc_df.copy()
        
        if "pval" in df_posthoc.columns:
            df_posthoc["pval"] = pd.to_numeric(df_posthoc["pval"], errors="coerce")
            df_posthoc["p.signif"] = df_posthoc["pval"].apply(p_to_star)
        
            # 🔥 hapus kolom hedges
            if "hedges" in df_posthoc.columns:
                df_posthoc = df_posthoc.drop(columns=["hedges"])
        
        st.dataframe(df_posthoc, use_container_width=True)

    # ===============================
    # PLOT
    # ===============================
    st.markdown("### 📈 Boxplot")
    
    # ===============================
    # 🎨 COLOR PALETTE
    # ===============================
    palette_name = st.radio(
        "🎨 Color Palette",
        ["Prism", "JCO", "NPG", "Lancet", "AAAS", "BW", "All Black", "All Gray", "iRATco Style"],
        horizontal=True
    )
    
    apply_prism_style()
    
    means = grouped.mean()
    stds = grouped.std()
    ns = grouped.count()
    ses = stds / np.sqrt(ns)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        error_type = st.selectbox("Error Bar", ["SD", "SE"])
    with col2:
        y_min_input = st.number_input("Y min", value=0.0)
    with col3:
        y_max_input = st.number_input("Y max", value=100.0)
    
    errors = stds if error_type == "SD" else ses
    
    colors = get_palette(palette_name, len(group_order))
    x = np.arange(len(group_order))
    
    fig, ax = plt.subplots()
    
    # ===============================
    # BOXPLOT
    # ===============================
    box_data = [grouped.get_group(g).values for g in group_order]
    
    bp = ax.boxplot(
        box_data,
        patch_artist=True,
        widths=0.6,
        showfliers=False
    )
    
    # warna tiap box
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor("black")
        patch.set_linewidth(1.5)
    
    # garis median
    for median in bp['medians']:
        median.set_color("black")
        median.set_linewidth(2)
    
    # ===============================
    # JITTER SCATTER
    # ===============================
    for i, g in enumerate(group_order):
        y = grouped.get_group(g)
        jitter = np.random.normal(i+1, 0.04, size=len(y))
    
        ax.scatter(
            jitter,
            y,
            color="gray",
            s=15,
            alpha=0.6
        )
    
    # ===============================
    # AXIS
    # ===============================
    ax.set_xticks(np.arange(1, len(group_order)+1))
    ax.set_xticklabels(group_order, rotation=45, ha='right')
    
    # ===============================
    # INPUT USER
    # ===============================
    col1, col2, col3 = st.columns(3)
    x_label = col1.text_input("X-axis Label", "X Label")
    y_label = col2.text_input("Y-axis Label", "Y Label")
    
    ref_group = col3.selectbox(
        "Ref. Group",
        group_order
    )
    
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_ylim(y_min_input, y_max_input)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # ===============================
    # GLOBAL TEXT
    # ===============================
    y_max = df["Value"].max()
    y_range = y_max - df["Value"].min()
    
    ax.text(
        ax.get_xlim()[0],
        y_max + y_range*0.2,
        f"{test}, {format_p(p_value)}",
        fontsize=12,
        fontweight='bold'
    )
    
    # ===============================
    # SIGNIFICANCE vs REFERENCE
    # ===============================
    if posthoc_df is not None:
    
        for i, g in enumerate(group_order):
    
            if g == ref_group:
                continue
    
            row = None
    
            if "group1" in posthoc_df.columns:
                row = posthoc_df[
                    ((posthoc_df["group1"] == ref_group) & (posthoc_df["group2"] == g)) |
                    ((posthoc_df["group2"] == ref_group) & (posthoc_df["group1"] == g))
                ]
                p_col = "p-adj"
    
            elif "A" in posthoc_df.columns:
                row = posthoc_df[
                    ((posthoc_df["A"] == ref_group) & (posthoc_df["B"] == g)) |
                    ((posthoc_df["B"] == ref_group) & (posthoc_df["A"] == g))
                ]
                p_col = "pval"
    
            else:
                try:
                    p_val = posthoc_df.loc[ref_group, g]
                except:
                    continue
    
                star = p_to_star(p_val)
    
                y_data_max = max(means + errors)
                y_text = y_data_max + y_range * 0.2
                y_star = (y_data_max + y_text) / 2
    
                ax.text(i+1, y_star, star, ha='center', va='center',
                        fontsize=13, fontweight='bold')
                continue
    
            if row is None or row.empty:
                continue
    
            p_val = float(row[p_col].values[0])
            star = p_to_star(p_val)
    
            y_data_max = max(means + errors)
            y_text = y_data_max + y_range * 0.2
            y_star = (y_data_max + y_text) / 2
    
            ax.text(
                i+1,
                y_star,
                star,
                ha='center',
                va='center',
                fontsize=13,
                fontweight='bold'
            )
    
    st.pyplot(fig)
# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown("""
© 2026 Mawar Subangkit  
iRATco Statistical Software
""")
