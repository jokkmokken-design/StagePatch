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

# --- LOGIK FÖR DEFAULT-MALL ---
DEFAULT_DB_PATH = "databas.xlsx"
standard_mics = {}

# 1. Kolla om det finns en fast fil i mappen (från GitHub)
if os.path.exists(DEFAULT_DB_PATH):
    try:
        db_df = pd.read_excel(DEFAULT_DB_PATH)
        for index, row in db_df.iterrows():
            mic_val = str(row["Mic"]) if pd.notna(row["Mic"]) else ""
            stativ_val = str(row["Stativ"]) if pd.notna(row["Stativ"]) else "Inget"
            standard_mics[str(row["Instrument"])] = {"Mic": mic_val, "Stativ": stativ_val}
        st.sidebar.success("✅ Laddade din micklåda från GitHub!")
    except Exception as e:
        st.sidebar.error(f"Kunde inte läsa databas.xlsx: {e}")

# 2. Om ingen fil hittas, använd nödlösningen
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

# 3. Möjlighet att ladda upp en NY fil tillfälligt
uppladdad_fil = st.sidebar.file_uploader("Uppdatera micklådan tillfälligt:", type=["xlsx"])
if uppladdad_fil is not None:
    db_df = pd.read_excel(uppladdad_fil)
    standard_mics = {} 
    for index, row in db_df.iterrows():
        mic_val = str(row["Mic"]) if pd.notna(row["Mic"]) else ""
        stativ_val = str(row["Stativ"]) if pd.notna(row["Stativ"]) else "Inget"
        standard_mics[str(row["Instrument"])] = {"Mic": mic_val, "Stativ": stativ_val}
    instrument_lista = list(standard_mics.keys())

# --- APPENS MINNE ---
if "patch_list" not in st.session_state:
    st.session_state["patch_list"] = []
if "success_msg" not in st.session_state:
    st.session_state["success_msg"] = ""

if "vald_inst" not in st.session_state or st.session_state["vald_inst"] not in instrument_lista:
    if instrument_lista:
        forsta_inst = instrument_lista[0]
        st.session_state["vald_inst"] = forsta_inst
        st.session_state["vald_mic"] = standard_mics[forsta_inst]["Mic"]
        s = standard_mics[forsta_inst]["Stativ"]
        st.session_state["vald_stativ"] = s if s in stativ_val else stativ_val[0]

def on_inst_change():
    inst = st.session_state["vald_inst"]
    st.session_state["vald_mic"] = standard_mics[inst]["Mic"]
    s = standard_mics[inst]["Stativ"]
    st.session_state["vald_stativ"] = s if s in stativ_val else stativ_val[0]

def lagg_till_kanal(ny_box):
    inst = st.session_state["vald_inst"]
    mic = st.session_state["vald_mic"]
    stativ = st.session_state["vald_stativ"]
    kanal_nummer = len(st.session_state["patch_list"]) + 1 
    st.session_state["patch_list"].append({
        "Kanal": kanal_nummer, "Instrument": inst, "Mic/DI": mic, "Stativ": stativ, "Stagebox": ny_box 
    })
    nuvarande_index = instrument_lista.index(inst)
    nasta_index = (nuvarande_index + 1) % len(instrument_lista)
    nasta_inst = instrument_lista[nasta_index]
    st.session_state["vald_inst"] = nasta_inst
    st.session_state["vald_mic"] = standard_mics[nasta_inst]["Mic"]
    s = standard_mics[nasta_inst]["Stativ"]
    st.session_state["vald_stativ"] = s if s in stativ_val else stativ_val[0]
    st.session_state["success_msg"] = f"{inst} tillagd!"

def uppdatera_patch_list_fran_tabell():
    andringar = st.session_state["patch_editor"].get("edited_rows", {})
    for rad_index_str, andrad_data in andringar.items():
        rad_index = int(rad_index_str)
        for kolumn, nytt_varde in andrad_data.items():
            st.session_state["patch_list"][rad_index][kolumn] = nytt_varde

# --- HUVUDYTA ---
app_titel = f"StagePatch 🎛️ - {gig_namn}" if gig_namn else "StagePatch 🎛️"
st.title(app_titel)

st.header("1. Lägg till kanal")
st.selectbox("Välj instrument:", instrument_lista, key="vald_inst", on_change=on_inst_change)
col1, col2, col3 = st.columns(3)
with col1: st.text_input("Mikrofon/DI", key="vald_mic")
with col2: st.selectbox("Stativ", options=stativ_val, key="vald_stativ")
with col3:
    box_alternativ = ["A", "B", "C", "D", "E", "F", "G", "H", ""]
    box_bokstav = st.selectbox("Stagebox", box_alternativ, format_func=lambda x: "Trådlös" if x == "" else f"Box {x}")
    highest = 0
    for rad in st.session_state["patch_list"]:
        val = str(rad.get("Stagebox", "")).strip()
        if val.startswith(box_bokstav) and box_bokstav != "":
            try:
                num = int(val[len(box_bokstav):]); highest = max(highest, num)
            except: pass
    nasta_box_namn = f"{box_bokstav}{highest + 1}" if box_bokstav != "" else ""
    st.info(f"👉 Blir: **{nasta_box_namn if nasta_box_namn else 'Trådlös'}**")

st.button("Lägg till", type="primary", on_click=lagg_till_kanal, args=(nasta_box_namn,))
if st.session_state["success_msg"]:
    st.success(st.session_state["success_msg"]); st.session_state["success_msg"] = ""

st.divider()

st.header("2. Aktuell Patchlista")
if st.session_state["patch_list"]:
    tabell_hojd = max(150, (len(st.session_state["patch_list"]) * 36) + 45)
    st.data_editor(
        st.session_state["patch_list"], use_container_width=True, height=tabell_hojd, hide_index=True,
        column_config={"Kanal": st.column_config.NumberColumn(disabled=True), "Stativ": st.column_config.SelectboxColumn(options=stativ_val)},
        key="patch_editor", on_change=uppdatera_patch_list_fran_tabell 
    )
    colA, colB, colC = st.columns(3)
    with colA:
        ch_del = st.selectbox("Radera kanal:", [r["Kanal"] for r in st.session_state["patch_list"]])
    with colB:
        st.write(""); st.write("")
        if st.button("🗑️ Radera"):
            st.session_state["patch_list"] = [r for r in st.session_state["patch_list"] if r["Kanal"] != ch_del]
            for i, r in enumerate(st.session_state["patch_list"]): r["Kanal"] = i + 1
            st.rerun()
    with colC:
        st.write(""); st.write("")
        if st.button("🚨 Rensa allt"): st.session_state["patch_list"] = []; st.rerun()

    st.divider()
    st.header("3. Exportera")
    colX, colY = st.columns(2)
    with colX:
        st.subheader("📝 Namn till Yamaha")
        st.code("\n".join([r["Instrument"] for r in st.session_state["patch_list"]]), language="text")
    with colY:
        st.subheader("📄 PDF & Packlista")
        
        # --- KOMPLETT PDF LOGIK ---
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 18)
        pdf_titel = f"Patchlista: {gig_namn}" if gig_namn else "Patchlista"
        pdf.cell(0, 10, pdf_titel, align="C", ln=1)
        pdf.ln(5)
        
        boxar = {}
        for rad in st.session_state["patch_list"]:
            box_text = str(rad["Stagebox"]).strip()
            box_grupp = box_text[0].upper() if box_text and box_text[0].isalpha() else "Trådlöst"
            if box_grupp not in boxar: boxar[box_grupp] = []
            boxar[box_grupp].append(rad)
            
        for box_namn in sorted(boxar.keys()):
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, f"Stagebox {box_namn}" if box_namn != "Trådlöst" else "Trådlöst", ln=1)
            pdf.set_font("helvetica", "", 12)
            for k in sorted(boxar[box_namn], key=lambda x: str(x["Stagebox"])):
                box_label = f"{k['Stagebox']} " if k['Stagebox'] else ""
                pdf.cell(0, 8, f"Ch {k['Kanal']}.   {box_label}  {k['Instrument']}", ln=1)
            pdf.ln(5)
            
        mick_antal = {}; stativ_antal = {}
        for rad in st.session_state["patch_list"]:
            m = rad["Mic/DI"]; s = rad["Stativ"]
            if m: mick_antal[m] = mick_antal.get(m, 0) + 1
            if s and s != "Inget": stativ_antal[s] = stativ_antal.get(s, 0) + 1

        pdf.ln(10); pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "--- PACKLISTA ---", align="C", ln=1); pdf.ln(5)
        pdf.set_font("helvetica", "B", 12); pdf.cell(0, 8, "Mickar/DI:", ln=1)
        pdf.set_font("helvetica", "", 12)
        for m, a in sorted(mick_antal.items()): pdf.cell(0, 8, f"{a} st  {m}", ln=1)
        pdf.ln(5); pdf.set_font("helvetica", "B", 12); pdf.cell(0, 8, "Stativ:", ln=1)
        pdf.set_font("helvetica", "", 12)
        for s, a in sorted(stativ_antal.items()): pdf.cell(0, 8, f"{a} st  {s}", ln=1)
        
        pdf_bytes = bytes(pdf.output())
        st.download_button("📄 Ladda ner PDF", data=pdf_bytes, file_name=f"Patch_{gig_namn}.pdf" if gig_namn else "Patch.pdf", type="primary")
else:
    st.info("Listan är tom.")