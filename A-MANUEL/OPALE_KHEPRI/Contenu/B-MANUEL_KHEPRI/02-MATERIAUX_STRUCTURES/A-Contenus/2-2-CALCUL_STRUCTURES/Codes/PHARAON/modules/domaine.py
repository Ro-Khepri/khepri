"""
Module DOMAINE — Domaine de vol (diagramme V-n)
Formules et paramètres — dossier de calcul Glasflügel H201B (pages 22-23)
Normes JAR-22 (planeurs) ou FAR/JAR-23 (avions)
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


RHO = 1.225   # kg/m³  masse volumique ISA niveau mer
G   = 9.81    # m/s²

# Facteurs de charge JAR-22 — procédure DATA de DOMAINE.PAS
NF_PLANEUR = [5.3, 4.0, -1.5, -2.65]   # NF[1..4]
NF_AVION   = [7.0, 7.0, -5.0, -5.0]


# ─────────────────────────────────────────────────────────────────────────────
# Calcul — fidèle à PROCEDURE DATA + CALVIT + DOMRAF de DOMAINE.PAS
# ─────────────────────────────────────────────────────────────────────────────

def compute_domaine(cat: str,
                    M: float, Mmax: float, Mmin: float,
                    Sref: float, LM: float,
                    Cxmin: float, Czmax: float, Czmaxdos: float,
                    CZA: float,
                    VNE_kmh: float = 249.0) -> dict:
    """
    Calcule les vitesses et paramètres du domaine de vol.

    Paramètres (identiques aux champs de saisie de DOMAINE.PAS) :
      cat      : 'A' avion  /  'U' ultra-léger ou planeur
      M        : masse d'essai [kg]
      Mmax     : masse maximale [kg]
      Mmin     : masse minimale [kg]
      Sref     : surface de référence — voilure prolongée dans fuselage [m²]
      LM       : longueur moyenne de la corde [m]  (= SMC / MAC)
      Cxmin    : coefficient de traînée minimum (polaire)
      Czmax    : CZ maximum positif
      Czmaxdos : CZ maximum en vol dos (valeur positive)
      CZA      : gradient de portance dCz/dα [rad⁻¹]
    """
    NF = NF_AVION if cat == 'A' else NF_PLANEUR

    # ── Paramètre de masse et facteur d'atténuation — PROCEDURE DATA ─────────
    MU   = (2 * M) / (Sref * RHO * LM * CZA)
    K    = (0.88 * MU) / (5.3 + MU)  # Formule DOMAINE.PAS — dynamique selon la masse d'essai M
    # K    = 0.665  # Facteur de réduction des rafales — valeur constructeur H201B p.22
    COEF = (K * RHO * CZA * Sref) / (2 * M * G)

    # ── Vitesses — PROCEDURE CALVIT ──────────────────────────────────────────
    VS   = np.sqrt(2 * M    * G / (RHO * Sref * Czmax))
    VS1  = np.sqrt(2 * Mmax * G / (RHO * Sref * Czmax))
    VS2  = np.sqrt(2 * Mmin * G / (RHO * Sref * Czmax))

    VSD  = np.sqrt(2 * M    * G / (RHO * Sref * Czmaxdos))
    VS1D = np.sqrt(2 * Mmax * G / (RHO * Sref * Czmaxdos))
    VS2D = np.sqrt(2 * Mmin * G / (RHO * Sref * Czmaxdos))

    VAM  = VS  * np.sqrt(NF[0])          # vitesse manœuvre à masse M
    VA   = VS1 * np.sqrt(NF[0])          # vitesse manœuvre à masse Mmax
    VAD  = VSD * np.sqrt(-NF[3])         # vitesse manœuvre vol dos

    # VD : formule dossier de calcul Glasflügel H201B, p.23 — V_D = 18 * (W / (S*Cxmin))^(1/3)
    # Cette formule donne une vitesse en km/h ; dans le code Python, toutes les vitesses sont
    # traitées en m/s. La conversion s'effectue avec 18/3.6 = 5.
    # Pour H201B : V_D = 5 * (350 / (9.80 * 0.0113))^(1/3) = 73.3 m/s (≈ 264 km/h).
    VD_bvs = 5.0 * (M / (Sref * Cxmin)) ** (1.0 / 3.0)  # formule BVS en m/s
    VD_jar = (VNE_kmh / 3.6) / 0.9                        # contrainte JAR-22 : VD ≥ VNE/0.9
    VD     = max(VD_bvs, VD_jar)                           # on retient la plus contraignante

    VB   = VA   # DOMAINE.PAS : VB := VA  (simplified)

    VG   = VSD * np.sqrt(-NF[3])   # transition décrochage–manœuvre dos

    # ── Points ABCD du domaine de manœuvre ───────────────────────────────────
    # A  : (VAM, NF[0])          sommet courbe décrochage positive
    # B  : (VD,  NF[1])          coin supérieur droit
    # C  : (VD,  NF[2])          coin inférieur droit
    # D  : (VG,  NF[3])          sommet courbe décrochage négative

    # ── Droites de rafale — PROCEDURE DOMRAF ─────────────────────────────────
    # n = 1 + COEF * 15  * V   (rafale 15 m/s — VB-level)
    # n = 1 + COEF * 7.5 * V   (rafale 7.5 m/s — VD-level)
    NR1 = 1 + COEF * 15  * VA   # gust line 15 m/s évaluée à VA
    NR2 = 1 + COEF * 7.5 * VD   # gust line 7.5 m/s évaluée à VD
    NR3 = 1 - COEF * 7.5 * VD   # gust line -7.5 m/s à VD
    NR4 = 1 - COEF * 15  * VA   # gust line -15 m/s à VA

    return {
        # paramètres de calcul
        "NF": NF, "MU": MU, "K": K, "COEF": COEF,
        # vitesses de décrochage [m/s]
        "VS": VS, "VS1": VS1, "VS2": VS2,
        "VSD": VSD, "VS1D": VS1D, "VS2D": VS2D,
        # vitesses caractéristiques [m/s]
        "VAM": VAM, "VA": VA, "VAD": VAD,
        "VB": VB, "VD": VD, "VG": VG,
        # points des droites de rafale
        "NR1": NR1, "NR2": NR2, "NR3": NR3, "NR4": NR4,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tracé — fidèle à PROCEDURE DOMAIN + DOMRAF de DOMAINE.PAS
# ─────────────────────────────────────────────────────────────────────────────

def _v_range(VD):
    return np.linspace(0, VD * 1.05, 600)


def plot_domaine(res: dict, mode: str = "combined") -> plt.Figure:
    """
    Trace le domaine de vol.
    mode : 'manoeuver'  — domaine de manœuvres seulement  (option 2)
           'rafales'    — domaine de rafales seulement     (option 3)
           'combined'   — les deux superposés              (option 4)
    """
    NF   = res["NF"]
    VS   = res["VS"];   VSD  = res["VSD"]
    VAM  = res["VAM"];  VD   = res["VD"];  VG = res["VG"]
    COEF = res["COEF"]; VA   = res["VA"]
    NR1  = res["NR1"];  NR2  = res["NR2"]
    NR3  = res["NR3"];  NR4  = res["NR4"]

    V = _v_range(VD)
    fig, ax = plt.subplots(figsize=(11, 7))

    # ── Domaine de manœuvres (PROCEDURE DOMAIN) ───────────────────────────────
    if mode in ("manoeuver", "combined"):

        # Courbe de décrochage positive : n = (V/VS)²  jusqu'à VAM
        mask_s  = V <= VAM
        n_s_pos = np.where(mask_s, (V / VS) ** 2, np.nan)
        # Branche horizontale NF[0], puis ligne inclinée de VAM à VD
        # puis descente verticale à 0
        v_mano_u = np.array([VAM, VD, VD])
        n_mano_u = np.array([NF[0],
                              NF[0] + (NF[1] - NF[0]) / (VD - VAM) * (VD - VAM),
                              0])
        # = [NF[0], NF[1], 0]

        # Courbe de décrochage négative : n = -(V/VSD)² jusqu'à VG
        mask_sn = V <= VG
        n_s_neg = np.where(mask_sn, -(V / VSD) ** 2, np.nan)
        v_mano_d = np.array([VG, VD, VD])
        n_mano_d = np.array([NF[3], NF[2], 0])

        ax.plot(V[mask_s],  n_s_pos[mask_s],  color="royalblue", lw=2)
        ax.plot(v_mano_u,   n_mano_u,          color="royalblue", lw=2,
                label="Domaine de manœuvres")
        ax.plot(V[mask_sn], n_s_neg[mask_sn],  color="royalblue", lw=2)
        ax.plot(v_mano_d,   n_mano_d,          color="royalblue", lw=2)

        # Remplissage
        v_env_u = np.concatenate([V[mask_s],  v_mano_u])
        n_env_u = np.concatenate([n_s_pos[mask_s], n_mano_u])
        v_env_d = np.concatenate([V[mask_sn], v_mano_d])
        n_env_d = np.concatenate([n_s_neg[mask_sn], n_mano_d])
        ax.fill(v_env_u, n_env_u, alpha=0.10, color="royalblue")
        ax.fill(v_env_d, n_env_d, alpha=0.10, color="royalblue")

        # Labels ABCD
        ax.annotate("A", (VAM, NF[0]),   fontsize=10, color="royalblue",
                    xytext=(VAM + 0.5, NF[0] + 0.15))
        ax.annotate("B", (VD,  NF[1]),   fontsize=10, color="royalblue",
                    xytext=(VD  + 0.5, NF[1] + 0.10))
        ax.annotate("C", (VD,  NF[2]),   fontsize=10, color="royalblue",
                    xytext=(VD  + 0.5, NF[2] - 0.20))
        ax.annotate("D", (VG,  NF[3]),   fontsize=10, color="royalblue",
                    xytext=(VG  + 0.5, NF[3] - 0.20))

    # ── Domaine de rafales (PROCEDURE DOMRAF) ─────────────────────────────────
    if mode in ("rafales", "combined"):
        # Courbes de décrochage × 1.25  (domaine de rafales)
        n_raf_pos = np.where(V <= VAM, 1.25 * (V / VS)  ** 2, np.nan)
        n_raf_neg = np.where(V <= VG,  -1.25 * (V / VSD) ** 2, np.nan)
        ax.plot(V, n_raf_pos, color="tomato", lw=1.5, linestyle="--")
        ax.plot(V, n_raf_neg, color="tomato", lw=1.5, linestyle="--")

        # Droites de rafale — n = 1 ± COEF * U_g * V
        n_C = 1 + COEF * 15  * V   # rafale 15 m/s (VB)
        n_D = 1 + COEF * 7.5 * V   # rafale 7.5 m/s (VD)
        n_E = 1 - COEF * 7.5 * V   # rafale -7.5 m/s (VD)
        n_F = 1 - COEF * 15  * V   # rafale -15 m/s (VB)

        ax.plot(V, n_C, color="tomato", lw=1.5,
                label=f"Rafale 15 m/s  · n = 1 + {COEF*15:.5f}·V")
        ax.plot(V, n_D, color="orange", lw=1.2, linestyle="-.",
                label=f"Rafale 7.5 m/s · n = 1 + {COEF*7.5:.5f}·V")
        ax.plot(V, n_E, color="orange", lw=1.2, linestyle="-.")
        ax.plot(V, n_F, color="tomato", lw=1.5)

        # Points I..L sur le domaine de rafales (nœuds caractéristiques)
        ax.annotate("I",  (res["VS"],  0),      fontsize=9, color="tomato",
                    xytext=(res["VS"] + 0.3, 0.3))
        ax.annotate("J",  (VA, NR1),            fontsize=9, color="tomato",
                    xytext=(VA + 0.3, NR1 + 0.15))
        ax.annotate("K",  (VD, NR2),            fontsize=9, color="tomato",
                    xytext=(VD + 0.3, NR2 + 0.10))
        ax.annotate("L",  (res["VSD"], 0),      fontsize=9, color="tomato",
                    xytext=(res["VSD"] + 0.3, -0.4))
        ax.annotate("M",  (VA, NR4),            fontsize=9, color="tomato",
                    xytext=(VA + 0.3, NR4 - 0.25))
        ax.annotate("N",  (VD, NR3),            fontsize=9, color="tomato",
                    xytext=(VD + 0.3, NR3 - 0.20))

    # ── Axes et mise en forme ─────────────────────────────────────────────────
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(1, color="gray",  lw=0.5, linestyle=":")

    # Vitesses clés
    vit = {"VS1": res["VS1"], "VA": VA, "VD": VD}
    for lbl, v in vit.items():
        if v <= VD * 1.05:
            ax.axvline(v, color="gray", lw=0.8, linestyle=":")
            ax.text(v + 0.2, NF[0] * 0.95, lbl, fontsize=8, color="gray", va="top")

    ax.set_xlabel("Vitesse vraie V  [m/s]", fontsize=11)
    ax.set_ylabel("Facteur de charge  n", fontsize=11)
    nfmin = min(NF[2], NF[3]) - 0.5
    nfmax = NF[0] + 0.5
    ax.set_ylim(nfmin - 0.3, nfmax + 0.3)
    ax.set_xlim(0, VD * 1.08)
    titre_mode = {
        "manoeuver": "Domaine de manœuvres",
        "rafales":   "Domaine de rafales",
        "combined":  "Domaines de manœuvres et de rafales",
    }
    ax.set_title(titre_mode[mode] + "  —  JAR-22", fontsize=12)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Interface Streamlit — fidèle à l'écran SAISIE.FEN de DOMAINE.PAS
# ─────────────────────────────────────────────────────────────────────────────

def render():
    st.title("Module 4 — Domaine de vol (DOMAINE)")
    st.caption("Domaine de manœuvres et de rafales · JAR-22 / DOMAINE.PAS (Prodhomme 1990)")

    with st.sidebar:
        st.subheader("Caractéristiques du planeur")

        nom = st.text_input("Nom du planeur", value="H201B Libelle")

        cat = st.radio("Catégorie",
                       ["U", "A"],
                       format_func=lambda x: "Planeur / ULM (JAR-22)" if x == "U"
                                        else "Avion (JAR-23)",
                       horizontal=True)

        st.divider()
        st.caption("Masses")
        M    = st.number_input("Masse d'essai M  [kg]",  50.0, 1000.0, 350.0, step=5.0)
        Mmax = st.number_input("Masse maximale Mmax [kg]", 50.0, 1000.0, 350.0, step=5.0,
                                help="H201B : 350 kg avec ballast d'eau (Flight & Service Manual)")
        Mmin = st.number_input("Masse minimale Mmin [kg]", 50.0, 1000.0, 315.0, step=5.0,
                                help="H201B : 315 kg sans ballast d'eau (Flight & Service Manual)")

        st.divider()
        st.caption("Géométrie de la voilure")
        Sref = st.number_input("Surface de référence Sref [m²]", 1.0, 50.0, 9.80, step=0.1)
        LM   = st.number_input("Corde moyenne LM [m]",           0.3, 5.0,  0.653, step=0.01,
                                format="%.3f")

        st.divider()
        st.caption("Coefficients aérodynamiques")
        Cxmin    = st.number_input("CX minimum  Cxmin",         0.001, 0.100, 0.0113, step=0.0005,
                                   format="%.4f",
                                   help="H201B : 0.0113 — dossier de calcul Glasflügel, p.22")
        Czmax    = st.number_input("CZ max positif  Czmax",     0.50,  3.00,  1.40,   step=0.05)
        Czmaxdos = st.number_input("CZ max vol dos  Czmaxdos",  0.20,  2.00,  0.80,   step=0.05)
        CZA      = st.number_input("Gradient portance CZA [rad⁻¹]", 1.0, 10.0, 5.38, step=0.05,
                                   format="%.2f",
                                   help="H201B : 5.38 rad⁻¹ — dossier de calcul Glasflügel, p.27/29/30")

        st.divider()
        st.caption("Vitesses opérationnelles")
        VNE_kmh = st.number_input("VNE (Vitesse à ne jamais dépasser) [km/h]", 50.0, 400.0, 249.0, step=1.0,
                                  help="H201B : 155 mph = 249 km/h (Flight & Service Manual)")

    # ── Calcul ───────────────────────────────────────────────────────────────
    res = compute_domaine(cat, M, Mmax, Mmin, Sref, LM,
                          Cxmin, Czmax, Czmaxdos, CZA, VNE_kmh)

    NF = res["NF"]

    # ── Facteurs de charge JAR ────────────────────────────────────────────────
    st.subheader("Facteurs de charge limites")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("n+ manœuvre",   f"{NF[0]}")
    c2.metric("n+ rafale",     f"{NF[1]}")
    c3.metric("n− rafale",     f"{NF[2]}")
    c4.metric("n− manœuvre",   f"{NF[3]}")

    st.divider()

    # ── Vitesses caractéristiques (tableau type IMPVIT) ───────────────────────
    st.subheader(f"Tableau des vitesses — {nom}")

    def kmh(v): return f"{v * 3.6:.1f}"
    def ms(v):  return f"{v:.2f}"

    rows = [
        ("VS",    "Décrochage  (masse M)",        res["VS"]),
        ("VS1",   "Décrochage  (masse Mmax)",      res["VS1"]),
        ("VS2",   "Décrochage  (masse Mmin)",      res["VS2"]),
        ("VSD",   "Décrochage dos (masse M)",      res["VSD"]),
        ("VS1D",  "Décrochage dos (masse Mmax)",   res["VS1D"]),
        ("VS2D",  "Décrochage dos (masse Mmin)",   res["VS2D"]),
        ("VAM",   "Manœuvre (masse M)",            res["VAM"]),
        ("VA",    "Manœuvre (masse Mmax) — Point A", res["VA"]),
        ("VAD",   "Manœuvre dos",                  res["VAD"]),
        ("VD",    "Vitesse de calcul plongée",      res["VD"]),
    ]
    import pandas as pd
    df_v = pd.DataFrame(
        [(r[0], r[2]*3.6, r[2], r[1]) for r in rows],
        columns=["Point", "V [km/h]", "V [m/s]", "Description"]
    )
    df_v["V [km/h]"] = df_v["V [km/h]"].map("{:.1f}".format)
    df_v["V [m/s]"]  = df_v["V [m/s]"].map("{:.2f}".format)
    st.dataframe(df_v, use_container_width=True, hide_index=True)

    st.divider()

    # ── Paramètres PARAM (affiché comme dans DOMAINE.PAS) ────────────────────
    with st.expander("Paramètres de rafale — PROCEDURE PARAM"):
        st.markdown(f"""
| Paramètre | Valeur |
|-----------|--------|
| Paramètre de masse  **μ** | {res['MU']:.4f} |
| Facteur d'atténuation  **k** | {res['K']:.4f} |
| Droite de rafale 7.5 m/s | n = 1 + **{res['COEF']*7.5:.6f}** × V |
| Droite de rafale 15 m/s  | n = 1 + **{res['COEF']*15:.6f}** × V |
""")
        st.caption("Formules : μ = 2M / (Sref·ρ·LM·CZA)   ;   k = 0.88μ / (5.3+μ)   ;   coef = k·ρ·CZA·Sref / (2·M·g)")

    st.divider()

    # ── Diagramme V-n ─────────────────────────────────────────────────────────
    st.subheader("Diagramme de domaine de vol V-n")
    mode = st.radio("Affichage",
                    ["combined", "manoeuver", "rafales"],
                    format_func=lambda x: {
                        "combined":  "Manœuvres + Rafales (option 4)",
                        "manoeuver": "Domaine de manœuvres (option 2)",
                        "rafales":   "Domaine de rafales   (option 3)",
                    }[x],
                    horizontal=True)

    fig = plot_domaine(res, mode=mode)
    st.pyplot(fig)
    plt.close(fig)

    # ── Points des droites de rafale ──────────────────────────────────────────
    with st.expander("Points caractéristiques du domaine de rafales (I..N)"):
        df_raf = pd.DataFrame([
            ("I",  res["VS"],   0,       "Vitesse de décrochage positive"),
            ("J",  res["VA"],   res["NR1"], "Gust 15 m/s à VA (sommet)"),
            ("K",  res["VD"],   res["NR2"], "Gust 7.5 m/s à VD"),
            ("L",  res["VSD"],  0,          "Vitesse de décrochage dos"),
            ("M",  res["VA"],   res["NR4"], "Gust -15 m/s à VA (creux)"),
            ("N",  res["VD"],   res["NR3"], "Gust -7.5 m/s à VD"),
        ], columns=["Point", "V [m/s]", "n", "Description"])
        df_raf["V [km/h]"] = (df_raf["V [m/s]"] * 3.6).map("{:.1f}".format)
        df_raf["V [m/s]"]  = df_raf["V [m/s]"].map("{:.2f}".format)
        df_raf["n"]        = df_raf["n"].map("{:.3f}".format)
        st.dataframe(df_raf[["Point","V [km/h]","V [m/s]","n","Description"]],
                     use_container_width=True, hide_index=True)
