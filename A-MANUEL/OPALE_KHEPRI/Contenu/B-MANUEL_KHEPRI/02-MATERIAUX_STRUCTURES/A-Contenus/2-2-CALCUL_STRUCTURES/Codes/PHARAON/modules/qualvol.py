"""
Module Qualité de vol — Stabilité longitudinale
Fidèle à MECAVOL.PAS (Prodhomme, 1991)

Calcule :
  - CZα PSE et EH (Diederich / ligne portante)
  - Gradient de déflexion dε/dα
  - Foyer PSE (aile + fuselage)
  - Foyer complet gouverne bloquée (3 méthodes)
  - Foyer complet gouverne libre (2 méthodes)
  - Cmα, Cm0
  - Marge de stabilité
  - Plage de centrage

Sources :
  MECAVOL.PAS (Prodhomme, 1991) — formules exactes
  Dossier de calcul H201B (Glasflügel) — données géométriques via datas.xlsx
  NASA TN D-8324 (Somers, 1977) — CZα profil FX-66-17AII-182
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

# ─── Données H201B par défaut ─────────────────────────────────────────────────
# Source : datas.xlsx (saisie manuelle depuis dossier de calcul Glasflügel)
_H201B_EH = {
    'Ancien': {
        'S_EH':   1.00,   # surface EH [m²]
        'b_EH':   2.50,   # envergure EH [m]
        'l_EH':   0.421,  # MAC EH [m]
        'lbd_EH': 6.25,   # allongement
        'lv':     3.571,  # bras de levier foyer aile → foyer EH [m]  (γ_VSP dossier)
        'ca_max': 3.90,   # pente portance EH [rad⁻¹]
    },
    'TM 201-5': {
        'S_EH':   1.16,
        'b_EH':   2.50,
        'l_EH':   0.468,
        'lbd_EH': 5.38,
        'lv':     3.529,  # γ_VSP dossier calcul
        'ca_max': 3.85,
    },
}

_H201B_WING = {
    'S':      9.80,    # surface alaire [m²]
    'b':     15.00,    # envergure [m]
    'l_m':    0.653,   # MAC [m]
    'l_E':    0.69,    # corde de référence (datum) [m]
    'lbd':   23.0,     # allongement
    'ge':     0.40,    # effilement
    'fa':     0.25,    # foyer aile / MAC (25% — standard lifting-line)
    'cza':    6.05,    # CZα 2D [rad⁻¹] — NASA TN D-8324
    'alpha0': -3.7,    # incidence portance nulle [°] — NASA TN D-8324
}

_H201B_FUS = {
    'l_nez':  0.80,   # longueur nez [m]
    'l_c':    1.40,   # longueur corps [m]
    'l_a':    4.00,   # longueur arrière [m]
    'd':      0.69,   # diamètre moyen (ellipse) [m]  = (B+H)/2 = (0.575+0.8)/2
    'Sw':     8.00,   # surface mouillée fuselage [m²]  (estimé)
}

_H201B_CG = {
    'xcg_min': 35.4,  # % l_E — Flight & Service Manual p.16 : 9,6 in = 244 mm / 690 mm
    'xcg_max': 50.4,  # % l_E — Flight & Service Manual p.16 : 13,7 in = 348 mm / 690 mm
}


# ─── Calcul principal ──────────────────────────────────────────────────────────
def compute_qualvol(p: dict) -> dict:
    """
    Reproduit fidèlement la procédure `calcul` de MECAVOL.PAS (Prodhomme, 1991).

    Paramètres (dict p) :
      Aile  : S, l_m, lbd, ge, fa, cza (CZα 2D), alpha0 [°]
      EH    : S_EH, l_EH, lbd_EH, lv (bras), fa_eh (foyer EH/%l_EH), eta_EH, ih [°]
      Fus   : cmafus_coef (1.5 par défaut — formule MECAVOL)
      Vol   : xcg [% l_m], hh (dist. perpend. plans MAC [m])

    Retourne : dict avec tous les résultats intermédiaires et finaux.
    """
    # ── Dépaquetage ──────────────────────────────────────────────────────────
    S      = p['S'];      l_m   = p['l_m'];   lbd  = p['lbd']
    ge     = p['ge'];     fa    = p['fa'];     cza  = p['cza']
    alpha0 = np.radians(p['alpha0'])

    S_EH   = p['S_EH'];   l_EH  = p['l_EH'];  lbd_EH = p['lbd_EH']
    lv     = p['lv']      # bras de levier foyer aile → foyer EH [m]
    fa_eh  = p['fa_eh']   # foyer EH [fraction de l_EH]
    eta_EH = p['eta_EH']  # rapport pressions dynamiques
    ih     = np.radians(p['ih'])   # calage EH [rad]
    hh     = p['hh']      # distance perpend. plans MAC [m]
    xcg    = p['xcg'] / 100.0     # en fraction de l_m
    cmafus_coef = p.get('cmafus_coef', 1.5)

    # ── CZα PSE (Diederich, MECAVOL ligne 907) ───────────────────────────────
    # czaa := 2*pi*lambdaa / (2 + sqrt(lambdaa²+4))
    czaa = 2 * np.pi * lbd / (2 + np.sqrt(lbd**2 + 4))

    # ── CZα EH ───────────────────────────────────────────────────────────────
    czaeh = 2 * np.pi * lbd_EH / (2 + np.sqrt(lbd_EH**2 + 4))

    # ── Gradient de déflexion dε/dα (MECAVOL lignes 905-908) ─────────────────
    # Paramètres géométriques r et m (Multhopp)
    # Dans MECAVOL : x2-x1 = distance nez→BA EH - nez→BA aile ≈ lv - fa_eh*l_EH + fa*l_m
    # Ici on utilise directement lv comme bras foyer→foyer, donc :
    r = 2 * lv * np.cos(alpha0) / p['b']
    m = 2 * (hh + lv * abs(np.sin(alpha0))) / p['b']
    desda = 1.75 * czaa / (np.pi * lbd * (ge * r)**0.25 * (1 + abs(m)))

    eps0 = (-np.degrees(alpha0)) * desda * np.pi / 180.0   # déflexion à portance nulle [rd]

    # ── Foyer PSE (aile + fuselage) ───────────────────────────────────────────
    # cmafus := 1.5 / S / l_m  (empirique MECAVOL — contribution déstabilisante fuselage)
    cmafus = cmafus_coef / S / l_m
    fpse = fa - cmafus / czaa    # en fraction de l_m

    # ── Paramètres aérodynamiques complets ───────────────────────────────────
    cz0pse   = (-np.degrees(alpha0)) * czaa * np.pi / 180.0
    czqpse   = czaa * (fpse - xcg)
    # Notation fidèle MECAVOL.PAS :
    #   lv          = x2-x1 + f1eh*cmaeh - fa*cma  (foyer_aile → foyer_EH)
    #   lv + fa*l_m = x2-x1 + f1eh*cmaeh            (BA_aile → foyer_EH)
    arm_ba_to_eh  = lv + fa * l_m         # x2-x1+f1eh*cmaeh [m]
    arm_cg_to_eh  = lv + fa * l_m - xcg * l_m   # x2-x1+f1eh*cmaeh-xcg*cma [m]

    cz0total = cz0pse + (ih - eps0) * czaeh * eta_EH * S_EH / S
    czatotal = czaa + czaeh * eta_EH * S_EH / S * (1 - desda)
    # MECAVOL : czqtotal := czqpse + czaeh*(f1eh*cmaeh - xcg*cma + x2-x1)/cma * etaeh*sweh/sr
    czqtotal = czqpse + czaeh * arm_cg_to_eh / l_m * eta_EH * S_EH / S
    czdm     = 3.0   # pente gouverne profondeur [rad⁻¹] — constante MECAVOL
    czdmtotal = czdm * eta_EH * S_EH / S

    # ── Foyers gouverne bloquée (3 méthodes, MECAVOL lignes 980-993) ─────────
    # Méthode 1 : ftotgb1 := fa + (f1eh*cmaeh-fa*cma+x2-x1)*sweh/sr*0.4/cma
    #                       = fa + lv * S_EH/S * 0.4/l_m
    ftotgb1 = fa + lv * S_EH / S * 0.4 / l_m

    # Méthode 2 : ftotgb2 := (fpse*czaa + (x2-x1+f1eh*cmaeh)*czaeh*(1-desda)*sweh/sr/cma)
    #                        / (czaa + czaeh*(1-desda)*sweh/sr)
    num2 = fpse * czaa + arm_ba_to_eh * czaeh * (1 - desda) * S_EH / S / l_m
    den2 = czaa + czaeh * (1 - desda) * S_EH / S
    ftotgb2 = num2 / den2 if den2 != 0 else fpse

    # Méthode 3 : ftotgb3 := (fpse + czaeh/czaa*etaeh*sweh/sr*(x2-x1+f1eh*cmaeh)/cma*(1-desda))
    #                        / (1 + czaeh/czaa*etaeh*sweh/sr*(1-desda))
    k3 = czaeh / czaa * eta_EH * S_EH / S * arm_ba_to_eh / l_m * (1 - desda)
    ftotgb3 = (fpse + k3) / (1 + czaeh / czaa * eta_EH * S_EH / S * (1 - desda))

    # ── Foyers gouverne libre (2 méthodes, MECAVOL lignes 999-1006) ──────────
    # ftotgl1 := ftotgb - sweh/sr*etaeh*(x2-x1+f1eh*cmaeh-xcg*cma)/cma * czdm/czatotal*0.4*(1-desda)
    k_gl = S_EH / S * eta_EH * arm_cg_to_eh / l_m
    ftotgl1 = ftotgb2 - k_gl * czdm / czatotal * 0.4 * (1 - desda)
    # ftotgl2 := ftotgb + (fa-ftotgb)*(czdm/czaeh*0.4)
    ftotgl2 = ftotgb2 + (fa - ftotgb2) * (czdm / czaeh * 0.4)

    # ── Coefficients de moment ────────────────────────────────────────────────
    # Moment aile / bord d'attaque
    cm0a  = fa * cz0pse
    cmaa  = fa * czaa
    # PSE / bord d'attaque
    cmapse = cmaa + cmafus
    cm0pse = -cmapse * alpha0   # ≈ -cmapse * α0_rad
    # Complet / CG (MECAVOL lignes 1027-1032)
    # cmdm_arm := etaeh*sweh/sr*(f1eh*cmaeh-xcg*cma+x2-x1)/cma
    cm0pse_cg = cm0pse - xcg * cz0pse
    cmdm_arm  = eta_EH * S_EH / S * arm_cg_to_eh / l_m
    cm0       = cm0pse_cg + cz0pse * (xcg - fpse) + cmdm_arm * czaeh * eps0
    cm0       = cm0 + xcg * cz0pse
    cmdm      = -cmdm_arm * czdm

    # Cmα complet = (xcg - ftotgb) * CZα_total  (MECAVOL ligne 1032)
    ftotgb = ftotgb2      # valeur retenue = méthode 2 (méthode pondérée)
    ftotgl = ftotgl1      # valeur retenue = méthode 1
    cmalpha = (xcg - ftotgb) * czatotal

    # ── Marge de stabilité ────────────────────────────────────────────────────
    marge_gb = (ftotgb - xcg) * 100   # % l_m  (positif = stable)
    marge_gl = (ftotgl - xcg) * 100

    return {
        # Intermédiaires
        'czaa': czaa, 'czaeh': czaeh,
        'desda': desda, 'eps0': eps0,
        'cmafus': cmafus,
        'cz0pse': cz0pse, 'czqpse': czqpse,
        'cz0total': cz0total, 'czatotal': czatotal,
        'czqtotal': czqtotal, 'czdmtotal': czdmtotal,
        # Foyers [% l_m]
        'fpse':    fpse   * 100,
        'ftotgb1': ftotgb1 * 100,
        'ftotgb2': ftotgb2 * 100,
        'ftotgb3': ftotgb3 * 100,
        'ftotgb':  ftotgb  * 100,
        'ftotgl1': ftotgl1 * 100,
        'ftotgl2': ftotgl2 * 100,
        'ftotgl':  ftotgl  * 100,
        # Moments
        'cm0a': cm0a, 'cmaa': cmaa,
        'cm0pse': cm0pse, 'cmapse': cmapse,
        'cm0': cm0, 'cmalpha': cmalpha, 'cmdm': cmdm,
        # Stabilité
        'xcg_pct': xcg * 100,
        'marge_gb': marge_gb,
        'marge_gl': marge_gl,
    }


# ─── Graphique plage de centrage ──────────────────────────────────────────────
def plot_centrage(r: dict, xcg_min: float, xcg_max: float) -> plt.Figure:
    """
    Représentation visuelle de la plage de centrage par rapport aux foyers.
    xcg_min / xcg_max : limites certifiées [% l_m]
    """
    fig, ax = plt.subplots(figsize=(10, 3.5))

    items = [
        ('Foyer PSE',          r['fpse'],    'tomato',     'o'),
        ('Foyer GB (méth. 2)', r['ftotgb2'], 'royalblue',  's'),
        ('Foyer GL (méth. 1)', r['ftotgl1'], 'seagreen',   '^'),
        ('CG courant',         r['xcg_pct'], 'black',      'D'),
    ]
    for label, val, color, mk in items:
        ax.axvline(val, color=color, lw=1.5, linestyle='--', alpha=0.7)
        ax.scatter([val], [0.5], color=color, marker=mk, s=80, zorder=5)
        ax.text(val, 0.65, f'{label}\n{val:.1f}%', color=color,
                ha='center', va='bottom', fontsize=8)

    # Plage certifiée
    ax.axvspan(xcg_min, xcg_max, alpha=0.35, color='gold', label=f'Plage certifiée [{xcg_min:.0f}–{xcg_max:.0f}% l_m]')

    ax.set_xlim(min(r['fpse'], xcg_min) - 3, max(r['ftotgb2'], xcg_max) + 3)
    ax.set_ylim(0, 1.2)
    ax.set_xlabel('Position [% l_m]', fontsize=10)
    ax.set_yticks([])
    ax.set_title('Plage de centrage — foyers et position CG', fontsize=11)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, axis='x', alpha=0.3)
    fig.tight_layout()
    return fig


def plot_cmalpha(r: dict, xcg_min: float, xcg_max: float, czatotal: float,
                 ftotgb: float) -> plt.Figure:
    """Cmα en fonction de la position CG."""
    xcg_range = np.linspace(xcg_min / 100, xcg_max / 100 * 1.3, 200)
    cmalpha_range = (xcg_range - ftotgb / 100) * czatotal

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(xcg_range * 100, cmalpha_range, 'royalblue', lw=2)
    ax.axhline(0, color='black', lw=0.8)
    ax.axvline(ftotgb, color='tomato', lw=1.5, linestyle='--',
               label=f'Foyer GB = {ftotgb:.1f}% l_m')
    ax.axvspan(xcg_min, xcg_max, alpha=0.35, color='gold',
               label=f'Plage certifiée [{xcg_min:.0f}–{xcg_max:.0f}%]')
    ax.scatter([r['xcg_pct']], [r['cmalpha']], color='black', zorder=5, s=60,
               label=f'CG courant → Cmα={r["cmalpha"]:.3f}')

    ax.set_xlabel('Position CG [% l_m]')
    ax.set_ylabel('Cmα [rad⁻¹]')
    ax.set_title('Coefficient Cmα en fonction de la position CG', fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


# ─── render() ─────────────────────────────────────────────────────────────────
def render():
    st.title("Module 7 — Qualité de vol")
    st.caption("Stabilité longitudinale · Foyers · Cmα · Plage de centrage — fidèle à MECAVOL.PAS (Prodhomme, 1991)")

    # ── Lire la géométrie d'aile si disponible ────────────────────────────────
    geo = st.session_state.get('geo_wing')
    if geo:
        A = geo['A']; trap = geo['trap']
        S_geo  = 2 * sum((((A[2*k+1][1]-A[2*k][1]) + (A[2*(k+1)+1][1]-A[2*(k+1)][1])) / 2
                          * (A[2*(k+1)][0] - A[2*k][0])) for k in range(trap)) / 1e6
        b_geo  = A[2*trap][0] * 2 / 1000.0
        lbd_geo = b_geo**2 / S_geo if S_geo > 0 else 23.0
        ge_geo  = ((A[2*trap+1][1] - A[2*trap][1]) / (A[1][1] - A[0][1])
                   if (A[1][1] - A[0][1]) > 0 else 0.4)
        cza_geo = geo['CZA'][2] if len(geo['CZA']) > 2 and geo['CZA'][2] != 0 else 6.05
        geo_loaded = True
    else:
        S_geo = _H201B_WING['S']; b_geo = _H201B_WING['b']
        lbd_geo = _H201B_WING['lbd']; ge_geo = _H201B_WING['ge']
        cza_geo = _H201B_WING['cza']
        geo_loaded = False

    with st.sidebar:
        st.subheader("Paramètres")

        if not geo_loaded:
            st.info("Aucune géométrie chargée — valeurs H201B par défaut.")

        # ── Sélection EH ──────────────────────────────────────────────────────
        st.markdown("**Empennage horizontal**")
        eh_variant = st.radio("Version EH", ['Ancien', 'TM 201-5'], horizontal=True)
        eh = _H201B_EH[eh_variant]

        # ── Aile ──────────────────────────────────────────────────────────────
        st.markdown("**Aile**")
        S     = st.number_input("Surface S [m²]",     2.0, 30.0, float(S_geo),   0.1)
        b     = st.number_input("Envergure b [m]",    5.0, 30.0, float(b_geo),   0.1)
        l_m   = st.number_input("MAC l_m [m]",        0.2, 2.0,  _H201B_WING['l_m'], 0.01)
        l_E   = st.number_input("Corde réf. l_E [m]", 0.2, 2.0,  _H201B_WING['l_E'], 0.01)
        lbd   = st.number_input("Allongement λ",      5.0, 40.0, float(lbd_geo), 0.5)
        ge    = st.number_input("Effilement η",       0.1, 1.0,  float(ge_geo),  0.01)
        fa_pct = st.number_input("Foyer aile [% l_m]", 20.0, 40.0, 25.0, 0.5)
        cza   = st.number_input("CZα aile [rad⁻¹]",  4.0, 8.0,  float(cza_geo), 0.05)
        alpha0 = st.number_input("α₀ portance nulle [°]", -8.0, 0.0, -3.7, 0.1)

        # ── EH ────────────────────────────────────────────────────────────────
        st.markdown("**Empennage horizontal**")
        S_EH   = st.number_input("Surface S_EH [m²]",       0.1, 5.0,  eh['S_EH'],   0.01)
        l_EH   = st.number_input("MAC EH l_EH [m]",         0.1, 1.5,  eh['l_EH'],   0.005)
        lbd_EH = st.number_input("Allongement EH λ_EH",     2.0, 15.0, eh['lbd_EH'], 0.05)
        lv     = st.number_input("Bras de levier l_v [m]",  1.0, 8.0,  eh['lv'],     0.01,
                                  help="Distance foyer aile → foyer EH")
        fa_eh_pct = st.number_input("Foyer EH [% l_EH]",    15.0, 40.0, 25.0, 0.5)
        eta_EH = st.number_input("η_EH (rapport pression)", 0.5, 1.0,  0.90, 0.01)
        ih_deg = st.number_input("Calage EH i_h [°]",       -5.0, 5.0,  1.0,  0.1)

        # ── Fuselage ──────────────────────────────────────────────────────────
        st.markdown("**Fuselage**")
        hh = st.number_input("Décalage vertical plans MAC [m]", 0.0, 1.0, 0.10, 0.01,
                               help="Distance perpendiculaire entre plan MAC aile et plan MAC EH")
        cmafus_coef = st.number_input("Coeff. fuselage (1.5 MECAVOL)", 0.5, 5.0, 1.5, 0.1,
                                       help="Empirique MECAVOL : cmafus = coeff / S / l_m")

        # ── CG ────────────────────────────────────────────────────────────────
        st.markdown("**Centre de gravité**")
        xcg_min_cert = _H201B_CG['xcg_min'] * l_E / l_m if l_m > 0 else 30.0
        xcg_max_cert = _H201B_CG['xcg_max'] * l_E / l_m if l_m > 0 else 45.0
        xcg = st.slider("Position CG [% l_m]", 20.0, 55.0,
                         float(round(xcg_min_cert + (xcg_max_cert - xcg_min_cert) / 2, 1)),
                         0.5)
        st.caption(f"Limites certifiées H201B : {xcg_min_cert:.1f}% – {xcg_max_cert:.1f}% l_m")

    # ── Calcul ────────────────────────────────────────────────────────────────
    params = {
        'S': S, 'b': b, 'l_m': l_m, 'lbd': lbd, 'ge': ge,
        'fa': fa_pct / 100.0, 'cza': cza, 'alpha0': alpha0,
        'S_EH': S_EH, 'l_EH': l_EH, 'lbd_EH': lbd_EH,
        'lv': lv, 'fa_eh': fa_eh_pct / 100.0,
        'eta_EH': eta_EH, 'ih': ih_deg, 'hh': hh,
        'xcg': xcg, 'cmafus_coef': cmafus_coef,
    }
    r = compute_qualvol(params)

    # ── Métriques clés ────────────────────────────────────────────────────────
    st.subheader("Résultats principaux")

    stable = r['marge_gb'] > 0
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Foyer PSE",        f"{r['fpse']:.1f} % l_m")
    col2.metric("Foyer complet GB", f"{r['ftotgb']:.1f} % l_m",
                help="Valeur retenue = méthode 2 (pondération CZα)")
    col3.metric("Marge stabilité GB",
                f"{r['marge_gb']:.1f} % l_m",
                delta="stable" if stable else "instable",
                delta_color="normal" if stable else "inverse")
    col4.metric("Cmα complet",      f"{r['cmalpha']:.4f} rad⁻¹",
                help="Négatif = stable en tangage")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CZα PSE",   f"{r['czaa']:.3f} rad⁻¹")
    col2.metric("CZα EH",    f"{r['czaeh']:.3f} rad⁻¹")
    col3.metric("dε/dα",     f"{r['desda']:.4f}")
    col4.metric("Foyer GL",  f"{r['ftotgl']:.1f} % l_m")

    st.divider()

    # ── Graphiques ────────────────────────────────────────────────────────────
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.subheader("Plage de centrage")
        fig_c = plot_centrage(r, xcg_min_cert, xcg_max_cert)
        st.pyplot(fig_c); plt.close(fig_c)
    with col_b:
        st.subheader("Cmα = f(CG)")
        fig_cm = plot_cmalpha(r, xcg_min_cert, xcg_max_cert, r['czatotal'], r['ftotgb'])
        st.pyplot(fig_cm); plt.close(fig_cm)

    st.divider()

    # ── Tableau foyers (3 méthodes) ───────────────────────────────────────────
    with st.expander("Détail des foyers — 3 méthodes gouverne bloquée", expanded=True):
        df_foyers = pd.DataFrame({
            'Foyer': ['PSE (aile + fuselage)', 'GB méthode 1', 'GB méthode 2 ★', 'GB méthode 3',
                      'GL méthode 1 ★', 'GL méthode 2'],
            '% l_m': [r['fpse'], r['ftotgb1'], r['ftotgb2'], r['ftotgb3'],
                      r['ftotgl1'], r['ftotgl2']],
            'Marge / CG [% l_m]': [r['fpse'] - r['xcg_pct'],
                                    r['ftotgb1'] - r['xcg_pct'],
                                    r['ftotgb2'] - r['xcg_pct'],
                                    r['ftotgb3'] - r['xcg_pct'],
                                    r['ftotgl1'] - r['xcg_pct'],
                                    r['ftotgl2'] - r['xcg_pct']],
        })
        df_foyers['% l_m']               = df_foyers['% l_m'].round(2)
        df_foyers['Marge / CG [% l_m]']  = df_foyers['Marge / CG [% l_m]'].round(2)
        st.dataframe(df_foyers, use_container_width=True, hide_index=True)
        st.caption("★ = valeur retenue par MECAVOL.PAS")

    # ── Tableau coefficients aéro ─────────────────────────────────────────────
    with st.expander("Coefficients aérodynamiques complets"):
        rows = [
            ("CZα PSE",           f"{r['czaa']:.4f} rad⁻¹",  "Diederich — MECAVOL ligne 907"),
            ("CZα EH",            f"{r['czaeh']:.4f} rad⁻¹", "Diederich — MECAVOL"),
            ("CZα total",         f"{r['czatotal']:.4f} rad⁻¹","aile + EH (1-dε/dα)"),
            ("dε/dα",             f"{r['desda']:.4f}",        "Multhopp — MECAVOL ligne 908"),
            ("ε₀",                f"{r['eps0']:.4f} rd",      "déflexion à portance nulle"),
            ("cmafus",            f"{r['cmafus']:.5f} /rad",  "contribution fuselage empirique"),
            ("Cz0 total",         f"{r['cz0total']:.4f}",     "portance nulle planeur"),
            ("Czδm total",        f"{r['czdmtotal']:.4f} /rd","efficacité gouverne profondeur"),
            ("Cm0 aile / BA",     f"{r['cm0a']:.4f}",         ""),
            ("Cmα aile / BA",     f"{r['cmaa']:.4f} /rd",     ""),
            ("Cm0 PSE / BA",      f"{r['cm0pse']:.4f}",       ""),
            ("Cmα PSE / BA",      f"{r['cmapse']:.4f} /rd",   "aile + fuselage"),
            ("Cm0 complet / CG",  f"{r['cm0']:.4f}",          ""),
            ("Cmα complet / CG",  f"{r['cmalpha']:.4f} /rd",  "(xcg-ftotgb)·CZα_total"),
            ("Cmδm / CG",         f"{r['cmdm']:.4f} /rd",     "efficacité gouverne"),
        ]
        df_aero = pd.DataFrame(rows, columns=['Grandeur', 'Valeur', 'Note'])
        st.dataframe(df_aero, use_container_width=True, hide_index=True)

    # ── Avertissements ────────────────────────────────────────────────────────
    st.divider()
    if not stable:
        st.error(f"⚠ Instabilité longitudinale : CG ({xcg:.1f}%) en avant du foyer ({r['ftotgb']:.1f}%). Cmα = {r['cmalpha']:.4f} > 0.")
    elif r['marge_gb'] < 5:
        st.warning(f"Marge de stabilité faible : {r['marge_gb']:.1f}% l_m (recommandé > 5%).")
    else:
        st.success(f"Stabilité satisfaisante : marge = {r['marge_gb']:.1f}% l_m, Cmα = {r['cmalpha']:.4f} rad⁻¹.")

    if xcg < xcg_min_cert or xcg > xcg_max_cert:
        st.warning(f"CG hors plage certifiée H201B ({xcg_min_cert:.1f}% – {xcg_max_cert:.1f}% l_m).")
