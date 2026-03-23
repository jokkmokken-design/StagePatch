import streamlit as st
import pandas as pd
from fpdf import FPDF
import io

st.set_page_config(page_title="StagePatch", layout="wide") 

# --- SIDOMENY: INSTÄLLNINGAR & DATABAS ---
st.sidebar.header("🎸 Gig & Inställningar")
gig_namn = st.sidebar.text_input("Namn på Gig/Band:", placeholder="T.ex. Sommarfestivalen 2026")

st.sidebar.divider()

st.sidebar.header("📁 Din Micklåda (Databas)")
st.sidebar.write("Ladda upp din egen Excel-fil med instrument och mikrofoner.")

template_data = {
    "Instrument": ["Kick In", "Kick Out", "Snare Top", "Bass DI", "Vocal Center"],
    "Mic": ["Shure Beta 91", "Audix D6", "Shure SM57", "Radial J48", "Shure Beta 58"],
    "Stativ": ["Inget", "Very Short", "Short", "Inget", "Tall"]
}
template_df = pd.DataFrame(template_data)
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    template_df.to_excel(writer, index=False)
excel_bytes = output.getvalue()

st.sidebar.download_button(
    label="⬇️ Ladda ner Excel-mall",
    data=excel_bytes,
    file_name="micklada_mall.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

uppladdad_fil = st.sidebar.file_uploader("Ladda upp din micklåda (.xlsx)", type=["xlsx"])

standard_mics = {}
if uppladdad_fil is not None:
    db_df = pd.read_excel(uppladdad_fil)
    st.sidebar.success(f"Inläst: {len(db_df)} instrument!")
    for index, row in db_df.iterrows():
        mic_val = str(row["Mic"]) if pd.notna(row["Mic"]) else ""
        stativ_val = str(row["Stativ"]) if pd.notna(row["Stativ"]) else "Inget"
        standard_mics[str(row["Instrument"])] = {"Mic": mic_val, "Stativ": stativ_val}
else:
    for index, row in template_df.iterrows():
         standard_mics[row["Instrument"]] = {"Mic": row["Mic"], "Stativ": row["Stativ"]}

stativ_val = ["Tall", "Short", "Very Short", "Flat", "Inget"]
instrument_lista = list(standard_mics.keys())


# --- APPENS MINNE ---
if "patch_list" not in st.session_state:
    st.session_state["patch_list"] = []
if "success_msg" not in st.session_state:
    st.session_state["success_msg"] = ""

if "vald_inst" not in st.session_state or st.session_state["vald_inst"] not in instrument_lista:
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
        "Kanal": kanal_nummer,
        "Instrument": inst,
        "Mic/DI": mic,
        "Stativ": stativ,
        "Stagebox": ny_box 
    })
    
    nuvarande_index = instrument_lista.index(inst)
    nasta_index = (nuvarande_index + 1) % len(instrument_lista)
    nasta_inst = instrument_lista[nasta_index]
    
    st.session_state["vald_inst"] = nasta_inst
    st.session_state["vald_mic"] = standard_mics[nasta_inst]["Mic"]
    s = standard_mics[nasta_inst]["Stativ"]
    st.session_state["vald_stativ"] = s if s in stativ_val else stativ_val[0]
    
    box_msg = f"i {ny_box}" if ny_box != "" else "som Trådlös"
    st.session_state["success_msg"] = f"{inst} tillagd på kanal {kanal_nummer} {box_msg}!"

def uppdatera_patch_list_fran_tabell():
    andringar = st.session_state["patch_editor"].get("edited_rows", {})
    for rad_index_str, andrad_data in andringar.items():
        rad_index = int(rad_index_str)
        for kolumn, nytt_varde in andrad_data.items():
            st.session_state["patch_list"][rad_index][kolumn] = nytt_varde


# --- HUVUDYTA ---
app_titel = f"StagePatch 🎛️ - {gig_namn}" if gig_namn else "StagePatch 🎛️"
st.title(app_titel)

# 1. LÄGG TILL KANAL
st.header("1. Lägg till kanal")

st.selectbox("Välj instrument från ridern:", instrument_lista, key="vald_inst", on_change=on_inst_change)

st.write("Justera valen vid behov innan du lägger till:")

col1, col2, col3 = st.columns(3)

with col1:
    st.text_input("Mikrofon/DI", key="vald_mic")

with col2:
    st.selectbox("Stativ", options=stativ_val, key="vald_stativ")

with col3:
    # A är nu först, tomt ("") är sist!
    box_alternativ = ["A", "B", "C", "D", "E", "F", "G", "H", ""]
    box_bokstav = st.selectbox(
        "Stagebox", 
        box_alternativ, 
        format_func=lambda x: "Ingen / Trådlös" if x == "" else f"Stagebox {x}"
    )
    
    if box_bokstav == "":
        nasta_box_namn = ""
        st.info("👉 Blir tilldelad: **Ingen stagebox (Tom)**")
    else:
        highest = 0
        for rad in st.session_state["patch_list"]:
            val = str(rad.get("Stagebox", "")).strip()
            if val.startswith(box_bokstav):
                try:
                    num = int(val[len(box_bokstav):])
                    if num > highest:
                        highest = num
                except ValueError:
                    pass
        nasta_box_namn = f"{box_bokstav}{highest + 1}"
        st.info(f"👉 Blir tilldelad: **{nasta_box_namn}**")

st.button("Lägg till i patchlistan", type="primary", on_click=lagg_till_kanal, args=(nasta_box_namn,))

if st.session_state["success_msg"] != "":
    st.success(st.session_state["success_msg"])
    st.session_state["success_msg"] = ""

st.divider() 

# 2. SAMMANSTÄLLNING
st.header("2. Aktuell Patchlista")

if len(st.session_state["patch_list"]) > 0:
    st.write("💡 *Tips: Dubbelklicka i tabellen för att redigera. Tryck Enter när du är klar med en cell!*")
    
    # Beräknar höjden på tabellen dynamiskt baserat på antal rader (ca 36 pixlar per rad + 40 för rubriker)
    tabell_hojd = max(150, (len(st.session_state["patch_list"]) * 36) + 42)
    
    st.data_editor(
        st.session_state["patch_list"], 
        use_container_width=True, 
        height=tabell_hojd, # Här använder vi formeln!
        hide_index=True,
        column_config={
            "Kanal": st.column_config.NumberColumn("Kanal", disabled=True),
            "Instrument": st.column_config.TextColumn("Instrument"),
            "Mic/DI": st.column_config.TextColumn("Mic/DI"),
            "Stativ": st.column_config.SelectboxColumn("Stativ", options=stativ_val), 
            "Stagebox": st.column_config.TextColumn("Stagebox")
        },
        key="patch_editor",
        on_change=uppdatera_patch_list_fran_tabell 
    )

    st.write("---")
    
    colA, colB, colC = st.columns([2, 2, 2])
    with colA:
        tillgangliga_kanaler = [rad["Kanal"] for rad in st.session_state["patch_list"]]
        kanal_att_ta_bort = st.selectbox("Radera enskild kanal:", tillgangliga_kanaler)
    with colB:
        st.write("") 
        st.write("") 
        if st.button("🗑️ Ta bort vald kanal"):
            ny_lista = [rad for rad in st.session_state["patch_list"] if rad["Kanal"] != kanal_att_ta_bort]
            for index, rad in enumerate(ny_lista):
                rad["Kanal"] = index + 1
            st.session_state["patch_list"] = ny_lista
            st.rerun()
    with colC:
        st.write("")
        st.write("")
        if st.button("🚨 Rensa hela listan"):
            st.session_state["patch_list"] = []
            st.rerun()

    st.divider()
    
    # 3. YAMAHA EXPORT & PDF
    st.header("3. Exportera och skriv ut")
    
    col_x, col_y = st.columns(2)
    
    with col_x:
        st.subheader("📝 Namn till Editorn")
        st.write("Kopiera namnen och klistra in (Cmd+V) i Yamahas Channel List.")
        bara_namn = "\n".join([rad["Instrument"] for rad in st.session_state["patch_list"]])
        st.code(bara_namn, language="text")
        
    with col_y:
        st.subheader("📄 Patch & Packlista")
        st.write("Skapar en snygg PDF för utskrift och packning.")
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", "B", 18)
        
        # Sätter gig-namnet på PDF:en om du har fyllt i det!
        pdf_titel = f"Patchlista: {gig_namn}" if gig_namn else "Patchlista"
        pdf.cell(0, 10, pdf_titel, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        boxar = {}
        for rad in st.session_state["patch_list"]:
            box_text = str(rad["Stagebox"]).strip()
            if len(box_text) > 0:
                box_grupp = box_text[0].upper() if box_text[0].isalpha() else "Trådlöst"
            else:
                box_grupp = "Trådlöst" 
                
            if box_grupp not in boxar:
                boxar[box_grupp] = []
            boxar[box_grupp].append(rad)
            
        for box_namn in sorted(boxar.keys()):
            pdf.set_font("helvetica", "B", 14)
            rubrik = "Trådlöst / Oplacerat" if box_namn == "Trådlöst" else f"Stagebox {box_namn}"
            pdf.cell(0, 10, rubrik, new_x="LMARGIN", new_y="NEXT")
            
            def sort_key(k):
                val = str(k["Stagebox"])
                try:
                    return int(''.join(filter(str.isdigit, val)))
                except ValueError:
                    return 999
            
            kanaler_i_box = sorted(boxar[box_namn], key=sort_key)
            
            pdf.set_font("helvetica", "", 12)
            for k in kanaler_i_box:
                box_print = f"{k['Stagebox']}  " if k['Stagebox'] != "" else ""
                text_rad = f"Ch {k['Kanal']}.   {box_print}{k['Instrument']}"
                pdf.cell(0, 8, text_rad, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
        mick_antal = {}
        stativ_antal = {}
        for rad in st.session_state["patch_list"]:
            mic = rad["Mic/DI"]
            if mic:
                mick_antal[mic] = mick_antal.get(mic, 0) + 1
            stativ = rad["Stativ"]
            if stativ and stativ != "Inget":
                stativ_antal[stativ] = stativ_antal.get(stativ, 0) + 1

        pdf.ln(10)
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "--- PACKLISTA ---", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Mikrofoner / DI-boxar:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 12)
        for mic, antal in sorted(mick_antal.items()):
            pdf.cell(0, 8, f"{antal} st   {mic}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Stativ:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 12)
        for stativ, antal in sorted(stativ_antal.items()):
            pdf.cell(0, 8, f"{antal} st   {stativ}", new_x="LMARGIN", new_y="NEXT")

        pdf_bytes = bytes(pdf.output())
        st.download_button(
            label="📄 Ladda ner PDF",
            data=pdf_bytes,
            file_name=f"Patchlista_{gig_namn}.pdf" if gig_namn else "Patchlista.pdf",
            mime="application/pdf",
            type="primary"
        )

else:
    st.info("Patchlistan är tom. Börja lägga till instrument ovan!")