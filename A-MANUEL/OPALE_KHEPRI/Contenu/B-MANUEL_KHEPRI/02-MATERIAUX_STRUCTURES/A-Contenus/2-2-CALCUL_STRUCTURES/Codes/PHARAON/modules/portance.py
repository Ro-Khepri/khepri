"""
Module Portance — Polaire elliptique (hypothèse de Prandtl, e=1)
Cx = Cx0 + ki·Cz²   avec ki = 1/(π·λ)

Loi de corde / YBA / YBF / CZα BIDIM : N=30 stations cosinus
Fidèle à EFFORT.PAS (Prodhomme, 1990) — procédures ligne0 / CORDE.
"""

import bisect
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd


def compute_polaire(lbd: float, cx0: float, masse: float, surface: float,
                    h: float, alpha0_deg: float = 0.0):
    """
    Calcule la polaire parabolique et les courbes dérivées.

    Paramètres
    ----------
    lbd        : allongement λ = b²/S
    cx0        : traînée parasite Cx0
    masse      : masse [kg]
    surface    : surface alaire S [m²]
    h          : altitude [m]
    alpha0_deg : incidence de portance nulle [°] (≈0 pour profil symétrique)
    """
    g    = 9.81
    W    = masse * g
    rho0 = 1.225
    T0, TH = 288.15, 0.0065
    rho  = rho0 * (1 + TH * h / T0) ** (-4.26)

    ki = 1.0 / (np.pi * lbd)                     # coeff traînée induite (e=1)
    dcz_dalpha = 2 * np.pi / (1 + 2 / lbd)       # pente portance [rad⁻¹] — lifting line

    # ── Points caractéristiques ────────────────────────────────────────────
    cz_fmax   = np.sqrt(cx0 / ki)                 # Cz à finesse max
    cx_fmax   = 2 * cx0                           # Cx à finesse max
    f_max     = cz_fmax / cx_fmax                 # finesse maximale
    v_fmax    = np.sqrt(2 * W / (rho * surface * cz_fmax))   # vitesse finesse max [m/s]

    # Taux de chute minimal : w = V·sin(γ) ≈ V/f → min(V/f) = min(V·Cx/Cz)
    # wmin à Cz = sqrt(3·Cx0/ki) — résultat analytique
    cz_wmin   = np.sqrt(3 * cx0 / ki)
    cx_wmin   = cx0 + ki * cz_wmin**2
    f_wmin    = cz_wmin / cx_wmin
    v_wmin    = np.sqrt(2 * W / (rho * surface * cz_wmin))
    w_min     = v_wmin / f_wmin                   # taux de chute [m/s]

    # ── Plage de Cz ────────────────────────────────────────────────────────
    cz_arr = np.linspace(0.05, 1.6, 400)
    cx_arr = cx0 + ki * cz_arr**2
    f_arr  = cz_arr / cx_arr
    v_arr  = np.sqrt(2 * W / (rho * surface * cz_arr))   # vitesse en m/s
    w_arr  = v_arr / f_arr                                 # taux de chute m/s

    # Incidence correspondante
    alpha0 = np.radians(alpha0_deg)
    alpha_arr = cz_arr / dcz_dalpha + alpha0              # rad
    alpha_deg = np.degrees(alpha_arr)

    return {
        "ki": ki, "cx0": cx0, "lbd": lbd, "rho": rho, "W": W, "S": surface,
        "dcz_dalpha": dcz_dalpha,
        "cz_fmax": cz_fmax, "cx_fmax": cx_fmax, "f_max": f_max,
        "v_fmax": v_fmax,
        "cz_wmin": cz_wmin, "cx_wmin": cx_wmin, "f_wmin": f_wmin,
        "v_wmin": v_wmin, "w_min": w_min,
        "cz": cz_arr, "cx": cx_arr, "finesse": f_arr,
        "vitesse": v_arr, "taux_chute": w_arr, "alpha_deg": alpha_deg,
    }


def compute_loi_corde(wing: dict) -> pd.DataFrame:
    """
    Calcule la loi de corde, YBA, YBF, CZα aux N=30 stations cosinus.

    Reproduit fidèlement la procédure CORDE de EFFORT.PAS (Prodhomme) :
      N=30, O=π/(2N), W_i = O·i, Y_i = B·cos(W_i)
      Interpolation linéaire par trapèze de la géométrie du plan de forme.

    Paramètres
    ----------
    wing : dict issu de geoaile (session_state['geo_wing'])
           Clés nécessaires : 'A', 'CZA', 'trap', 'C'

    Retourne
    --------
    DataFrame : Y [m], W [rd], Corde [m], YBA [m], YBF [m], CZα
                (30 lignes, de l'emplanture vers le saumon)
    """
    A       = wing['A']
    CZA_arr = wing['CZA']   # [CZA-1=CZAXE, CZA0=CZEMP, CZA1, ..., CZA_trap]
    trap    = wing['trap']
    XI      = wing['C'] / 1000.0   # demi-largeur fuselage [m] (C est déjà la demi-largeur en mm)

    # ── Sections (en mètres) ─────────────────────────────────────────────
    n_sec   = trap + 1
    X_sec   = [A[2*k][0]   / 1000.0 for k in range(n_sec)]   # envergure
    YBA_sec = [A[2*k][1]   / 1000.0 for k in range(n_sec)]   # BA
    YBF_sec = [A[2*k+1][1] / 1000.0 for k in range(n_sec)]   # BF

    B = X_sec[trap]   # demi-envergure [m]
    if B <= 0:
        return pd.DataFrame()

    # ── Coefficients linéaires par trapèze (EFFORT.PAS A1..F3) ──────────
    # Trapèze k (0-based, 0=innermost) : X_sec[k] → X_sec[k+1]
    # CZA :
    #   k=0 : inner = CZA_arr[0] (CZAXE),  outer = CZA_arr[2] (CZA1)
    #   k≥1 : inner = CZA_arr[k+1],         outer = CZA_arr[k+2]
    coeffs = []
    for k in range(trap):
        xi, xo = X_sec[k], X_sec[k+1]
        dx_inv  = 1.0 / (xi - xo) if abs(xi - xo) > 1e-9 else 0.0   # (XA-XB)⁻¹

        a = (YBA_sec[k] - YBA_sec[k+1]) * dx_inv
        b = YBA_sec[k+1] - a * xo

        c = (YBF_sec[k] - YBF_sec[k+1]) * dx_inv
        d = YBF_sec[k+1] - c * xo

        cza_i = CZA_arr[0]      if k == 0 else CZA_arr[k+1]
        cza_o = CZA_arr[k+2]
        e = (cza_o - cza_i) / (xo - xi) if abs(xo - xi) > 1e-9 else 0.0
        f = cza_o - e * xo

        coeffs.append({'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f})

    CZAXE = CZA_arr[0]
    W0    = float(np.arccos(np.clip(XI / B, -1.0, 1.0)))   # frontière fuselage

    # ── 30 stations cosinus (EFFORT.PAS : O=π/(2·N)) ────────────────────
    N      = 30
    O_step = np.pi / (2 * N)
    rows   = []

    for i in range(1, N + 1):
        W  = O_step * i
        Y1 = B * np.cos(W)

        # Trapèze contenant Y1 : bisect sur X_sec croissant
        k_use = min(bisect.bisect_right(X_sec, Y1) - 1, trap - 1)
        k_use = max(k_use, 0)
        co    = coeffs[k_use]

        xba = co['a'] * Y1 + co['b']
        ybf = co['c'] * Y1 + co['d']

        # CZα : constante (CZAXE) à l'intérieur du fuselage
        cza = CZAXE if W > W0 else (co['e'] * Y1 + co['f'])

        rows.append({
            'Y [m]':     round(Y1,  5),
            'W [rd]':    round(W,   5),
            'Corde [m]': round(ybf - xba, 5),
            'YBA [m]':   round(xba, 5),
            'YBF [m]':   round(ybf, 5),
            'CZα':       round(cza, 5),
        })

    return pd.DataFrame(rows)


def plot_loi_corde(df: pd.DataFrame) -> plt.Figure:
    """Graphique Corde / YBA / YBF en fonction de l'envergure."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    y = df['Y [m]']

    ax1.plot(y, df['Corde [m]'], 'royalblue', lw=2, label='Corde')
    ax1.fill_between(y, 0, df['Corde [m]'], alpha=0.15, color='royalblue')
    ax1.set_ylabel('Corde [m]')
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Loi de corde et positions BA/BF — 30 stations cosinus', fontsize=11)

    ax2.plot(y, df['YBA [m]'], 'tomato',    lw=2, label='YBA (bord d\'attaque)')
    ax2.plot(y, df['YBF [m]'], 'seagreen',  lw=2, label='YBF (bord de fuite)')
    ax2.set_ylabel('Position en corde [m]')
    ax2.set_xlabel('Envergure Y [m]')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_cza(df: pd.DataFrame) -> plt.Figure:
    """Graphique CZα BIDIM en fonction de l'envergure."""
    fig, ax = plt.subplots(figsize=(10, 3.5))
    y = df['Y [m]']
    ax.plot(y, df['CZα'], 'darkorange', lw=2, marker='o', ms=3)
    ax.fill_between(y, 0, df['CZα'], alpha=0.15, color='darkorange')
    ax.set_xlabel('Envergure Y [m]')
    ax.set_ylabel('CZα BIDIM')
    ax.set_title('Loi CZα BIDIM — 30 stations cosinus (EFFORT.PAS)', fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_polaire(res: dict) -> plt.Figure:
    """Polaire Cx = f(Cz) + point finesse max + point taux de chute min."""
    fig, ax = plt.subplots(figsize=(6, 8))

    ax.plot(res["cx"], res["cz"], color="royalblue", linewidth=2, label="Polaire parabolique")

    # Droite tangente issue de l'origine → finesse max
    cz_tang = np.array([0, res["cz_fmax"] * 1.3])
    cx_tang = cz_tang / res["f_max"]
    ax.plot(cx_tang, cz_tang, "--", color="tomato", linewidth=1.2,
            label=f"Finesse max = {res['f_max']:.1f}")

    # Points caractéristiques
    ax.scatter([res["cx_fmax"]], [res["cz_fmax"]], color="tomato", zorder=5, s=60)
    ax.annotate(f"Fmax ({res['v_fmax']*3.6:.0f} km/h)",
                (res["cx_fmax"], res["cz_fmax"]),
                xytext=(res["cx_fmax"] + 0.003, res["cz_fmax"] - 0.08), fontsize=8)

    ax.scatter([res["cx_wmin"]], [res["cz_wmin"]], color="green", zorder=5, s=60)
    ax.annotate(f"wmin ({res['v_wmin']*3.6:.0f} km/h\n{res['w_min']:.2f} m/s)",
                (res["cx_wmin"], res["cz_wmin"]),
                xytext=(res["cx_wmin"] + 0.003, res["cz_wmin"] + 0.05), fontsize=8,
                color="green")

    ax.set_xlabel("Cx (traînée)", fontsize=11)
    ax.set_ylabel("Cz (portance)", fontsize=11)
    ax.set_title("Polaire parabolique — hypothèse elliptique", fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    return fig


def plot_finesse_vitesse(res: dict) -> plt.Figure:
    """Finesse et taux de chute en fonction de la vitesse."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7), sharex=True)
    v_kmh = res["vitesse"] * 3.6

    ax1.plot(v_kmh, res["finesse"], color="royalblue", linewidth=2)
    ax1.axvline(res["v_fmax"] * 3.6, color="tomato", linestyle="--", linewidth=1,
                label=f"Vf_max = {res['v_fmax']*3.6:.0f} km/h  (f={res['f_max']:.1f})")
    ax1.scatter([res["v_fmax"] * 3.6], [res["f_max"]], color="tomato", zorder=5)
    ax1.set_ylabel("Finesse f = Cz/Cx", fontsize=10)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("Finesse et taux de chute en fonction de la vitesse", fontsize=12)

    ax2.plot(v_kmh, res["taux_chute"], color="seagreen", linewidth=2)
    ax2.axvline(res["v_wmin"] * 3.6, color="green", linestyle="--", linewidth=1,
                label=f"Vw_min = {res['v_wmin']*3.6:.0f} km/h  (w={res['w_min']:.2f} m/s)")
    ax2.scatter([res["v_wmin"] * 3.6], [res["w_min"]], color="green", zorder=5)
    ax2.set_ylabel("Taux de chute w [m/s]", fontsize=10)
    ax2.set_xlabel("Vitesse [km/h]", fontsize=10)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.invert_yaxis()

    fig.tight_layout()
    return fig


def render():
    st.title("Module 3 — Portance elliptique")
    st.caption("Polaire parabolique · Prandtl lifting-line · e = 1 (validé sur H201B)")

    with st.sidebar:
        st.subheader("Paramètres")
        lbd    = st.number_input("Allongement λ", 10.0, 40.0, 23.0, step=0.5)
        cx0    = st.number_input("Cx0 (traînée parasite)", 0.005, 0.05, 0.0113,
                                  step=0.001, format="%.4f")
        masse  = st.number_input("Masse [kg]", 100.0, 600.0, 350.0, step=5.0)
        surface = st.number_input("Surface alaire [m²]", 5.0, 25.0, 9.80, step=0.1)
        h      = st.number_input("Altitude [m]", 0, 5000, 500, step=100)
        alpha0 = st.number_input("Incidence portance nulle α₀ [°]", -5.0, 0.0, 0.0,
                                  step=0.1)

    res = compute_polaire(lbd, cx0, masse, surface, h, alpha0)

    # ── Métriques clés ────────────────────────────────────────────────────
    st.subheader("Points caractéristiques")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Finesse max",      f"{res['f_max']:.1f}")
    c2.metric("Vitesse finesse max", f"{res['v_fmax']*3.6:.1f} km/h")
    c3.metric("Taux de chute min", f"{res['w_min']:.2f} m/s")
    c4.metric("Vitesse taux mini", f"{res['v_wmin']*3.6:.1f} km/h")

    c1, c2, c3 = st.columns(3)
    c1.metric("ki (coeff induit)", f"{res['ki']:.5f}")
    c2.metric("Cz à finesse max",  f"{res['cz_fmax']:.3f}")
    c3.metric("dCz/dα",           f"{res['dcz_dalpha']:.3f} rad⁻¹")

    st.divider()

    # ── Graphiques ────────────────────────────────────────────────────────
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Polaire Cx = f(Cz)")
        fig1 = plot_polaire(res)
        st.pyplot(fig1)
        plt.close(fig1)
    with col2:
        st.subheader("Finesse et taux de chute")
        fig2 = plot_finesse_vitesse(res)
        st.pyplot(fig2)
        plt.close(fig2)

    # ── Tableau Cz/Cx/f/V/α ──────────────────────────────────────────────
    with st.expander("Tableau polaire complet"):
        import pandas as pd
        step = 20
        idx  = np.arange(0, len(res["cz"]), step)
        df = pd.DataFrame({
            "α [°]":    np.round(res["alpha_deg"][idx], 2),
            "Cz":       np.round(res["cz"][idx], 4),
            "Cx":       np.round(res["cx"][idx], 5),
            "Finesse":  np.round(res["finesse"][idx], 1),
            "V [km/h]": np.round(res["vitesse"][idx] * 3.6, 1),
            "w [m/s]":  np.round(res["taux_chute"][idx], 3),
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Sortie vers DOMAINE ───────────────────────────────────────────────
    st.divider()
    st.subheader("Valeurs à utiliser dans DOMAINE")
    st.info(
        f"**Cx0** = {cx0:.4f} · **ki** = {res['ki']:.5f} · "
        f"**Cz finesse max** = {res['cz_fmax']:.3f} · "
        f"**Finesse max** = {res['f_max']:.1f} à {res['v_fmax']*3.6:.0f} km/h"
    )

    # ── Loi de corde / YBA / YBF / CZα BIDIM ────────────────────────────
    st.divider()
    st.subheader("Loi de corde, YBA, YBF et CZα BIDIM (EFFORT.PAS)")

    wing = st.session_state.get('geo_wing')
    if wing is None:
        st.info("Aucune géométrie d'aile chargée. "
                "Définissez la voilure dans **GEOAILE** pour accéder à cette section.")
    else:
        nom_aile = wing.get('nom', '?')
        st.caption(
            f"Géométrie : **{nom_aile}** · {wing['trap']} trapèze(s) · "
            f"demi-envergure {wing['A'][2*wing['trap']][0]/1000:.3f} m · "
            f"N = 30 stations cosinus"
        )

        df_lc = compute_loi_corde(wing)

        if df_lc.empty:
            st.warning("Données de géométrie insuffisantes (demi-envergure nulle ?).")
        else:
            # Graphiques
            col_a, col_b = st.columns([3, 2])
            with col_a:
                fig_lc = plot_loi_corde(df_lc)
                st.pyplot(fig_lc)
                plt.close(fig_lc)
            with col_b:
                fig_cza = plot_cza(df_lc)
                st.pyplot(fig_cza)
                plt.close(fig_cza)

            # Tableau
            with st.expander("Tableau — 30 stations (EFFORT.PAS ligne0)", expanded=False):
                st.dataframe(
                    df_lc.style.format({
                        'Y [m]':     '{:.5f}',
                        'W [rd]':    '{:.5f}',
                        'Corde [m]': '{:.5f}',
                        'YBA [m]':   '{:.5f}',
                        'YBF [m]':   '{:.5f}',
                        'CZα':       '{:.5f}',
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

            if all(v == 0.0 for v in wing['CZA']):
                st.warning(
                    "Les valeurs CZα sont toutes nulles dans le fichier .AIL — "
                    "renseignez les coefficients CZA-1 à CZA_n dans GEOAILE."
                )
