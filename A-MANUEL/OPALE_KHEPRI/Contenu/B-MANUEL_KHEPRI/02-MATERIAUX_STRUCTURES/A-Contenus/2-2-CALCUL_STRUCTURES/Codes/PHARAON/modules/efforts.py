"""
Module EFFORTS — Contraintes dans le longeron en fonction de y
Modèle : longeron à semelles (caps) + âme (web)
Matériau de référence : fibre de verre composite (H201B)
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from modules.mecavol import compute_mecavol
from data.longeron_h201b import h_longeron, Y_DOSSIER, H_DOSSIER


# Résistances admissibles fibre de verre composite (valeurs courantes)
SIGMA_ADM_TRACTION   = 300e6   # Pa — traction/compression semelles
SIGMA_ADM_CISAILLEMENT = 80e6  # Pa — cisaillement âme
FACTEUR_SECURITE_MAT  = 1.5    # matériau composite


def hauteur_longeron(y: np.ndarray, demi: float,
                     h_root: float, h_tip: float,
                     source: str = "dossier") -> np.ndarray:
    """
    Hauteur du longeron h(y).
    - source='dossier' ou 'catia' : données réelles H201B (interpolation)
    - source='lineaire'           : loi linéaire h_root → h_tip (fallback)
    """
    if source in ("dossier", "catia"):
        return h_longeron(y, source=source)
    return h_root + (h_tip - h_root) * (y / demi)


def compute_efforts(res_meca: dict,
                    h_root: float, h_tip: float,
                    b_semelle: float, t_semelle: float,
                    e_ame: float, source_h: str = "dossier"):
    """
    Calcule les contraintes de flexion et de cisaillement dans le longeron.

    Modèle en I simplifié :
      - Deux semelles (caps) : b_semelle × t_semelle
      - Âme (web) : épaisseur e_ame, hauteur h(y)

    Paramètres
    ----------
    res_meca   : résultats de compute_mecavol
    h_root     : hauteur emplanture [m] (utilisé si source_h='lineaire')
    h_tip      : hauteur saumon [m]     (utilisé si source_h='lineaire')
    b_semelle  : largeur des semelles [m]
    t_semelle  : épaisseur des semelles [m]
    e_ame      : épaisseur de l'âme [m]
    source_h   : 'dossier' | 'catia' | 'lineaire'
    """
    y    = res_meca["y"]
    M    = res_meca["M_ultime"]
    T    = res_meca["T"]
    demi = res_meca["demi"]

    h = hauteur_longeron(y, demi, h_root, h_tip, source=source_h)   # [m]

    # ── Section en I ──────────────────────────────────────────────────
    # Moment quadratique exact pour une section en I (semelles + âme)
    # Formule : I = I_rectangle_total - I_vide_intérieur
    # I = (b_semelle × H_tot³ / 12) - ((b_semelle - e_ame) × h³ / 12)
    # où H_tot = hauteur totale = h + 2 × t_semelle
    #    h     = hauteur de l'âme seule (entre les faces intérieures des semelles)
    #    b_semelle = largeur des semelles
    H_tot = h + 2 * t_semelle                                           # hauteur totale [m]
    I = (b_semelle * H_tot**3 / 12
         - (b_semelle - e_ame) * h**3 / 12)                             # m⁴

    # Module de flexion : W_flex = I / (H_tot/2)
    v_max = h / 2 + t_semelle          # distance axe neutre → fibre extrême = H_tot/2
    W_flex = I / v_max

    # Moment statique de la demi-section par rapport à l'axe neutre (formule Jourawski)
    # Contribution des semelles + contribution de la demi-âme
    S_stat = (b_semelle * t_semelle * (h / 2 + t_semelle / 2)
              + e_ame * (h / 2) * (h / 4))                    # m³

    # Contrainte de cisaillement maximale (à mi-hauteur de l'âme) par Jourawski
    # ── Contraintes ──────────────────────────────────────────────────────
    sigma = np.abs(M) / W_flex         # contrainte de flexion [Pa]
    tau = np.abs(T) * S_stat / (I * e_ame)                    # Pa

    # Contrainte de Von Mises équivalente
    sigma_vm = np.sqrt(sigma**2 + 3 * tau**2)

    # ── Taux de travail ──────────────────────────────────────────────────
    taux_flexion     = sigma / (SIGMA_ADM_TRACTION    / FACTEUR_SECURITE_MAT)
    taux_cisaillement= tau   / (SIGMA_ADM_CISAILLEMENT / FACTEUR_SECURITE_MAT)
    taux_vm          = sigma_vm / (SIGMA_ADM_TRACTION / FACTEUR_SECURITE_MAT)

    return {
        "y": y, "h": h, "I": I, "W_flex": W_flex,
        "H_tot": H_tot, "S_stat": S_stat,
        "sigma": sigma, "tau": tau, "sigma_vm": sigma_vm,
        "taux_flexion": taux_flexion,
        "taux_cisaillement": taux_cisaillement,
        "taux_vm": taux_vm,
        "sigma_adm": SIGMA_ADM_TRACTION / FACTEUR_SECURITE_MAT,
        "tau_adm":   SIGMA_ADM_CISAILLEMENT / FACTEUR_SECURITE_MAT,
    }


def plot_efforts(res: dict) -> plt.Figure:
    y = res["y"]
    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)

    # ── Contraintes absolues ──────────────────────────────────────────────
    ax = axes[0]
    ax.plot(y, res["sigma"] / 1e6,    color="royalblue", lw=2, label="σ flexion [MPa]")
    ax.plot(y, res["tau"] / 1e6,      color="seagreen",  lw=2, label="τ cisaillement [MPa]", linestyle="--")
    ax.plot(y, res["sigma_vm"] / 1e6, color="orange",    lw=1.5, label="σ Von Mises [MPa]", linestyle="-.")
    ax.axhline(res["sigma_adm"] / 1e6, color="tomato", linestyle=":", lw=1.5,
               label=f"σ admissible = {res['sigma_adm']/1e6:.0f} MPa")
    ax.set_ylabel("Contrainte [MPa]")
    ax.set_title("Contraintes dans le longeron (moment ultime JAR-22)", fontsize=12)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ── Taux de travail ───────────────────────────────────────────────────
    ax = axes[1]
    ax.plot(y, res["taux_flexion"]      * 100, color="royalblue", lw=2, label="Flexion")
    ax.plot(y, res["taux_cisaillement"] * 100, color="seagreen",  lw=2, label="Cisaillement", linestyle="--")
    ax.plot(y, res["taux_vm"]           * 100, color="orange",    lw=1.5, label="Von Mises", linestyle="-.")
    ax.axhline(100, color="tomato", linestyle=":", lw=1.5, label="Limite 100%")
    ax.fill_between(y, res["taux_vm"] * 100, 100,
                    where=res["taux_vm"] >= 1.0,
                    color="tomato", alpha=0.3, label="Zone critique")
    ax.set_ylabel("Taux de travail [%]")
    ax.set_ylim(0, max(res["taux_vm"].max() * 110, 110))
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ── Hauteur du longeron ───────────────────────────────────────────────
    ax = axes[2]
    ax.plot(y, res["h"] * 100, color="gray", lw=2)
    ax.fill_between(y, 0, res["h"] * 100, alpha=0.2, color="gray")
    ax.set_ylabel("Hauteur longeron h [cm]")
    ax.set_xlabel("Position spanwise y [m]")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def render():
    st.title("Module 6 — Contraintes structurales (EFFORTS)")
    st.caption("Contraintes de flexion et cisaillement dans le longeron principal · JAR-22")
    
    st.info(
        "**Modèle structurel :** section en I — formule exacte de Jourawski. "
        "Le moment quadratique et la contrainte de cisaillement sont calculés "
        "avec les formules exactes de résistance des matériaux (pas de simplification). "
        "Les résistances admissibles sont indicatives (fibre de verre composite standard)."
    )

    # ── Reprise des paramètres MECAVOL depuis session_state ──────────────
    meca = st.session_state.get('mecavol_params', {})
    def_masse          = float(meca.get('masse',          350.0))
    def_surface        = float(meca.get('surface',          9.80))
    def_b              = float(meca.get('b',               15.0))
    def_n              = float(meca.get('n',                5.3))
    def_masse_struct   = float(meca.get('masse_structure',  52.0))
    def_masse_dist_add = float(meca.get('masse_dist_add',   0.0))
    def_charges_conc   = meca.get('charges_conc', [])
    def_rzeh           = float(meca.get('rzeh',             0.0))
    def_masse_ballast  = float(meca.get('masse_ballast',   18.0))
    def_y_ballast      = float(meca.get('y_ballast',        1.0))

    if meca:
        st.info("Paramètres repris depuis le module MECAVOL.")

    with st.sidebar:
        st.subheader("Planeur")
        masse   = st.number_input("Masse totale [kg]",   100.0, 600.0, def_masse,        step=5.0)
        surface = st.number_input("Surface alaire [m²]",   5.0,  25.0, def_surface,      step=0.1)
        b       = st.number_input("Envergure [m]",          8.0,  30.0, def_b,            step=0.5)
        n       = st.number_input("Facteur de charge n",   -3.0,   7.0, def_n,            step=0.1)
        masse_structure = st.number_input("Structure demi-aile [kg]", 0.0, 150.0, def_masse_struct, step=1.0)
        masse_dist_add  = st.number_input("Masse distribuée add. [kg]", 0.0, 50.0, def_masse_dist_add, step=0.5)

        # Charges concentrées reprises de MECAVOL (affichage info uniquement)
        charges_conc = def_charges_conc
        if charges_conc:
            st.caption("Charges concentrées (reprises de MECAVOL) :")
            for cc in charges_conc:
                if cc['masse'] > 0:
                    st.caption(f"  {cc.get('label','Masse')} : {cc['masse']:.1f} kg @ y={cc['y']:.2f} m")

        rzeh          = def_rzeh
        masse_ballast = st.number_input("Lest demi-aile [kg]", 0.0, 100.0, def_masse_ballast, step=1.0)
        y_ballast     = st.number_input("Position y lest [m]",  0.0,   7.0, def_y_ballast,     step=0.1)

        st.divider()
        st.subheader("Géométrie longeron")
        source_h = st.radio("Profil de hauteur h(y)",
                            ["dossier", "lineaire"],
                            format_func=lambda x: {
                                "dossier":  "Dossier de calcul H201B ✓",
                                "lineaire": "Loi linéaire (manuel)",
                            }[x])
        if source_h == "lineaire":
            h_root = st.number_input("Hauteur emplanture [mm]", 20.0, 250.0, 143.5, step=1.0) / 1000
            h_tip  = st.number_input("Hauteur saumon [mm]",      5.0,  80.0,  64.6, step=1.0) / 1000
        else:
            h_root, h_tip = 0.1435, 0.0646
        st.caption("Section en I — fibre de verre composite")
        b_semelle = st.number_input("Largeur semelle [mm]",   10.0, 150.0, 100.0, step=1.0) / 1000
        t_semelle = st.number_input("Épaisseur semelle [mm]",  1.0,  30.0,  20.0, step=0.5) / 1000
        e_ame     = st.number_input("Épaisseur âme [mm]",      1.0,  20.0,   5.0, step=0.5) / 1000

        st.divider()
        st.subheader("Matériau")
        st.caption(f"σ_adm flexion  = {SIGMA_ADM_TRACTION/1e6:.0f} MPa")
        st.caption(f"τ_adm cisaill. = {SIGMA_ADM_CISAILLEMENT/1e6:.0f} MPa")
        st.caption(f"Facteur sécu.  = {FACTEUR_SECURITE_MAT}")

    # ── Calcul en chaîne ─────────────────────────────────────────────────
    res_meca = compute_mecavol(masse, surface, b, n,
                               masse_structure, masse_dist_add, charges_conc,
                               rzeh=rzeh,
                               masse_ballast=masse_ballast, y_ballast=y_ballast)
    res = compute_efforts(res_meca, h_root, h_tip, b_semelle, t_semelle, e_ame,
                          source_h=source_h)

    # ── Métriques ─────────────────────────────────────────────────────────
    st.subheader("Résultats à l'emplanture (section la plus chargée)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("σ flexion max",     f"{res['sigma'][0]/1e6:.1f} MPa")
    c2.metric("τ cisaillement max", f"{res['tau'][0]/1e6:.1f} MPa")
    c3.metric("σ Von Mises max",   f"{res['sigma_vm'][0]/1e6:.1f} MPa")

    taux_max = res["taux_vm"][0] * 100
    couleur = "normal" if taux_max < 80 else ("off" if taux_max < 100 else "inverse")
    c4.metric("Taux de travail max", f"{taux_max:.1f} %",
              delta=f"{'✓ OK' if taux_max < 100 else '✗ RUPTURE'}",
              delta_color=couleur)

    # Alerte si dépassement
    if res["taux_vm"].max() >= 1.0:
        y_crit = res["y"][res["taux_vm"] >= 1.0]
        st.error(f"⚠️ Dépassement de la contrainte admissible entre y = {y_crit[0]:.2f} m "
                 f"et y = {y_crit[-1]:.2f} m — revoir la section du longeron.")
    else:
        st.success(f"Longeron dimensionné OK — taux max = {taux_max:.1f} % < 100 %")

    st.divider()
    fig = plot_efforts(res)
    st.pyplot(fig)
    plt.close(fig)

    with st.expander("Tableau des contraintes f(y)"):
        import pandas as pd
        step = max(len(res["y"]) // 20, 1)
        idx  = np.arange(0, len(res["y"]), step)
        df = pd.DataFrame({
            "y [m]":          np.round(res["y"][idx], 3),
            "h [mm]":         np.round(res["h"][idx] * 1000, 1),
            "σ flex [MPa]":   np.round(res["sigma"][idx] / 1e6, 2),
            "τ cis [MPa]":    np.round(res["tau"][idx] / 1e6, 2),
            "σ VM [MPa]":     np.round(res["sigma_vm"][idx] / 1e6, 2),
            "Taux VM [%]":    np.round(res["taux_vm"][idx] * 100, 1),
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
