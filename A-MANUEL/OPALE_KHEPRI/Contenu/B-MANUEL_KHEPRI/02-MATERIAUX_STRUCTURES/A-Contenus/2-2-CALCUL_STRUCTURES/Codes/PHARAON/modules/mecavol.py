"""
Module MECAVOL — Distribution des charges aérodynamiques sur la demi-aile
Hypothèse elliptique + masses distribuées + charges concentrées + lest
Correction EH : rza = n·m·g − rzeh  (MECAVOL.PAS, Prodhomme 1992)
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


def compute_mecavol(masse: float, surface: float, b: float, n: float,
                    masse_structure: float,
                    masse_dist_add: float,
                    charges_conc: list,
                    rzeh: float = 0.0,
                    masse_ballast: float = 0.0, y_ballast: float = 1.0,
                    n_points: int = 200):
    """
    Calcule la distribution de charges, l'effort tranchant et le moment fléchissant
    sur la demi-aile (y de 0 à b/2).

    Paramètres
    ----------
    masse           : masse totale planeur [kg]
    surface         : surface alaire [m²]
    b               : envergure totale [m]
    n               : facteur de charge
    masse_structure : masse de la structure de la demi-aile [kg]
                      (aile + équipements fixes intégrés)
    masse_dist_add  : masse distribuée additionnelle sur la demi-aile [kg]
                      (ex. panneaux solaires collés, répartition uniforme)
    charges_conc    : liste de dict {'masse': float [kg], 'y': float [m]}
                      charges concentrées (moteur, batteries, etc.)
    rzeh            : force aérodynamique totale sur l'EH [N]
                      (>0 = vers le haut, <0 = vers le bas)
                      Physique : rza = n·m·g − rzeh
    masse_ballast   : masse de lest en eau sur une demi-aile [kg]
    y_ballast       : position spanwise du barycentre du lest [m]
    n_points        : nombre de points de discrétisation
    """
    g    = 9.81
    demi = b / 2.0
    y    = np.linspace(0, demi, n_points)

    # ── Portance aile — correction EH ────────────────────────────────────
    rza = n * masse * g - rzeh
    l0  = 2.0 * rza / (np.pi * demi)
    l_aero = l0 * np.sqrt(np.maximum(1 - (y / demi)**2, 0))

    # ── Masse distribuée totale (structure + additionnelle) × n ──────────
    masse_dist_totale = masse_structure + masse_dist_add
    p_dist = n * masse_dist_totale * g / demi
    l_poids_dist = -p_dist * np.ones_like(y)

    # ── Charge nette distribuée ───────────────────────────────────────────
    l_net = l_aero + l_poids_dist

    # ── Effort tranchant T(y) ─────────────────────────────────────────────
    T = np.zeros(n_points)
    for i in range(n_points):
        T[i] = np.trapz(l_net[i:], y[i:])

    # Lest en eau × n
    F_ballast = n * masse_ballast * g
    T -= np.where(y <= y_ballast, F_ballast, 0.0)

    # Charges concentrées × n
    F_conc = []
    for cc in charges_conc:
        F = n * cc['masse'] * g
        T -= np.where(y <= cc['y'], F, 0.0)
        F_conc.append(F)

    # ── Moment fléchissant M(y) ───────────────────────────────────────────
    M = np.zeros(n_points)
    for i in range(n_points):
        M[i] = np.trapz(T[i:], y[i:])

    # ── Moment ultime JAR-22 ──────────────────────────────────────────────
    f_securite = 1.5
    M_ultime = M * f_securite

    return {
        "y": y, "demi": demi,
        "l_aero": l_aero, "l_poids": l_poids_dist, "l_net": l_net,
        "T": T, "M": M, "M_ultime": M_ultime,
        "l0": l0, "rza": rza, "rzeh": rzeh,
        "F_ballast": F_ballast, "y_ballast": y_ballast,
        "charges_conc": charges_conc, "F_conc": F_conc,
        "masse_dist_add": masse_dist_add,
        "n": n, "masse": masse, "f_securite": f_securite,
    }


def plot_charges(res: dict) -> plt.Figure:
    """3 sous-graphes : distribution de charges, effort tranchant, moment fléchissant."""
    y   = res["y"]
    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)

    # ── Charges distribuées ───────────────────────────────────────────────
    ax = axes[0]
    rzeh_label = f" (rzeh={res['rzeh']:+.0f} N)" if res['rzeh'] != 0 else ""
    ax.plot(y, res["l_aero"],    color="royalblue", lw=2,
            label=f"Portance aile (elliptique){rzeh_label}")
    ax.plot(y, -res["l_poids"],  color="tomato",    lw=1.5, linestyle="--",
            label="Poids distribué (structure + additionnelle)")
    ax.plot(y, res["l_net"],     color="seagreen",  lw=2,
            label="Charge nette")

    colors_conc = ["orange", "purple", "brown"]
    for k, cc in enumerate(res["charges_conc"]):
        if cc['masse'] > 0:
            ax.axvline(cc['y'], color=colors_conc[k % 3], linestyle=":", lw=1.2,
                       label=f"{cc.get('label','Masse')} @ y={cc['y']:.2f} m")
    if res["F_ballast"] > 0:
        ax.axvline(res["y_ballast"], color="steelblue", linestyle=":", lw=1.2,
                   label=f"Lest @ y={res['y_ballast']:.2f} m")

    ax.set_ylabel("Charge linéique [N/m]")
    ax.set_title(f"Distribution des charges — n = {res['n']:.1f}", fontsize=12)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="black", lw=0.8)

    # ── Effort tranchant ──────────────────────────────────────────────────
    ax = axes[1]
    ax.plot(y, res["T"] / 1000, color="royalblue", lw=2)
    for k, cc in enumerate(res["charges_conc"]):
        if cc['masse'] > 0:
            ax.axvline(cc['y'], color=colors_conc[k % 3], linestyle=":", lw=1.2)
    ax.set_ylabel("Effort tranchant T [kN]")
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="black", lw=0.8)

    # ── Moment fléchissant ────────────────────────────────────────────────
    ax = axes[2]
    ax.plot(y, res["M"] / 1000,        color="royalblue", lw=2,
            label="Moment limite")
    ax.plot(y, res["M_ultime"] / 1000, color="tomato",    lw=1.5, linestyle="--",
            label=f"Moment ultime (×{res['f_securite']})")
    for k, cc in enumerate(res["charges_conc"]):
        if cc['masse'] > 0:
            ax.axvline(cc['y'], color=colors_conc[k % 3], linestyle=":", lw=1.2)
    ax.set_ylabel("Moment fléchissant M [kN·m]")
    ax.set_xlabel("Position spanwise y [m]")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.annotate(f"M_empl. = {res['M'][0]/1000:.2f} kN·m",
                xy=(0, res["M"][0]/1000),
                xytext=(res["demi"] * 0.15, res["M"][0]/1000 * 0.85),
                fontsize=8, arrowprops=dict(arrowstyle="->", color="gray"))

    fig.tight_layout()
    return fig


def render():
    st.title("Module 5 — Charges aérodynamiques (MECAVOL)")
    st.caption("Distribution elliptique · EH · Lest · Masses distribuées et concentrées · JAR-22")

    with st.sidebar:
        # ── Planeur ───────────────────────────────────────────────────────
        st.subheader("Planeur")
        masse   = st.number_input("Masse totale [kg]",   100.0, 600.0, 350.0, step=5.0)
        surface = st.number_input("Surface alaire [m²]",   5.0,  25.0,   9.80, step=0.1)
        b       = st.number_input("Envergure [m]",          8.0,  30.0,  15.0, step=0.5)

        st.divider()
        st.subheader("Cas de charge")
        n = st.number_input("Facteur de charge n", -3.0, 7.0, 5.3, step=0.1,
                            help="5.3 = limite positif JAR-22 · -2.65 = limite négatif")

        st.divider()
        st.subheader("Empennage horizontal (EH)")
        rzeh = st.number_input(
            "Force aéro EH rzeh [N]", -2000.0, 2000.0, 0.0, step=10.0,
            help=("Effort aérodynamique sur l'EH (positif = vers le haut).\n"
                  "rza = n·m·g − rzeh (MECAVOL.PAS).")
        )

        st.divider()
        st.subheader("Structure demi-aile")
        masse_structure = st.number_input(
            "Masse structure [kg]", 0.0, 150.0, 52.0, step=1.0,
            help="Aile + équipements fixes intégrés (H201B : 51 kg aile + 1 kg einbauten = 52 kg)"
        )

        st.divider()
        st.subheader("Lest en eau")
        masse_ballast = st.number_input(
            "Lest demi-aile [kg]", 0.0, 100.0, 18.0, step=1.0,
            help="H201B : 36 kp total → 18 kg par demi-aile (dossier p.7)"
        )
        y_ballast = st.number_input(
            "Position y lest [m]", 0.0, 7.0, 1.0, step=0.1,
            help="Barycentre du lest en envergure"
        )

        st.divider()
        st.subheader("Masse distribuée additionnelle")
        masse_dist_add = st.number_input(
            "Masse distribuée [kg]", 0.0, 50.0, 0.0, step=0.5,
            help="Masse répartie uniformément sur la demi-aile (ex. panneaux solaires collés)"
        )

        st.divider()
        st.subheader("Charges concentrées")
        st.caption("Jusqu'à 3 masses ponctuelles (moteur, batteries, etc.)")
        charges_conc = []
        labels = ["Charge 1", "Charge 2", "Charge 3"]
        for k, lbl in enumerate(labels):
            with st.expander(lbl, expanded=(k == 0)):
                m_k = st.number_input(f"Masse [kg]",    0.0, 50.0, 0.0, step=0.5, key=f"mc_m{k}")
                y_k = st.number_input(f"Position y [m]", 0.0, b/2, min(2.5, b/2), step=0.1, key=f"mc_y{k}")
                n_k = st.text_input("Libellé", lbl, key=f"mc_n{k}")
                charges_conc.append({'masse': m_k, 'y': y_k, 'label': n_k})

    # ── Sauvegarde des paramètres pour EFFORTS ────────────────────────────
    st.session_state['mecavol_params'] = {
        'masse': masse, 'surface': surface, 'b': b, 'n': n,
        'masse_structure': masse_structure,
        'masse_dist_add': masse_dist_add,
        'charges_conc': charges_conc,
        'rzeh': rzeh,
        'masse_ballast': masse_ballast, 'y_ballast': y_ballast,
    }

    # ── Calcul ────────────────────────────────────────────────────────────
    res = compute_mecavol(
        masse, surface, b, n,
        masse_structure, masse_dist_add,
        charges_conc,
        rzeh=rzeh,
        masse_ballast=masse_ballast, y_ballast=y_ballast
    )

    # ── Contrainte masse additionnelle vs lest ────────────────────────────
    masse_conc_totale = sum(cc['masse'] for cc in charges_conc)
    masse_add_totale  = masse_dist_add + masse_conc_totale
    if masse_ballast > 0:
        marge = masse_ballast - masse_add_totale
        if marge >= 0:
            st.success(
                f"Masses additionnelles = {masse_add_totale:.1f} kg ≤ lest = {masse_ballast:.1f} kg "
                f"— marge : {marge:.1f} kg"
            )
        else:
            st.error(
                f"Masses additionnelles = {masse_add_totale:.1f} kg > lest = {masse_ballast:.1f} kg "
                f"— dépassement : {-marge:.1f} kg"
            )

    # ── Métriques ─────────────────────────────────────────────────────────
    st.subheader("Résultats à l'emplanture")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portance aile rza", f"{res['rza']/1000:.2f} kN",
              help=f"rza = n·m·g − rzeh = {n*masse*9.81:.0f} − {rzeh:.0f} N")
    c2.metric("T à l'emplanture",  f"{res['T'][0]/1000:.2f} kN")
    c3.metric("M à l'emplanture",  f"{res['M'][0]/1000:.2f} kN·m")
    c4.metric("M ultime (×1.5)",   f"{res['M_ultime'][0]/1000:.2f} kN·m")

    if rzeh != 0:
        delta_pct = abs(rzeh) / (n * masse * 9.81) * 100
        st.info(
            f"EH rzeh = {rzeh:+.0f} N ({delta_pct:.1f}% de n·m·g) — "
            f"{'moment majoré' if rzeh < 0 else 'moment minoré'}."
        )

    st.divider()
    fig = plot_charges(res)
    st.pyplot(fig)
    plt.close(fig)

    # ── Export vers EFFORTS ───────────────────────────────────────────────
    st.divider()
    st.subheader("Données transmises au module EFFORTS")
    st.info(
        f"**M à l'emplanture** = {res['M'][0]/1000:.3f} kN·m · "
        f"**M ultime** = {res['M_ultime'][0]/1000:.3f} kN·m · "
        f"**T à l'emplanture** = {res['T'][0]/1000:.3f} kN"
    )

    with st.expander("Tableau M(y) et T(y)"):
        import pandas as pd
        step = max(len(res["y"]) // 20, 1)
        idx  = np.arange(0, len(res["y"]), step)
        df = pd.DataFrame({
            "y [m]":          np.round(res["y"][idx], 3),
            "l_net [N/m]":    np.round(res["l_net"][idx], 1),
            "T [N]":          np.round(res["T"][idx], 1),
            "M [N·m]":        np.round(res["M"][idx], 1),
            "M_ultime [N·m]": np.round(res["M_ultime"][idx], 1),
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
