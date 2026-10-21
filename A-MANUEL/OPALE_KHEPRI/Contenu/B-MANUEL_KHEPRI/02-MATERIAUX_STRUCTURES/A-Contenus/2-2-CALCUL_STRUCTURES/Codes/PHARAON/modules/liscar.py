"""
Module LISCAR — Lissage de profil aérodynamique par polynômes
Algorithme fidèle au LISCAR original (ENSAE 1990, Turbo-Pascal / Fortran)
Base polynomiale : (x^k − √x)  k=1..ncoef  — garantit y=0 en BA et BF
Nœuds cosinus : j=2..60 (59 points intérieurs)
Profil par défaut : Wortmann FX 66-17AII-182 (H201B Libelle)
Source données    : NASA TN D-8324 (Somers, 1977) — converti au format LISCAR
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import io
import os

# ─────────────────────────────────────────────────────────────────────────────
# Chargement du profil FX 66-17AII-182 depuis FX66_H182.LIS
# Source : NASA TN D-8324 (Somers, 1977) — converti depuis format Selig au format LISCAR
# Format : x_ext% y_ext% x_int% y_int%  — 59 points cosinus de BF vers BA
# ─────────────────────────────────────────────────────────────────────────────

def _load_fx66() -> tuple:
    """
    Charge les données réelles FX 66-17AII-182 depuis data/FX66_H182.LIS.
    Retourne (x, y_ext, y_int) en fraction de corde [0..1], triés BA→BF.
    """
    lis_path = os.path.join(os.path.dirname(__file__), "..", "data", "FX66_H182.LIS")
    rows = []
    with open(lis_path, "r") as f:
        for line in f:
            vals = line.split()
            if len(vals) == 4:
                try:
                    rows.append([float(v) for v in vals])
                except ValueError:
                    continue
    arr = np.array(rows) / 100.0   # % → fraction de corde

    # Le fichier va de BF (x≈0.9993) vers BA (x≈0.0007) — on inverse
    arr = arr[::-1]

    # Ajouter BA (0,0) et BF (1,0)
    row0 = np.array([[0.0, 0.0, 0.0, 0.0]])
    row1 = np.array([[1.0, 0.0, 1.0, 0.0]])
    arr = np.vstack([row0, arr, row1])

    x     = arr[:, 0]
    y_ext = arr[:, 1]
    y_int = arr[:, 3]
    return x, y_ext, y_int


# Chargement au démarrage du module
try:
    _FX66_X, _FX66_Y_EXT, _FX66_Y_INT = _load_fx66()
    FX66_EXTRADOS = np.column_stack([_FX66_X, _FX66_Y_EXT])
    FX66_INTRADOS = np.column_stack([_FX66_X, _FX66_Y_INT])
    _FX66_OK = True
except Exception as _e:
    _FX66_OK = False
    _FX66_ERR = str(_e)
    # Fallback minimal pour ne pas planter l'import
    FX66_EXTRADOS = np.array([[0.0, 0.0], [0.5, 0.086], [1.0, 0.0]])
    FX66_INTRADOS = np.array([[0.0, 0.0], [0.5, -0.021], [1.0, 0.0]])


# ─────────────────────────────────────────────────────────────────────────────
# Algorithme LISCAR — base polynomiale (x^k − √x)
# ─────────────────────────────────────────────────────────────────────────────

def cosine_nodes(n: int = 59) -> np.ndarray:
    """
    59 nœuds cosinus intérieurs j=2..60 (fidèle à l'original Pascal/Fortran).
    tet = (j-1)*π/60,  x = 0.5*(1+cos(tet))
    Triés de BA (x≈0) vers BF (x≈1).
    """
    j = np.arange(2, n + 2)          # j = 2 .. 60
    tet = (j - 1) * np.pi / 60.0
    x = 0.5 * (1.0 + np.cos(tet))
    return x[::-1]                    # ordre BA → BF


def _basis_matrix(x: np.ndarray, ncoef: int) -> np.ndarray:
    """
    Matrice de la base LISCAR : colonnes = (x^k − √x)  pour k=1..ncoef.
    Garantit y=0 en x=0 et x=1 (BA et BF fermés automatiquement).
    """
    sqrt_x = np.sqrt(np.maximum(x, 0.0))
    A = np.zeros((len(x), ncoef))
    for k in range(1, ncoef + 1):
        A[:, k - 1] = x**k - sqrt_x
    return A


def poly_fit_liscar(x: np.ndarray, y: np.ndarray, ncoef: int) -> np.ndarray:
    """Moindres carrés dans la base LISCAR — retourne les coefficients C[k]."""
    A = _basis_matrix(x, ncoef)
    C, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    return C


def poly_eval_liscar(x: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Évalue Σ C[k]*(x^(k+1) − √x)  sur le vecteur x."""
    sqrt_x = np.sqrt(np.maximum(x, 0.0))
    result = np.zeros_like(x, dtype=float)
    for k in range(1, len(C) + 1):
        result += C[k - 1] * (x**k - sqrt_x)
    return result


def liscar(x_ext: np.ndarray, y_ext: np.ndarray,
           x_int: np.ndarray, y_int: np.ndarray,
           ncoef: int = 6, n_pts: int = 59):
    """
    Lisse le profil et rééchantillonne sur n_pts nœuds cosinus.

    Base polynomiale : (x^k − √x) — algorithme LISCAR original ENSAE 1990.

    Retourne un dict avec :
      - x_lis, y_ext_lis, y_int_lis : profil lissé (n_pts points BA→BF)
      - coeffs_ext, coeffs_int       : vecteurs C de la base LISCAR
      - ep_max, pos_ep_max           : épaisseur relative max et sa position
      - rms_ext, rms_int             : écarts quadratiques moyens
    """
    xi = cosine_nodes(n_pts)          # nœuds intérieurs BA→BF

    # Exclure les points exactement en 0 ou 1 pour √x bien défini
    mask_e = (x_ext > 0) & (x_ext < 1)
    mask_i = (x_int > 0) & (x_int < 1)

    C_ext = poly_fit_liscar(x_ext[mask_e], y_ext[mask_e], ncoef)
    C_int = poly_fit_liscar(x_int[mask_i], y_int[mask_i], ncoef)

    y_ext_lis = poly_eval_liscar(xi, C_ext)
    y_int_lis = poly_eval_liscar(xi, C_int)

    # Forcer les bords à zéro (la base le garantit déjà, mais sécurité numérique)
    y_ext_lis[0]  = 0.0;  y_ext_lis[-1]  = 0.0
    y_int_lis[0]  = 0.0;  y_int_lis[-1]  = 0.0

    ep = y_ext_lis - y_int_lis
    ep_max     = ep.max()
    pos_ep_max = xi[ep.argmax()]

    # RMS sur les points originaux
    rms_ext = np.sqrt(np.mean(
        (poly_eval_liscar(x_ext[mask_e], C_ext) - y_ext[mask_e])**2))
    rms_int = np.sqrt(np.mean(
        (poly_eval_liscar(x_int[mask_i], C_int) - y_int[mask_i])**2))

    return {
        "x_lis": xi,
        "y_ext_lis": y_ext_lis, "y_int_lis": y_int_lis,
        "coeffs_ext": C_ext, "coeffs_int": C_int,
        "ep_max": ep_max, "pos_ep_max": pos_ep_max,
        "rms_ext": rms_ext, "rms_int": rms_int,
        "n_pts": n_pts, "ncoef": ncoef,
    }


def parse_ini(text: str):
    """
    Parse un fichier .INI au format LISCAR original :
    4 colonnes par ligne : x_ext  y_ext  x_int  y_int  (en % de corde).
    Retourne (x_ext, y_ext, x_int, y_int) en fraction [0..1].
    """
    pts = []
    for line in text.splitlines():
        vals = line.split()
        if len(vals) >= 4:
            try:
                pts.append([float(v) for v in vals[:4]])
            except ValueError:
                continue
    if not pts:
        return None
    arr = np.array(pts) / 100.0
    x_ext, y_ext = arr[:, 0], arr[:, 1]
    x_int, y_int = arr[:, 2], arr[:, 3]
    idx = np.argsort(x_ext); x_ext, y_ext = x_ext[idx], y_ext[idx]
    idx = np.argsort(x_int); x_int, y_int = x_int[idx], y_int[idx]
    return x_ext, y_ext, x_int, y_int


def parse_dat(text: str):
    """
    Parse un fichier .DAT au format Selig ou deux colonnes x y.
    Sépare automatiquement extrados et intrados.
    Retourne (x_ext, y_ext, x_int, y_int) en fraction [0..1].
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    pts = []
    for line in lines:
        parts = line.split()
        try:
            x, y = float(parts[0]), float(parts[1])
            pts.append((x, y))
        except (ValueError, IndexError):
            continue
    if not pts:
        return None

    pts = np.array(pts)
    x, y = pts[:, 0], pts[:, 1]

    if x.max() > 1.5:
        x /= 100.0; y /= 100.0

    idx_min = np.argmin(x)
    if 0 < idx_min < len(x) - 1:
        x_ext, y_ext = x[:idx_min+1][::-1], y[:idx_min+1][::-1]
        x_int, y_int = x[idx_min:],         y[idx_min:]
    else:
        mask = y >= 0
        x_ext, y_ext = x[mask],  y[mask]
        x_int, y_int = x[~mask], y[~mask]

    idx = np.argsort(x_ext); x_ext, y_ext = x_ext[idx], y_ext[idx]
    idx = np.argsort(x_int); x_int, y_int = x_int[idx], y_int[idx]
    return x_ext, y_ext, x_int, y_int


def export_lis(res: dict, nom: str = "PROFIL") -> str:
    """Génère le fichier .LIS au format du LISCAR original (4 colonnes en %)."""
    lines = [f" PROFIL LISSE : {nom}",
             f" NCOEF : {res['ncoef']}",
             f" N POINTS : {res['n_pts']}", " ",
             f"{'J':>4} {'X_EXT':>10} {'Y_EXT':>12} {'X_INT':>10} {'Y_INT':>12} {'EP':>10}"]
    ep = res["y_ext_lis"] - res["y_int_lis"]
    for j, (x, ye, yi, e) in enumerate(
            zip(res["x_lis"], res["y_ext_lis"], res["y_int_lis"], ep), start=1):
        lines.append(
            f"{j:4d} {x*100:10.4f} {ye*100:12.6f} {x*100:10.4f} {yi*100:12.6f} {e*100:10.4f}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Graphiques
# ─────────────────────────────────────────────────────────────────────────────

def plot_profil(x_raw_ext, y_raw_ext, x_raw_int, y_raw_int, res: dict,
                titre: str = "") -> plt.Figure:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))

    ax1.plot(x_raw_ext, y_raw_ext, "o", ms=4, color="steelblue",
             alpha=0.6, label="Points bruts extrados")
    ax1.plot(x_raw_int, y_raw_int, "s", ms=4, color="tomato",
             alpha=0.6, label="Points bruts intrados")
    ax1.plot(res["x_lis"], res["y_ext_lis"], "-", lw=2, color="royalblue",
             label=f"Lissé extrados (ncoef={res['ncoef']})")
    ax1.plot(res["x_lis"], res["y_int_lis"], "-", lw=2, color="firebrick",
             label="Lissé intrados")

    i_ep = res["y_ext_lis"] - res["y_int_lis"]
    i_max = np.argmax(i_ep)
    ax1.annotate("", xy=(res["pos_ep_max"], res["y_int_lis"][i_max]),
                xytext=(res["pos_ep_max"], res["y_ext_lis"][i_max]),
                arrowprops=dict(arrowstyle="<->", color="green", lw=1.5))
    ax1.text(res["pos_ep_max"] + 0.01, 0, f"ep={res['ep_max']*100:.2f}%",
             color="green", fontsize=8)

    ax1.set_aspect("equal")
    ax1.set_title(f"Profil {titre} — lissage LISCAR (base x^k−√x)", fontsize=12)
    ax1.legend(fontsize=8, loc="upper right")
    ax1.grid(True, alpha=0.3)
    ax1.set_xlabel("x/c"); ax1.set_ylabel("y/c")

    # Résidus
    mask_e = (x_raw_ext > 0) & (x_raw_ext < 1)
    mask_i = (x_raw_int > 0) & (x_raw_int < 1)
    res_ext = poly_eval_liscar(x_raw_ext[mask_e], res["coeffs_ext"]) - y_raw_ext[mask_e]
    res_int = poly_eval_liscar(x_raw_int[mask_i], res["coeffs_int"]) - y_raw_int[mask_i]
    ax2.plot(x_raw_ext[mask_e], res_ext * 100, "o-", ms=3, color="royalblue",
             label=f"Résidu extrados (RMS={res['rms_ext']*100:.4f}%)")
    ax2.plot(x_raw_int[mask_i], res_int * 100, "s-", ms=3, color="firebrick",
             label=f"Résidu intrados (RMS={res['rms_int']*100:.4f}%)")
    ax2.axhline(0, color="black", lw=0.8)
    ax2.set_xlabel("x/c"); ax2.set_ylabel("Résidu [% corde]")
    ax2.set_title("Résidus du lissage polynomial")
    ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Interface Streamlit
# ─────────────────────────────────────────────────────────────────────────────

def render():
    import pandas as pd

    st.title("Module 2 — Lissage de profil (LISCAR)")
    st.caption("Base polynomiale (xᵏ−√x) · Distribution cosinus · Export .LIS")

    if not _FX66_OK:
        st.error(f"Impossible de charger FX66_H182.LIS : {_FX66_ERR}")

    with st.sidebar:
        st.subheader("Profil source")
        source = st.radio("Source", [
            "H201B — Wortmann FX 66-17AII-182 (NASA TN D-8324)",
            "Fichier .INI (format LISCAR 4 colonnes)",
            "Fichier .DAT (format Selig / 2 colonnes)",
            "Définir manuellement",
        ])

        st.divider()
        st.subheader("Paramètres LISCAR")
        ncoef = st.slider("Nombre de coefficients (ncoef)", 3, 10, 6)
        n_pts = st.slider("Nombre de points lissés", 30, 100, 59)

    # ── Chargement du profil ──────────────────────────────────────────────
    if source.startswith("H201B"):
        x_ext, y_ext = FX66_EXTRADOS[:, 0], FX66_EXTRADOS[:, 1]
        x_int, y_int = FX66_INTRADOS[:, 0], FX66_INTRADOS[:, 1]
        nom_profil = "FX 66-17AII-182"
        st.info("Données : NASA TN D-8324 (Somers, 1977) — FX 66-17AII-182 testé en soufflerie")

    elif source.startswith("Fichier .INI"):
        uploaded = st.file_uploader("Fichier .INI / .LIS (format LISCAR : 4 col. x_ext y_ext x_int y_int en %)",
                                    type=["ini", "lis", "txt"])
        if uploaded is None:
            st.info("Chargez un fichier .INI au format LISCAR original.")
            return
        text = uploaded.read().decode("utf-8", errors="ignore")
        parsed = parse_ini(text)
        if parsed is None:
            st.error("Format non reconnu — attendu : 4 colonnes par ligne.")
            return
        x_ext, y_ext, x_int, y_int = parsed
        nom_profil = uploaded.name

    elif source.startswith("Fichier .DAT"):
        uploaded = st.file_uploader("Fichier .DAT (format Selig ou 2 colonnes x y)",
                                    type=["dat", "txt"])
        if uploaded is None:
            st.info("Chargez un fichier .DAT ou sélectionnez le profil H201B.")
            return
        text = uploaded.read().decode("utf-8", errors="ignore")
        parsed = parse_dat(text)
        if parsed is None:
            st.error("Format non reconnu.")
            return
        x_ext, y_ext, x_int, y_int = parsed
        nom_profil = uploaded.name

    else:  # Définir manuellement
        st.markdown(
            "Saisissez les coordonnées de votre profil en **fraction de corde** "
            "(x/c entre 0 et 1, y/c positif pour l'extrados, négatif pour l'intrados). "
            "Le bord d'attaque est en x=0, le bord de fuite en x=1.")
        st.caption(
            "Astuce : vous pouvez aussi coller des données depuis Excel "
            "(colonnes séparées par des tabulations).")

        with st.sidebar:
            nom_profil = st.text_input("Nom du profil", "MON_PROFIL").upper()

        # Points par défaut : NACA 4412 simplifié (quelques stations)
        default_ext = [
            [0.000, 0.000], [0.025, 0.059], [0.050, 0.079], [0.100, 0.103],
            [0.200, 0.124], [0.300, 0.130], [0.400, 0.124], [0.500, 0.110],
            [0.600, 0.090], [0.700, 0.068], [0.800, 0.045], [0.900, 0.022],
            [1.000, 0.000],
        ]
        default_int = [
            [0.000, 0.000], [0.025, -0.026], [0.050, -0.033], [0.100, -0.038],
            [0.200, -0.038], [0.300, -0.031], [0.400, -0.022], [0.500, -0.013],
            [0.600, -0.006], [0.700,  0.000], [0.800,  0.005], [0.900,  0.007],
            [1.000,  0.000],
        ]

        col_e, col_i = st.columns(2)
        with col_e:
            st.markdown("**Extrados**")
            df_ext = pd.DataFrame(default_ext, columns=["x/c", "y/c"])
            edited_ext = st.data_editor(
                df_ext,
                column_config={
                    "x/c": st.column_config.NumberColumn(format="%.4f", step=0.001,
                                                         min_value=0.0, max_value=1.0),
                    "y/c": st.column_config.NumberColumn(format="%.4f", step=0.001),
                },
                num_rows="dynamic", hide_index=True,
                use_container_width=True, key="liscar_ext",
            )
        with col_i:
            st.markdown("**Intrados**")
            df_int = pd.DataFrame(default_int, columns=["x/c", "y/c"])
            edited_int = st.data_editor(
                df_int,
                column_config={
                    "x/c": st.column_config.NumberColumn(format="%.4f", step=0.001,
                                                         min_value=0.0, max_value=1.0),
                    "y/c": st.column_config.NumberColumn(format="%.4f", step=0.001),
                },
                num_rows="dynamic", hide_index=True,
                use_container_width=True, key="liscar_int",
            )

        arr_e = edited_ext.dropna().values.astype(float)
        arr_i = edited_int.dropna().values.astype(float)
        if len(arr_e) < 3 or len(arr_i) < 3:
            st.warning("Saisissez au moins 3 points par surface.")
            return
        idx = np.argsort(arr_e[:, 0]); x_ext, y_ext = arr_e[idx, 0], arr_e[idx, 1]
        idx = np.argsort(arr_i[:, 0]); x_int, y_int = arr_i[idx, 0], arr_i[idx, 1]

        st.info(
            "Les valeurs par défaut sont celles du profil **NACA 4412** (à titre d'exemple). "
            "Remplacez-les par les coordonnées de votre profil.")

    # ── Calcul ───────────────────────────────────────────────────────────
    try:
        res = liscar(x_ext, y_ext, x_int, y_int, ncoef=ncoef, n_pts=n_pts)
    except np.linalg.LinAlgError:
        st.error("Impossible d'ajuster le polynôme — réduisez ncoef.")
        return

    # ── Métriques ─────────────────────────────────────────────────────────
    st.subheader("Résultats du lissage")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Épaisseur max", f"{res['ep_max']*100:.2f} %")
    c2.metric("Position ép. max", f"{res['pos_ep_max']*100:.1f} % corde")
    c3.metric("RMS extrados", f"{res['rms_ext']*100:.5f} %")
    c4.metric("RMS intrados", f"{res['rms_int']*100:.5f} %")

    st.divider()
    fig = plot_profil(x_ext, y_ext, x_int, y_int, res, titre=nom_profil)
    st.pyplot(fig)
    plt.close(fig)

    # ── Export .LIS ───────────────────────────────────────────────────────
    st.divider()
    lis_content = export_lis(res, nom=nom_profil)
    st.download_button(
        label="Télécharger le fichier .LIS",
        data=lis_content,
        file_name=f"{nom_profil.replace(' ', '_')}.LIS",
        mime="text/plain",
    )

    with st.expander("Aperçu fichier .LIS"):
        st.code(lis_content[:2000] + ("\n..." if len(lis_content) > 2000 else ""))

    with st.expander("Tableau des points lissés"):
        ep = res["y_ext_lis"] - res["y_int_lis"]
        df = pd.DataFrame({
            "j":          np.arange(1, n_pts + 1),
            "x/c":        np.round(res["x_lis"], 6),
            "y_ext/c":    np.round(res["y_ext_lis"], 6),
            "y_int/c":    np.round(res["y_int_lis"], 6),
            "ép. [%c]":   np.round(ep * 100, 4),
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Section : profil réel f(position spanwise) ────────────────────────────
    st.divider()
    st.subheader("Profil réel en fonction de la position spanwise")
    st.caption(
        "Visualise la section transversale réelle de l'aile (en mètres) "
        "à une position donnée le long de l'envergure. "
        "Nécessite que le module GEOAILE ait été exécuté au préalable."
    )

    wing = st.session_state.get('geo_wing')

    if wing is None:
        st.info("Lance d'abord le module GEOAILE pour charger la géométrie de l'aile.")
    else:
        # Récupération de la géométrie depuis GEOAILE
        A    = wing['A']       # liste de points en mm : [[x_span, y_corde], ...]
        trap = wing['trap']    # nombre de trapèzes

        # Construction des tableaux de stations spanwise et de cordes
        # A contient les points dans l'ordre :
        #   A[0], A[1]  : station 0 (emplanture ou axe)
        #   A[2], A[3]  : station 1 (fin du trapèze 1)
        #   A[4], A[5]  : station 2 (fin du trapèze 2 = saumon)
        # Pour chaque station k : A[2k] = bord d'attaque, A[2k+1] = bord de fuite
        # Les coordonnées sont en mm.

        stations_x = []   # positions spanwise en mètres
        cordes     = []   # cordes locales en mètres
        y_ba_list  = []   # ordonnée bord d'attaque en mètres

        for k in range(trap + 1):
            x_span_mm = A[2 * k][0]
            y_ba_mm   = A[2 * k][1]
            y_bf_mm   = A[2 * k + 1][1]
            corde_m   = (y_bf_mm - y_ba_mm) / 1000.0
            stations_x.append(x_span_mm / 1000.0)
            cordes.append(corde_m)
            y_ba_list.append(y_ba_mm / 1000.0)

        b_half = stations_x[-1]   # demi-envergure en mètres

        # Slider : l'utilisateur choisit la position spanwise
        x_span_choisi = st.slider(
            "Position spanwise x [m]  (0 = emplanture, {:.2f} = saumon)".format(b_half),
            min_value=0.0,
            max_value=float(b_half),
            value=0.0,
            step=0.05,
            key="liscar_span_slider"
        )

        # Interpolation linéaire de la corde et du bord d'attaque à x_span_choisi
        corde_locale = float(np.interp(x_span_choisi, stations_x, cordes))
        y_ba_local   = float(np.interp(x_span_choisi, stations_x, y_ba_list))

        # Profil normalisé issu de LISCAR (x/c, y/c)
        x_norm     = res['x_lis']          # tableau numpy, valeurs entre 0 et 1
        y_ext_norm = res['y_ext_lis']      # extrados normalisé
        y_int_norm = res['y_int_lis']      # intrados normalisé

        # Mise à l'échelle physique : multiplication par la corde locale
        # + translation pour placer le bord d'attaque à sa position correcte
        x_ext_phys = y_ba_local + x_norm * corde_locale    # en mètres (direction chordwise)
        y_ext_phys = y_ext_norm * corde_locale              # en mètres (épaisseur)
        x_int_phys = y_ba_local + x_norm * corde_locale
        y_int_phys = y_int_norm * corde_locale

        # Affichage des métriques
        col1, col2, col3 = st.columns(3)
        col1.metric("Position spanwise", f"{x_span_choisi:.2f} m")
        col2.metric("Corde locale", f"{corde_locale*100:.1f} cm")
        col3.metric("Épaisseur max", f"{(y_ext_phys - y_int_phys).max()*100:.1f} cm")

        # Figure
        fig_span, ax_span = plt.subplots(figsize=(10, 3))
        ax_span.plot(x_ext_phys, y_ext_phys, color="royalblue", lw=2, label="Extrados")
        ax_span.plot(x_int_phys, y_int_phys, color="tomato",    lw=2, label="Intrados")
        ax_span.fill_between(x_ext_phys, y_ext_phys, y_int_phys, alpha=0.12, color="royalblue")
        ax_span.set_xlabel("Position chordwise [m]")
        ax_span.set_ylabel("Épaisseur [m]")
        ax_span.set_title(
            f"Section du profil {nom_profil} à x = {x_span_choisi:.2f} m "
            f"(corde = {corde_locale*100:.1f} cm)"
        )
        ax_span.legend(fontsize=9)
        ax_span.set_aspect('equal')
        ax_span.grid(True, alpha=0.3)
        st.pyplot(fig_span)
        plt.close(fig_span)

        # Tableau compact
        with st.expander("Coordonnées physiques à cette station"):
            df_phys = pd.DataFrame({
                "x chordwise [m]" : np.round(x_ext_phys, 5),
                "y extrados [m]"  : np.round(y_ext_phys, 5),
                "y intrados [m]"  : np.round(y_int_phys, 5),
                "épaisseur [m]"   : np.round(y_ext_phys - y_int_phys, 5),
            })
            st.dataframe(df_phys, use_container_width=True, hide_index=True)

    with st.expander("Note algorithmique"):
        st.markdown("""
**Base polynomiale LISCAR (Wortmann, ENSAE 1990)**

Le polynôme ajusté est de la forme :

$$y(x) = \\sum_{k=1}^{n_{coef}} C_k \\left( x^k - \\sqrt{x} \\right)$$

Cette base garantit automatiquement **y(0) = 0** (bord d'attaque) et **y(1) = 0** (bord de fuite),
et capture la singularité en √x caractéristique du bord d'attaque (théorie des profils minces).

Les nœuds cosinus intérieurs sont $x_j = \\frac{1}{2}\\left(1 + \\cos\\frac{(j-1)\\pi}{60}\\right)$
pour $j = 2 \\ldots 60$ (59 points).
        """)
