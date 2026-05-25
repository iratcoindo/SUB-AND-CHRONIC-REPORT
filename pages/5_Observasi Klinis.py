import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("🧪 OECD Clinical Observation Input")

# =========================
# STUDY TYPE
# =========================
study_type = st.selectbox(
    "Study Type",
    ["Subchronic", "Chronic"]
)

# =========================
# TIMEPOINT
# =========================
if study_type == "Subchronic":

    times = [
        "30m","1h","2h","4h","12h","16h","20h","24h"
    ] + [f"D{i}" for i in range(2,119)]

else:

    times = [
        "30m","1h","2h","4h","12h","16h","20h","24h"
    ] + [f"D{i}" for i in range(2,299)]

# =========================
# SHOW
# =========================
st.write(f"Total Timepoints: {len(times)}")

selected_time = st.selectbox(
    "Select Timepoint",
    times
)

# =========================
# PARAMETER MASTER (FIX)
# =========================
params = [
    ("Mata","Refleks kornea","Kedip melambat/asimetris/hilang"),
    ("Mata","Pupil konstriksi & dilatasi","Lambat/asimetris/tidak ada"),
    ("Mata","Lakrimasi","Ada lakrimasi berlebih / mata basah jelas"),
    ("Mata","Discharge okular","Ada sekret (jenis & jumlah) atau krusta"),
    ("Mata","Konjungtiva","Hiperemia/edema; blefarospasme"),

    ("Rambut","Grooming","Grooming menurun; rambut kusam/kotor; piloereksi menetap"),
    ("Rambut","Alopecia/ruffled fur","Ada alopecia"),

    ("Kulit","Eritema/lesi","Ada eritema/lesi/ulkus/nekrosis"),

    ("Membran mukosa","Warna mukosa","Pucat/sianosis/ikterus"),

    ("Sistem pernafasan","Pola napas","Takipnea/bradipnea, dyspnea"),
    ("Sistem pernafasan","Nasal discharge","Ada sekresi (jenis/warna)"),

    ("Saraf otonom","Salivasi","Hipersalivasi/drooling"),
    ("Saraf otonom","Piloereksi","Ada piloereksi menetap/berulang"),

    ("Saraf pusat","Tremor","Ada tremor"),
    ("Saraf pusat","Kejang","Ada kejang"),
    ("Saraf pusat","Sedasi/letargi","Letargi/sedasi"),

    ("Aktivitas somatomotor","Gait/cara jalan","Ataksia/tidak mampu berjalan"),
    ("Aktivitas somatomotor","Righting reflex","Lambat/gagal"),

    ("Tingkah laku","Perilaku umum","Pasif ekstrem, agresif ekstrem"),
    ("Tingkah laku","Tingkah laku aneh","Ada perilaku aneh"),

    ("Sekresi/ekskresi","Feses (diare)","Lembek/diare cair/mukus/darah"),
    ("Sekresi/ekskresi","Urinasi","Anuria; hematuria"),

    ("Nafsu makan","Nafsu makan","Menurun nyata / tidak makan"),

    ("Kondisi umum","Lemas/tidur abnormal","Lemas jelas/prostration"),
    ("Kondisi umum","Koma","Ada (severe/endpoint)")
]

# =========================
# BUILD TABLE
# =========================
data = []

for cat, sub, desc in params:
    row = {
        "Kategori": cat,
        "Parameter": sub,
        "Abnormal": desc
    }
    for t in times:
        row[t] = ""
    data.append(row)

df = pd.DataFrame(data)

# =========================
# DATA EDITOR
# =========================
edited = st.data_editor(
    df,
    use_container_width=True,
    num_rows="fixed",
    column_config={
        "Kategori": st.column_config.TextColumn(disabled=True),
        "Parameter": st.column_config.TextColumn(disabled=True),
        "Abnormal": st.column_config.TextColumn(disabled=True),
    }
)

# =========================
# DOWNLOAD
# =========================
st.download_button(
    "⬇️ Download Data",
    edited.to_csv(index=False).encode("utf-8"),
    "clinical_observation.csv",
    "text/csv"
)

# =========================
# HEATMAP (TT = HIJAU, T = MERAH)
# =========================
import numpy as np
import matplotlib.pyplot as plt

st.markdown("## 🔥 Heatmap Observasi")

# copy data
df_heat = edited.copy()

# convert TT/T → numeric
# =========================
# CLEAN + CONVERT (FIX ERROR)
# =========================
for t in times:
    df_heat[t] = (
        df_heat[t]
        .astype(str)              # paksa string
        .str.strip()              # hilangkan spasi
        .str.upper()              # kapital
        .map({" ": 0, "T": 1})   # mapping
        .fillna(0)                # selain itu → 0
        .astype(float)            # paksa numeric
    )

# ambil matrix
heat_data = df_heat[times].values

# ambil matrix saja
heat_data = df_heat[times].values

# plot
fig, ax = plt.subplots(figsize=(12,6), dpi=150)

im = ax.imshow(heat_data, aspect='auto')

# custom colormap (hijau → merah)
from matplotlib.colors import ListedColormap
cmap = ListedColormap(["green", "red"])
im.set_cmap(cmap)

# label
ax.set_xticks(np.arange(len(times)))
ax.set_xticklabels(times, rotation=45)

ax.set_yticks(np.arange(len(df_heat)))
ax.set_yticklabels(df_heat["Kategori"] + " - " + df_heat["Parameter"])

ax.set_title("Clinical Observation Heatmap")

# grid biar rapi
ax.set_xticks(np.arange(-.5, len(times), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(df_heat), 1), minor=True)
ax.grid(which="minor", color="gray", linestyle='-', linewidth=0.2)


plt.tight_layout()

st.pyplot(fig)
plt.close(fig)

# =========================
# TEXT MATRIX (NO HEATMAP)
# =========================
fig2, ax = plt.subplots(figsize=(12,6), dpi=150)

# kosongkan background
ax.set_xlim(-0.5, len(times)-0.5)
ax.set_ylim(len(df_heat)-0.5, -0.5)

# =========================
# TULIS TEXT TT / T
# =========================
for i in range(df_heat.shape[0]):
    for j in range(len(times)):

        raw_val = str(edited.iloc[i][times[j]]).strip().upper()

        # LOGIKA BARU
        if raw_val == "T":
            display_val = "T"
            color = "red"
        else:
            display_val = "TT"
            color = "green"

        ax.text(
            j, i,
            display_val,   # 🔥 pakai ini, bukan val
            ha='center',
            va='center',
            fontsize=7,
            fontweight='bold',
            color=color
        )

# =========================
# AXIS LABEL
# =========================
ax.set_xticks(np.arange(len(times)))
ax.set_xticklabels(times, rotation=45)

ax.set_yticks(np.arange(len(df_heat)))
ax.set_yticklabels(df_heat["Kategori"] + " - " + df_heat["Parameter"])

# =========================
# GRID (BIAR KAYA TABLE)
# =========================
ax.set_xticks(np.arange(-.5, len(times), 1), minor=True)
ax.set_yticks(np.arange(-.5, len(df_heat), 1), minor=True)
ax.grid(which="minor", color="gray", linestyle='-', linewidth=0.2)

ax.set_title("Clinical Observation Table")

plt.tight_layout()

st.pyplot(fig2)
plt.close(fig2)
