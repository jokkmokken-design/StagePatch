import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import os 

st.set_page_config(page_title="StagePatch", layout="wide") 

# --- SIDOMENY: GIG & DATABAS ---
st.sidebar.header("🎸 Gig & Inställningar")
gig_namn = st.sidebar.text_input("Namn på Gig/Band:", placeholder="T.ex. Sommarfestivalen 2026")

st.sidebar.divider()

st.sidebar.header("📁 Din Micklåda (Databas)")

DEFAULT_DB_PATH = "databas.xlsx"
standard_mics = {}

if os.path.exists(DEFAULT_DB_PATH):
    try:
        db_df = pd.read_excel(DEFAULT_DB_PATH)
        for index, row in db_df.iterrows():
            m = str(row["Mic"]) if pd.notna(row["Mic"]) else ""
            s = str(row["Stativ"]) if pd.notna(row["Stativ"]) else "Inget"
            standard_mics[str(row["Instrument"])] = {"Mic": m, "Stativ": s}
        st.sidebar.success("✅ Laddade micklåda från fil!")
    except:
        pass

if not standard_mics:
    template_data = {
        "Instrument": ["Kick In", "Kick Out", "Snare Top", "Bass DI", "Vocal Center"],
        "Mic": ["Shure Beta 91", "Audix D6", "Shure SM57", "Radial J48", "Shure Beta 58"],
        "Stativ": ["Inget", "Very Short", "Short", "Inget", "Tall"]
    }
    for i in range(len(template_data["Instrument"])):
        inst = template_data["Instrument"][i]
        standard_mics[inst] = {"Mic": template_data["Mic"][i], "Stativ": template_data["Stativ"][i]}

stativ_val = ["Tall", "Short", "Very Short", "Flat", "Inget"]
instrument_lista = list(standard_mics.keys())

uppladdad_fil = st.sidebar.file_uploader("Uppdatera micklådan tillfälligt:", type=["xlsx"])
if uppladdad_fil is not None:
    db_df = pd.read_excel(uppladdad_fil)
    standard_mics = {} 
    for index, row in db_df.iterrows():
        m = str(row["Mic"]) if pd.notna(row["Mic"]) else ""
        s = str(row["Stativ"]) if pd.notna(row["Stativ"]) else "Inget"
        standard_mics[str(row["Instrument"])] = {"Mic": m, "Stativ": s}
    instrument_lista = list(standard_mics.keys())

# --- APPENS MINNE ---
if "patch_list" not in st.session_state:
    st.session_state["patch_list"] = []
if "success_msg" not in st.session_state:
    st.session_state["success_msg"] = ""

if "vald_inst" not in st.session_state or st.session_state["vald_inst"] not in instrument_lista:
    if instrument_lista:
        st.session_state["vald_inst"] = instrument_lista[0]
        on_inst_change_logic = standard_mics[instrument_lista[0]]
        st.session_state["vald_mic"] = on_inst_change_logic["Mic"]
        st.session_state["vald_stativ"] = on_inst_change_logic["Stativ"] if on_inst_change_logic["Stativ"] in stativ_val else stativ_val[0]

def on_inst_change():
    inst = st.session_state["vald_inst"]
    st.session_state["vald_mic"] = standard_mics[inst]["Mic"]
    s = standard_mics[inst]["Stativ"]
    st.session_state["vald_stativ"] = s if s in stativ_val else stativ_val[0]

def lagg_till_kanal(ny_box):
    inst = st.session_state["vald_inst"]
    mic = st.session_state["vald_mic"]
    stativ = st.session_state["vald_stativ"]
    knr = len(st.session_state["patch_list"]) + 1 
    st.session_state["patch_list"].append({
        "Kanal": knr, "Instrument": inst, "Mic/DI": mic, "Stativ": stativ, "Stagebox": ny_box 
    })
    idx = instrument_lista.index(inst)
    n_idx = (idx + 1) % len(instrument_lista)
    n_inst = instrument_lista[n_idx]
    st.session_state["vald_inst"] = n_inst
    st.session_state["vald_mic"] = standard_mics[n_inst]["Mic"]
    s = standard_mics[n_inst]["Stativ"]
    st.session_state["vald_stativ"] = s if s in stativ_val else stativ_val[0]
    st.session_state["success_msg"] = f"{inst} tillagd!"

def update_table():
    edits = st.session_state["patch_editor"].get("edited_rows", {})
    for idx_str, data in edits.items():
        idx = int(idx_str)
        for col, val in data.items():
            st.session_state["patch_list"][idx][col] = val

# --- HUVUDYTA ---
st.title(f"StagePatch 🎛️ - {gig_namn}" if gig_namn else "StagePatch 🎛️")

st.header("1. Lägg till kanal")
st.selectbox("Välj instrument:", instrument_lista, key="vald_inst", on_change=on_inst_change)
c1, c2, c3 = st.columns(3)
with c1: st.text_input("Mikrofon/DI", key="vald_mic")
with c2: st.selectbox("Stativ", options=stativ_val, key="vald_stativ")
with c3:
    boxes = ["A", "B", "C", "D", "E", "F", "G", "H", ""]
    b_let = st.selectbox("Stagebox", boxes, format_func=lambda x: "Trådlös" if x == "" else f"Box {x}")
    high = 0
    for r in st.session_state["patch_list"]:
        v = str(r.get("Stagebox", ""))
        if v.startswith(b_let) and b_let != "":
            try:
                n = int(v[len(b_let):]); high = max(high, n)
            except: pass
    next_b = f"{b_let}{high + 1}" if b_let != "" else ""
    st.info(f"👉 Blir: **{next_b if next_b else 'Trådlös'}**")

st.button("Lägg till", type="primary", on_click=lagg_till_kanal, args=(next_b,))
if st.session_state["success_msg"]:
    st.success(st.session_state["success_msg"]); st.session_state["success_msg"] = ""

st.divider()

st.header("2. Aktuell Patchlista")
if st.session_state["patch_list"]:
    h = max(150, (len(st.session_state["patch_list"]) * 36) + 45)
    st.data_editor(
        st.session_state["patch_list"], use_container_width=True, height=h, hide_index=True,
        column_config={"Kanal": st.column_config.NumberColumn(disabled=True), "Stativ": st.column_config.SelectboxColumn(options=stativ_val)},
        key="patch_editor", on_change=update_table 
    )
    ca, cb, cc = st.columns(3)
    with ca: ch_del = st.selectbox("Radera kanal:", [r["Kanal"] for r in st.session_state["patch_list"]])
    with cb: 
        st.write(""); st.write("")
        if st.button("🗑️ Radera"):
            st.session_state["patch_list"] = [r for r in st.session_state["patch_list"] if r["Kanal"] != ch_del]
            for i, r in enumerate(st.session_state["patch_list"]): r["Kanal"] = i + 1
            st.rerun()
    with cc:
        st.write(""); st.write("")
        if st.button("🚨 Rensa allt"): st.session_state["patch_list"] = []; st.rerun()

    st.divider()
    st.header("3. Exportera")
    cx, cy = st.columns(2)
    with cx:
        st.subheader("📝 Namn till Yamaha")
        st.code("\n".join([r["Instrument"] for r in st.session_state["patch_list"]]), language="text")
    with cy:
        st.subheader("📄 PDF & Packlista")
        
        # --- ROBUST PDF-MOTOR ---
        pdf = FPDF()
        pdf.add_page()
        
        # 1. Rubrik
        pdf.set_font("helvetica", "B", 18)
        titel = f"Patchlista: {gig_namn}" if gig_namn else "Patchlista"
        pdf.cell(0, 10, titel, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        # 2. Gruppering
        box_groups = {}
        for r in st.session_state["patch_list"]:
            b_val = str(r.get("Stagebox", "")).strip()
            g = b_val[0].upper() if b_val and b_val[0].isalpha() else "Trådlöst"
            if g not in box_groups: box_groups[g] = []
            box_groups[g].append(r)
            
        # 3. Rita Patchlistan
        for g_name in sorted(box_groups.keys()):
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"Stagebox {g_name}" if g_name != "Trådlöst" else "Trådlöst", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 12)
            for k in sorted(box_groups[g_name], key=lambda x: str(x["Stagebox"])):
                b_lbl = f"{k['Stagebox']} " if k['Stagebox'] else ""
                row_txt = f"Ch {k['Kanal']}.   {b_lbl}  {k['Instrument']}"
                pdf.cell(0, 8, row_txt, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
        # 4. Räkna Packlista
        m_count = {}; s_count = {}
        for r in st.session_state["patch_list"]:
            m = r["Mic/DI"]; s = r["Stativ"]
            if m: m_count[m] = m_count.get(m, 0) + 1
            if s and s != "Inget": s_count[s] = s_count.get(s, 0) + 1

        # 5. Rita Packlista
        if m_count or s_count:
            pdf.ln(10)
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "--- PACKLISTA ---", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(5)
            
            if m_count:
                pdf.set_font("helvetica", "B", 12); pdf.cell(0, 8, "Mickar/DI:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 12)
                for m, a in sorted(m_count.items()): pdf.cell(0, 8, f"{a} st  {m}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)
            
            if s_count:
                pdf.set_font("helvetica", "B", 12); pdf.cell(0, 8, "Stativ:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 12)
                for s, a in sorted(s_count.items()): pdf.cell(0, 8, f"{a} st  {s}", new_x="LMARGIN", new_y="NEXT")
        
        pdf_bytes = bytes(pdf.output())
        st.download_button("📄 Ladda ner PDF", data=pdf_bytes, file_name=f"Patch_{gig_namn}.pdf" if gig_namn else "Patch.pdf", type="primary")
else:
    st.info("Listan är tom.")