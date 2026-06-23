import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("🧪 OECD Clinical Observation Input")

# =========================
# STUDY TYPE
# =========================
study_type = st.selectbox(
    "Study Type",
    ["Acute", "Subchronic", "Chronic"]
)

# =========================
# TIMEPOINT
# =========================
if study_type == "Acute":

    times = [
        "30m", "1h", "2h", "4h",
        "12h", "16h", "20h", "24h"
    ] + [f"D{i}" for i in range(2,15)]

elif study_type == "Subchronic":

    times = [
        "30m", "1h", "2h", "4h",
        "12h", "16h", "20h", "24h"
    ] + [f"D{i}" for i in range(2,119)]

else:  # Chronic

    times = [
        "30m", "1h", "2h", "4h",
        "12h", "16h", "20h", "24h"
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
# =========================
# SPLIT PER 30 HARI
# =========================
early_times = ["30m","1h","2h","4h","12h","16h","20h","24h"]

day_times = [
    t for t in times
    if t.startswith("D")
]

time_chunks = []

# early chunk
if len(early_times) > 0:
    time_chunks.append(early_times)

# 30 hari per chunk
for start in range(0, len(day_times), 30):

    chunk = day_times[start:start+30]

    time_chunks.append(chunk)

# =========================
# LOOP HEATMAP
# =========================
for chunk_idx, chunk_times in enumerate(time_chunks):

    # =========================
    # TITLE
    # =========================
    if chunk_idx == 0:

        title_text = "24h Observation"

    else:

        title_text = (
            f"{chunk_times[0]} - "
            f"{chunk_times[-1]}"
        )

    st.markdown(f"### 🔥 {title_text}")

    # =========================
    # MATRIX
    # =========================
    heat_data = df_heat[
        chunk_times
    ].values

    # =========================
    # FIGURE
    # =========================
    fig, ax = plt.subplots(
        figsize=(16,6),
        dpi=150
    )

    im = ax.imshow(
        heat_data,
        aspect='auto'
    )

    # =========================
    # COLOR
    # =========================
    from matplotlib.colors import ListedColormap

    cmap = ListedColormap([
        "green",
        "red"
    ])

    im.set_cmap(cmap)

    # =========================
    # CUSTOM X LABEL
    # =========================
    xtick_pos = []
    xtick_lab = []

    for i, t in enumerate(chunk_times):

        # 24h
        if t == "24h":

            xtick_pos.append(i)
            xtick_lab.append("24h")

        # day
        elif t.startswith("D"):

            day_num = int(
                t.replace("D","")
            )

            # subchronic
            if study_type == "Subchronic":

                if (
                    day_num == 1 or
                    day_num % 5 == 0
                ):

                    xtick_pos.append(i)
                    xtick_lab.append(
                        str(day_num)
                    )

            # chronic
            else:

                if (
                    day_num == 1 or
                    day_num % 5 == 0
                ):

                    xtick_pos.append(i)
                    xtick_lab.append(
                        str(day_num)
                    )

    # apply
    ax.set_xticks(xtick_pos)

    ax.set_xticklabels(
        xtick_lab,
        rotation=45,
        fontsize=8
    )

    # =========================
    # Y LABEL
    # =========================
    ax.set_yticks(
        np.arange(len(df_heat))
    )

    ax.set_yticklabels(
        df_heat["Kategori"]
        + " - "
        + df_heat["Parameter"]
    )

    ax.set_title(
        f"Clinical Observation Heatmap\n{title_text}"
    )

    # =========================
    # GRID
    # =========================
    ax.set_xticks(
        np.arange(-.5, len(chunk_times), 1),
        minor=True
    )

    ax.set_yticks(
        np.arange(-.5, len(df_heat), 1),
        minor=True
    )

    ax.grid(
        which="minor",
        color="gray",
        linestyle='-',
        linewidth=0.2
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)

# =========================
# TEXT TABLE PER 30 HARI
# =========================
for chunk_idx, chunk_times in enumerate(time_chunks):

    # =========================
    # TITLE
    # =========================
    if chunk_idx == 0:

        title_text = "24h Observation"

    else:

        title_text = (
            f"{chunk_times[0]} - "
            f"{chunk_times[-1]}"
        )

    st.markdown(f"### 📋 {title_text}")

    # =========================
    # FIGURE
    # =========================
    fig2, ax = plt.subplots(
        figsize=(16,6),
        dpi=150
    )

    ax.set_xlim(
        -0.5,
        len(chunk_times)-0.5
    )

    ax.set_ylim(
        len(df_heat)-0.5,
        -0.5
    )

    # =========================
    # TEXT LOOP
    # =========================
    for i in range(df_heat.shape[0]):

        for j in range(len(chunk_times)):

            raw_val = str(
                edited.iloc[i][chunk_times[j]]
            ).strip().upper()

            if raw_val == "T":

                display_val = "T"
                color = "red"

            else:

                display_val = "TT"
                color = "green"

            ax.text(
                j,
                i,
                display_val,
                ha='center',
                va='center',
                fontsize=7,
                fontweight='bold',
                color=color
            )

    # =========================
    # X LABEL
    # =========================
    xtick_pos = []
    xtick_lab = []
    
    for i, t in enumerate(chunk_times):
    
        # =========================
        # EARLY TIMEPOINT
        # =========================
        if t in [
            "30m","1h","2h","4h",
            "12h","16h","20h","24h"
        ]:
    
            xtick_pos.append(i)
            xtick_lab.append(t)
    
        # =========================
        # DAY TIMEPOINT
        # =========================
        elif t.startswith("D"):
    
            day_num = int(
                t.replace("D","")
            )
    
            # subchronic
            if study_type == "Subchronic":
    
                if (
                    day_num == 1 or
                    day_num % 5 == 0
                ):
    
                    xtick_pos.append(i)
                    xtick_lab.append(
                        str(day_num)
                    )
    
            # chronic
            else:
    
                if (
                    day_num == 1 or
                    day_num % 5 == 0
                ):
    
                    xtick_pos.append(i)
                    xtick_lab.append(
                        str(day_num)
                    )
    
    # apply
    ax.set_xticks(xtick_pos)
    
    ax.set_xticklabels(
        xtick_lab,
        rotation=45,
        fontsize=8
    )

    # =========================
    # Y LABEL
    # =========================
    ax.set_yticks(
        np.arange(len(df_heat))
    )

    ax.set_yticklabels(
        df_heat["Kategori"]
        + " - "
        + df_heat["Parameter"]
    )

    # =========================
    # GRID
    # =========================
    ax.set_xticks(
        np.arange(-.5, len(chunk_times), 1),
        minor=True
    )

    ax.set_yticks(
        np.arange(-.5, len(df_heat), 1),
        minor=True
    )

    ax.grid(
        which="minor",
        color="gray",
        linestyle='-',
        linewidth=0.2
    )

    ax.set_title(
        f"Clinical Observation Table\n{title_text}"
    )

    plt.tight_layout()

    st.pyplot(fig2)

    plt.close(fig2)
