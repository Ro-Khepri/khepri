import streamlit as st

st.set_page_config(
    page_title="Khépri — Planeur Solaire",
    page_icon="✈",
    layout="wide",
)

# Navigation
PAGES = {
    "Accueil": "accueil",
    "1 · Géométrie aile (GEOAILE)": "geoaile",
    "2 · Profil NACA (LISCAR)": "liscar",
    "3 · Portance elliptique": "portance",
    "4 · Domaine de vol (DOMAINE)": "domaine",
    "5 · Charges aéro (MECAVOL)": "mecavol",
    "6 · Contraintes (EFFORTS)": "efforts",
    "7 · Qualité de vol": "qualvol",
}

with st.sidebar:
    st.title("Khépri")
    st.caption("Planeur solaire photovoltaïque")
    st.divider()
    page = st.radio("Module", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("Normes JAR-22 — Base H201B Libelle")

# Routing
module = PAGES[page]

if module == "accueil":
    from modules import accueil
    accueil.render()
elif module == "geoaile":
    from modules import geoaile
    geoaile.render()
elif module == "liscar":
    from modules import liscar
    liscar.render()
elif module == "portance":
    from modules import portance
    portance.render()
elif module == "domaine":
    from modules import domaine
    domaine.render()
elif module == "mecavol":
    from modules import mecavol
    mecavol.render()
elif module == "efforts":
    from modules import efforts
    efforts.render()
elif module == "qualvol":
    from modules import qualvol
    qualvol.render()
