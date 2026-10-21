"""
Module GEOAILE — Géométrie de voilure
Fidèle à l'outil original GEOAILE (ENSAE 1990, Turbo-Pascal / Prodhomme)
Format natif : fichier .AIL (coordonnées absolues en mm)
Calcule : Sref, Sext, SMC, MAC, AR, effilement, angles de flèche φBA/C4/C2/BF
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

# ─── Données H201B par défaut ─────────────────────────────────────────────────
# A[i] = [X_envergure_mm, Y_corde_mm]  
# Alternance : indices pairs = BA (bord d'attaque), impairs = BF (bord de fuite)
H201B = {
    'nom': 'H201B',
    'trap': 2,
    # Flèche respectant le recul du BA pour garder la ligne 25% droite
    'A': [[0, 0], [0, 900], [4400, 68], [4400, 698], [7500, 135], [7500, 495]],
    'B': [[2353, 400], [3783, 400]],   # aérofrein [X_enverg_mm, Y_corde_mm]
    'C': 425.0,                        # Largeur totale du FUSELAGE [mm] — dossier Glasflügel p.30
    'D': [[0, 0], [0, 0], [4400, 150], [7500, 90]],  # ailerons (D[j]=[X_mm, prof_Y_mm])
    'CZA': [6.05, 6.05, 6.05, 6.05],  # NASA TN D-8324 — profil constant FX-66-17AII-182, Re≈1.5e6, M≈0.10–0.15
}

# ─── Parseur .AIL ─────────────────────────────────────────────────────────────
def parse_ail(text: str, nom: str = 'AILE') -> dict | None:
    kv = {}
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            key = parts[0].rstrip(':').upper()
            try:
                val = float(parts[-1])
                if (key != 'TRAP' and not key.startswith('CZA')
                        and abs(val) < 10 and val != 0):
                    val *= 1000.0
                kv[key] = val
            except ValueError:
                pass

    if 'TRAP' not in kv:
        return None
    trap = int(kv['TRAP'])

    A = []
    for i in range(1, 2*(trap+1)+1):
        A.append([kv.get(f'A{i}1', 0.0), kv.get(f'A{i}2', 0.0)])

    B = [
        [kv.get('B11', kv.get('BB11', 0.0)), kv.get('B12', kv.get('BB12', 0.0))],
        [kv.get('B21', kv.get('BB21', 0.0)), kv.get('B22', kv.get('BB22', 0.0))],
    ]
    C = kv.get('C', kv.get('CC', 0.0))

    D = []
    for i in range(1, 2*trap+1):
        j = i // 2 + i % 2
        s = 2 - i % 2
        D.append([
            kv.get(f'AF{j}{s}1', kv.get(f'F{j}{s}1', 0.0)),
            kv.get(f'AF{j}{s}2', kv.get(f'F{j}{s}2', 0.0)),
        ])

    CZA = [kv.get(f'CZA{i}', 0.0) for i in range(-1, trap+1)]

    return {
        'nom': nom.upper().replace('.AIL', '').replace('.ail', ''),
        'trap': trap, 'A': A, 'B': B, 'C': C, 'D': D, 'CZA': CZA,
    }

def segments_to_wing(segments: list, nom: str = 'AILE',
                     C_fus: float = 425.0) -> dict:
    A = []
    y_ba = 0.0
    x = 0.0
    A.append([0.0, 0.0])
    A.append([0.0, segments[0]['c_root'] * 1000.0])
    for seg in segments:
        db = seg['demi_b'] * 1000.0
        ct = seg['c_tip'] * 1000.0
        y_ba += db * np.tan(np.radians(seg['fleche']))
        x += db
        A.append([x, y_ba])
        A.append([x, y_ba + ct])
    trap = len(segments)
    span = x
    B = [[0.30 * span, 400.0], [0.50 * span, 400.0]]
    D = [[0.0, 0.0], [0.0, 0.0]] * trap
    CZA = [0.0] * (trap + 3)
    return {'nom': nom.upper(), 'trap': trap, 'A': A, 'B': B, 'C': C_fus,
            'D': D, 'CZA': CZA}

# ─── Extraction paramètres de trapèzes depuis les points A ───────────────────
def _wing_to_segs(wing: dict) -> list:
    """Inverse de segments_to_wing : extrait c_root/c_tip/demi_b/fleche depuis A."""
    A = wing['A']
    trap = wing['trap']
    segs = []
    for i in range(trap):
        x0  = A[2 * i][0];      y_ba0 = A[2 * i][1]
        x1  = A[2*(i+1)][0];    y_ba1 = A[2*(i+1)][1]
        y_bf0 = A[2*i + 1][1]
        y_bf1 = A[2*(i+1) + 1][1]
        demi_b = (x1 - x0) / 1000.0
        c_root = (y_bf0 - y_ba0) / 1000.0
        c_tip  = (y_bf1 - y_ba1) / 1000.0
        fleche = float(np.degrees(np.arctan2(y_ba1 - y_ba0, x1 - x0))) if (x1 - x0) > 0 else 0.0
        segs.append({'c_root': c_root, 'c_tip': c_tip,
                     'demi_b': demi_b, 'fleche': fleche})
    return segs


# ─── Export .AIL ─────────────────────────────────────────────────────────────
def wing_to_ail(wing: dict) -> str:
    """Génère le texte d'un fichier .AIL (format original GEOAILE) à partir d'un dict wing.
    Valeurs écrites en mètres — le parseur les ramènera en mm via ×1000 (valeurs < 10)."""
    trap = wing['trap']
    lines = [
        f"NOM:  {wing['nom']}",
        f"TRAP: {trap}",
        "",
    ]
    for k in range(2 * (trap + 1)):
        lines.append(f"A{k+1}1: {wing['A'][k][0] / 1000:.6f}")
        lines.append(f"A{k+1}2: {wing['A'][k][1] / 1000:.6f}")
    lines.append("")
    lines.append(f"B11: {wing['B'][0][0] / 1000:.6f}")
    lines.append(f"B12: {wing['B'][0][1] / 1000:.6f}")
    lines.append(f"B21: {wing['B'][1][0] / 1000:.6f}")
    lines.append(f"B22: {wing['B'][1][1] / 1000:.6f}")
    lines.append("")
    lines.append(f"C:   {wing['C'] / 1000:.6f}")
    lines.append("")
    for i in range(1, 2 * trap + 1):
        j = i // 2 + i % 2
        s = 2 - i % 2
        k = i - 1
        lines.append(f"AF{j}{s}1: {wing['D'][k][0] / 1000:.6f}")
        lines.append(f"AF{j}{s}2: {wing['D'][k][1] / 1000:.6f}")
    lines.append("")
    for idx, i in enumerate(range(-1, trap + 1)):
        raw = wing['CZA'][idx]
        lines.append(f"CZA{i}: {raw:.6f}")
    return '\n'.join(lines)


def _tables_edit_wing(wing: dict, key_prefix: str) -> tuple:
    """
    Affiche des tableaux data_editor pour tous les points géométriques (A, B, C, D).
    Retourne (wing_construit_depuis_tables, bouton_valider_pressé).
    Les calculs (flèche, MAC, etc.) ne se mettent à jour qu'après "Valider".
    """
    import copy
    w = copy.deepcopy(wing)
    trap = w['trap']
    n_A = 2 * (trap + 1)
    ver = st.session_state.get('geo_edit_ver', 0)

    # ── Points A ──────────────────────────────────────────────────────────
    st.markdown("**Points A — Plan de forme**")
    st.caption("BA = bord d'attaque · BF = bord de fuite · coordonnées absolues en mm")
    df_A = pd.DataFrame({
        'Point': [f'A{k+1}' for k in range(n_A)],
        'Rôle':  ['BA (bord d\'attaque)' if k % 2 == 0 else 'BF (bord de fuite)'
                  for k in range(n_A)],
        'X Envergure [mm]': [float(round(w['A'][k][0])) for k in range(n_A)],
        'Y Corde [mm]':     [float(round(w['A'][k][1])) for k in range(n_A)],
    })
    edited_A = st.data_editor(
        df_A,
        column_config={
            'Point': st.column_config.TextColumn(disabled=True, width='small'),
            'Rôle':  st.column_config.TextColumn(disabled=True, width='medium'),
            'X Envergure [mm]': st.column_config.NumberColumn(format="%g", step=1.0, min_value=0.0),
            'Y Corde [mm]':     st.column_config.NumberColumn(format="%g", step=1.0, min_value=0.0),
        },
        hide_index=True, use_container_width=True,
        key=f'{key_prefix}_A_v{ver}',
    )

    # ── Points B (Aérofrein) ──────────────────────────────────────────────
    st.markdown("**Points B — Aérofrein**")
    st.caption("B1 = limite intérieure · B2 = limite extérieure en envergure · Y = position en corde")
    df_B = pd.DataFrame({
        'Point': ['B1 (intérieur)', 'B2 (extérieur)'],
        'X Envergure [mm]': [float(round(w['B'][i][0])) for i in range(2)],
        'Y Corde [mm]':     [float(round(w['B'][i][1])) for i in range(2)],
    })
    edited_B = st.data_editor(
        df_B,
        column_config={
            'Point': st.column_config.TextColumn(disabled=True, width='medium'),
            'X Envergure [mm]': st.column_config.NumberColumn(format="%g", step=1.0, min_value=0.0),
            'Y Corde [mm]':     st.column_config.NumberColumn(format="%g", step=1.0, min_value=0.0),
        },
        hide_index=True, use_container_width=True,
        key=f'{key_prefix}_B_v{ver}',
    )

    # ── Fuselage C ────────────────────────────────────────────────────────
    st.markdown("**Fuselage C**")
    C_new = st.number_input(
        'Largeur totale fuselage C [mm]', 0.0, 2000.0, float(w['C']), 10.0,
        key=f'{key_prefix}_C_v{ver}',
    )

    # ── Points D (Ailerons) ───────────────────────────────────────────────
    edited_D = None
    if len(w['D']) > 0:
        st.markdown("**Points D — Ailerons**")
        st.caption("X = position en envergure · Profondeur = extension en corde depuis le bord de fuite")
        labels = []
        for ti in range(1, trap + 1):
            labels += [f'D tr.{ti} intérieur', f'D tr.{ti} extérieur']
        df_D = pd.DataFrame({
            'Point':            labels[:len(w['D'])],
            'X Envergure [mm]': [float(round(w['D'][k][0])) for k in range(len(w['D']))],
            'Profondeur [mm]':  [float(round(w['D'][k][1])) for k in range(len(w['D']))],
        })
        edited_D = st.data_editor(
            df_D,
            column_config={
                'Point':            st.column_config.TextColumn(disabled=True),
                'X Envergure [mm]': st.column_config.NumberColumn(format="%g", step=1.0, min_value=0.0),
                'Profondeur [mm]':  st.column_config.NumberColumn(format="%g", step=1.0, min_value=0.0),
            },
            hide_index=True, use_container_width=True,
            key=f'{key_prefix}_D_v{ver}',
        )

    # ── Bouton Valider ────────────────────────────────────────────────────
    validated = st.button(
        '✅ Valider les modifications',
        key=f'{key_prefix}_valider',
        type='primary',
        use_container_width=True,
        help='Déclenche le recalcul de toutes les caractéristiques (flèche, MAC, surface…)',
    )

    if validated:
        for k in range(n_A):
            w['A'][k][0] = float(edited_A.iloc[k]['X Envergure [mm]'])
            w['A'][k][1] = float(edited_A.iloc[k]['Y Corde [mm]'])
        for i in range(2):
            w['B'][i][0] = float(edited_B.iloc[i]['X Envergure [mm]'])
            w['B'][i][1] = float(edited_B.iloc[i]['Y Corde [mm]'])
        w['C'] = C_new
        if edited_D is not None:
            for k in range(len(w['D'])):
                w['D'][k][0] = float(edited_D.iloc[k]['X Envergure [mm]'])
                w['D'][k][1] = float(edited_D.iloc[k]['Profondeur [mm]'])

    return w, validated


# ─── Calcul des caractéristiques ──────────────────────────────────────────────
def compute_car(wing: dict) -> dict:
    A, B, C_fus, D, trap = wing['A'], wing['B'], wing['C'], wing['D'], wing['trap']

    cord = {}
    cord[-1] = A[1][1] / 1000.0                               
    for i in range(1, trap + 1):
        cord[i] = (A[2*i+1][1] - A[2*i][1]) / 1000.0         

    # Corde au fuselage
    if A[2][0] > 0:
        cord[0] = cord[-1] - (A[2][1] + A[1][1] - A[3][1]) * C_fus / (A[2][0] * 1000.0)
    else:
        cord[0] = cord[-1]

    long_ = {}
    for i in range(1, trap + 1):
        long_[i] = (A[2*i][0] - A[2*(i-1)][0]) / 1000.0

    surf = {}
    S_demi = 0.0
    for i in range(1, trap + 1):
        surf[i] = (cord[i] + cord[i-1]) * long_[i] / 2.0
        S_demi += surf[i]

    # C_fus est la demi-largeur du fuselage (fidèle au Pascal GEOAILE)
    # Sext_demi = S_demi - (cord[0]+cord[-1])/2 * C_fus/1000  →  ×2 pour aile entière
    Sext = (S_demi - (cord[0] + cord[-1]) * C_fus / 2000.0) * 2.0
    Sref = S_demi * 2.0

    # Surface prolongée jusqu'à l'axe (sans correction fuselage) — valeur dossier Glasflügel p.7
    # On recalcule S_demi avec cord[-1] (corde à l'axe) comme base du 1er trapèze
    S_demi_prol = 0.0
    for i in range(1, trap + 1):
        # Si i=1, on utilise cord[-1] au lieu de cord[0] (pas de correction fuselage)
        c_base = cord[-1] if i == 1 else cord[i-1]
        S_demi_prol += (cord[i] + c_base) * long_[i] / 2.0
    Sref_prolongee = S_demi_prol * 2.0

    n = 2 * (trap + 1)
    env = 2.0 * max(A[n-1][0], A[n-2][0]) / 1000.0
    AR  = env**2 / Sref    if Sref > 0 else 0.0
    SMC = Sref / env       if env  > 0 else 0.0
    lam = cord[trap] / cord[-1] if cord[-1] > 0 else 0.0
    ki  = 1.0 / (np.pi * AR) if AR > 0 else 0.0

    phi_ba, phi_q, phi_d, phi_bf = {}, {}, {}, {}
    for i in range(1, trap + 1):
        li = long_[i]
        v1 = (A[2*i][1] - A[2*(i-1)][1]) / (1000.0 * li) if li > 0 else 0.0
        v2 = (cord[i] - cord[i-1]) / li                   if li > 0 else 0.0
        phi_ba[i] = np.degrees(np.arctan(v1))
        phi_q[i]  = np.degrees(np.arctan(v1 + v2 / 4))
        phi_d[i]  = np.degrees(np.arctan(v1 + v2 / 2))
        phi_bf[i] = np.degrees(np.arctan(v1 + v2))

    mac_n, mac_d, xn, yc = 0.0, 0.0, 0.0, 0.0
    for i in range(1, trap + 1):
        cr, ct, l = cord[i-1], cord[i], long_[i]
        la = ct / cr if cr > 0 else 0.0
        mi = (2/3) * cr * (1 + la + la**2) / (1 + la) if (1 + la) > 0 else 0.0
        xi = (l / 3) * (1 + 2*la) / (1 + la)          if (1 + la) > 0 else 0.0
        si = (cr + ct) * l / 2
        mac_n += mi * si
        mac_d += si
        xn += (yc + xi) * si
        yc += l

    MAC  = mac_n / mac_d if mac_d > 0 else 0.0
    MACx = xn   / mac_d  if mac_d > 0 else 0.0

    return {
        'cord': cord, 'long': long_, 'surf': surf,
        'Sref': Sref, 'Sext': Sext, 'Sref_prolongee': Sref_prolongee,
        'env': env, 'AR': AR, 'SMC': SMC, 'lam': lam, 'ki': ki,
        'phi_ba': phi_ba, 'phi_q': phi_q, 'phi_d': phi_d, 'phi_bf': phi_bf,
        'MAC': MAC, 'MACx': MACx,
    }

def _bf_interp(A: list, I_pascal: int, x_mm: float) -> float:
    ai = A[2 * I_pascal - 1]      
    ao = A[2 * I_pascal + 1]      
    dx = ao[0] - ai[0]
    if abs(dx) < 1e-9:
        return float(ai[1])
    return ai[1] - (x_mm - ai[0]) * (ai[1] - ao[1]) / dx

# ─── Visualisation planforme ──────────────────────────────────────────────────
def plot_planforme(wing: dict, car: dict, spar_pct: float = 0.35) -> plt.Figure:
    A, B, C_fus, D, trap = wing['A'], wing['B'], wing['C'], wing['D'], wing['trap']
    nom = wing['nom']

    fig, ax = plt.subplots(figsize=(13, 5))
    colors = ['royalblue', 'seagreen', 'orange']

    # ── Plan de forme ─────────────────────────────────────────────────────
    for i in range(trap):
        c = colors[i % len(colors)]
        i0 = 2 * i
        poly_x = [A[i0][0]/1000, A[i0+2][0]/1000, A[i0+3][0]/1000, A[i0+1][0]/1000, A[i0][0]/1000]
        poly_y = [A[i0][1]/1000, A[i0+2][1]/1000, A[i0+3][1]/1000, A[i0+1][1]/1000, A[i0][1]/1000]
        ax.fill(poly_x, poly_y, alpha=0.15, color=c)
        ax.plot(poly_x, poly_y, color=c, lw=2)

    # Labels A
    for k, pt in enumerate(A):
        ax.plot(pt[0]/1000, pt[1]/1000, 'o', ms=4, color='#888888', zorder=5)
        ax.annotate(f'A{k+1}', (pt[0]/1000, pt[1]/1000), fontsize=7, color='#555555',
                    xytext=(3, 6 if k % 2 == 0 else -12), textcoords='offset points', zorder=5)

    # ── Frontière fuselage — C est la demi-largeur du fuselage (fidèle au Pascal :
    # DRAWLINE(C, A[1,2], C, A[2,2]) utilise C directement comme abscisse)
    if C_fus > 0:
        limite_fuselage = C_fus / 1000.0  # C = demi-largeur → abscisse directe en m
        ax.axvline(x=limite_fuselage, color='gray', linestyle=':', lw=2, zorder=2)
        ax.text(limite_fuselage + 0.05, 0.8, f'Fuselage (C={C_fus:.0f} mm)', color='gray', fontsize=9, rotation=90)

    # ── Longeron Structurel (position configurable en % de la corde) ─────
    x_spar = []
    y_spar = []
    for i in range(trap):
        x0 = A[2*i][0] / 1000.0
        x1 = A[2*i+2][0] / 1000.0
        y_ba_0 = A[2*i][1] / 1000.0
        y_bf_0 = A[2*i+1][1] / 1000.0
        y_ba_1 = A[2*i+2][1] / 1000.0
        y_bf_1 = A[2*i+3][1] / 1000.0

        c0 = y_bf_0 - y_ba_0
        c1 = y_bf_1 - y_ba_1

        if i == 0:
            x_spar.append(x0)
            y_spar.append(y_ba_0 + spar_pct * c0)
        x_spar.append(x1)
        y_spar.append(y_ba_1 + spar_pct * c1)

    ax.plot(x_spar, y_spar, color='dimgray', lw=3, linestyle='-.',
            label=f'Longeron principal ({spar_pct*100:.0f}% corde)', zorder=4)

    # ── Aérofrein B ───────────────────────────────────────────────────────
    if B[1][0] > B[0][0]:
        largeur_af = 120.0
        y_af = B[0][1] / 1000.0   # seul B1.Y fait foi — Pascal : B[2,2] := B[1,2] + 4*ECHY
        ab_x = [B[0][0]/1000, B[1][0]/1000, B[1][0]/1000, B[0][0]/1000, B[0][0]/1000]
        ab_y = [y_af, y_af, y_af + largeur_af/1000, y_af + largeur_af/1000, y_af]
        ax.fill(ab_x, ab_y, color='gold', alpha=0.70, label='Aérofrein')
        ax.plot(ab_x, ab_y, color='goldenrod', lw=1.5)
        
        ax.plot(B[0][0]/1000, B[0][1]/1000, 'o', ms=5, color='darkorange', zorder=5)
        ax.annotate('B1', (B[0][0]/1000, B[0][1]/1000), fontsize=8, color='black',
                    xytext=(-12, -12), textcoords='offset points', fontweight='bold')
        
        ax.plot(B[1][0]/1000, B[1][1]/1000, 'o', ms=5, color='darkorange', zorder=5)
        ax.annotate('B2', (B[1][0]/1000, B[1][1]/1000), fontsize=8, color='black',
                    xytext=(4, -12), textcoords='offset points', fontweight='bold')

    # ── Ailerons D ────────────────────────────────────────────────────────
    d_counter = 1
    for ti in range(1, trap + 1):
        j1, j2 = 2*ti - 2, 2*ti - 1
        if j2 < len(D) and D[j1][0] > 0 and D[j2][0] > 0:
            x1, d1 = D[j1][0], D[j1][1]
            x2, d2 = D[j2][0], D[j2][1]
            if x2 == 0:
                x2 = float(A[2*ti][0])
            bf_1 = _bf_interp(A, ti, x1)
            bf_2 = _bf_interp(A, ti, x2)
            
            ail_x = [x1/1000, x2/1000, x2/1000, x1/1000, x1/1000]
            ail_y = [(bf_1-d1)/1000, (bf_2-d2)/1000, bf_2/1000, bf_1/1000, (bf_1-d1)/1000]
            ax.fill(ail_x, ail_y, color='lightgreen', alpha=0.70,
                    label='Aileron' if ti == 1 else '_nolegend_')
            ax.plot(ail_x, ail_y, color='darkgreen', lw=1.5)
            
            ax.plot(x1/1000, (bf_1-d1)/1000, 'o', ms=4, color='darkgreen', zorder=5)
            ax.annotate(f'D{d_counter}', (x1/1000, (bf_1-d1)/1000), fontsize=8, color='black',
                        xytext=(-15, -5), textcoords='offset points')
            d_counter += 1
            
            ax.plot(x2/1000, (bf_2-d2)/1000, 'o', ms=4, color='darkgreen', zorder=5)
            ax.annotate(f'D{d_counter}', (x2/1000, (bf_2-d2)/1000), fontsize=8, color='black',
                        xytext=(5, -5), textcoords='offset points')
            d_counter += 1

    # ── MAC ───────────────────────────────────────────────────────────────
    x_mac = car['MACx']
    mac   = car['MAC']
    y_ba_mac = 0.0
    for i in range(trap):
        x0 = A[2*i][0] / 1000.0
        x1 = A[2*i+2][0] / 1000.0
        if x0 <= x_mac <= x1 and x1 > x0:
            t = (x_mac - x0) / (x1 - x0)
            y_ba_mac = (A[2*i][1] + t * (A[2*i+2][1] - A[2*i][1])) / 1000.0
            break
            
    ax.annotate('', xy=(x_mac+0.13, y_ba_mac+0.02),
                xytext=(x_mac+0.13, y_ba_mac+mac-0.02),
                arrowprops=dict(arrowstyle='<->', color='tomato', lw=1.5))
    ax.text(x_mac+0.20, y_ba_mac+mac/2, f'MAC\n{mac:.3f} m',
            color='tomato', fontsize=7.5, va='center')

    ax.set_xlabel('X (Envergure) [m]', fontsize=11, fontweight='bold')
    ax.set_ylabel('Y (Corde) [m]', fontsize=11, fontweight='bold')
    ax.set_title(f"Planforme — {nom}  ({trap} trapèze{'s' if trap > 1 else ''})",
                 fontsize=12)
                 
    ax.set_xlim(-0.3, A[-1][0]/1000 + 0.5)
    ax.invert_yaxis()
    ax.set_aspect('equal')
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    return fig

# ─── Interface Streamlit ──────────────────────────────────────────────────────
def render():
    import copy

    st.title('Module 1 — Géométrie aile (GEOAILE)')
    st.caption('Fidèle à GEOAILE ENSAE 1990 (Prodhomme) · Fichiers .AIL · '
               'Sref/Sext · MAC · Angles de flèche · Planforme')

    # ── Application des valeurs de trapèzes issues d'une validation précédente
    # Doit se faire AVANT la création des widgets (sinon StreamlitAPIException)
    if 'geo_pending_segs' in st.session_state:
        pending = st.session_state.pop('geo_pending_segs')
        for i, seg in enumerate(pending['segs']):
            if i == 0:
                st.session_state[f'cr{i}'] = round(seg['c_root'], 4)
            st.session_state[f'ct{i}'] = round(seg['c_tip'],  4)
            st.session_state[f'db{i}'] = round(seg['demi_b'], 4)
            st.session_state[f'fl{i}'] = round(seg['fleche'], 2)
        if 'C_fus' in pending:
            st.session_state['C_fus_manual'] = pending['C_fus']
        st.session_state['geo_segs_hash'] = pending['hash']

    # ── Sélection source ──────────────────────────────────────────────────
    with st.sidebar:
        st.subheader('Source du profil de voilure')
        source = st.radio('', [
            'H201B — Libelle (défaut)',
            'Charger un fichier .AIL',
            'Définir manuellement',
        ])

    # ── Réinitialise session_state si la source change ────────────────────
    if st.session_state.get('geo_source') != source:
        st.session_state['geo_source'] = source
        for k in ('geo_wing', 'geo_file_id', 'geo_segs_hash', 'geo_edit_ver'):
            st.session_state.pop(k, None)

    # ── Construction de l'aile initiale selon la source ──────────────────
    if source == 'H201B — Libelle (défaut)':
        if 'geo_wing' not in st.session_state:
            st.session_state['geo_wing'] = copy.deepcopy(H201B)

    elif source == 'Charger un fichier .AIL':
        uploaded = st.file_uploader('Fichier .AIL (glisser-déposer)',
                                    type=['ail', 'AIL', 'txt'])
        if uploaded is None:
            st.info('Chargez un fichier .AIL ou sélectionnez H201B.')
            return
        file_id = uploaded.name + str(uploaded.size)
        if st.session_state.get('geo_file_id') != file_id:
            text = uploaded.read().decode('latin-1', errors='ignore')
            nom  = uploaded.name.replace('.AIL','').replace('.ail','').upper()
            parsed = parse_ail(text, nom)
            if parsed is None:
                st.error("Format .AIL non reconnu — vérifiez que le fichier contient TRAP: ...")
                return
            st.session_state['geo_wing']   = parsed
            st.session_state['geo_file_id'] = file_id
            st.session_state.pop('geo_edit_ver', None)
        st.success(f"Fichier : {st.session_state['geo_wing']['nom']} "
                   f"— {st.session_state['geo_wing']['trap']} trapèze(s)")

    else:  # Définir manuellement
        with st.sidebar:
            st.subheader('Trapèzes')
            n_seg = st.radio('Nombre de trapèzes', [1, 2, 3], index=1)
            defaults_cr = [0.90, 0.63, 0.36]
            defaults_ct = [0.63, 0.36, 0.20]
            defaults_db = [4.40, 3.10, 1.50]
            segs = []
            for i in range(n_seg):
                st.markdown(f'**Trapèze {i+1}**')
                cr_d = defaults_cr[i] if i < len(defaults_cr) else 0.30
                ct_d = defaults_ct[i] if i < len(defaults_ct) else 0.20
                db_d = defaults_db[i] if i < len(defaults_db) else 1.50
                if i > 0:
                    cr_d = segs[-1]['c_tip']
                    st.caption(f"Corde empl. = {cr_d:.3f} m (raccordée)")
                cr = (st.number_input('Corde empl. [m]', 0.1, 3.0, cr_d, 0.01,
                                      key=f'cr{i}') if i == 0 else cr_d)
                ct = st.number_input('Corde sau. [m]', 0.1, 3.0, ct_d, 0.01, key=f'ct{i}')
                db = st.number_input('Demi-enverg. [m]', 0.5, 20.0, db_d, 0.05, key=f'db{i}')
                fl = st.number_input('Flèche BA [°]', -10.0, 45.0, 0.0, 0.5, key=f'fl{i}')
                segs.append({'c_root': cr, 'c_tip': ct, 'demi_b': db, 'fleche': fl})
                if i < n_seg - 1:
                    st.divider()
            nom_m = st.text_input('Nom', 'MON_AILE').upper()
            C_fus = st.number_input('Largeur Fuselage C [mm]', 0.0, 2000.0, 425.0, 10.0,
                                    key='C_fus_manual')

        segs_hash = str(segs) + nom_m + str(C_fus)
        if st.session_state.get('geo_segs_hash') != segs_hash:
            st.session_state['geo_segs_hash'] = segs_hash
            st.session_state['geo_wing'] = segments_to_wing(segs, nom_m, C_fus)
            st.session_state.pop('geo_edit_ver', None)

    if 'geo_wing' not in st.session_state:
        return

    wing = st.session_state['geo_wing']

    # ── Bouton Sauvegarder (sidebar, toutes sources) ──────────────────────
    ail_text = wing_to_ail(wing)
    st.sidebar.divider()
    st.sidebar.download_button(
        label='💾 Sauvegarder en .AIL',
        data=ail_text.encode('latin-1'),
        file_name=f"{wing['nom']}.AIL",
        mime='text/plain',
        help='Télécharge la géométrie actuelle (après validation) au format .AIL',
    )

    # ── Calculs ───────────────────────────────────────────────────────────
    car  = compute_car(wing)
    trap = wing['trap']

    # ── Caractéristiques géométriques ─────────────────────────────────────
    st.subheader('Caractéristiques géométriques')

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Sref (prolongée)', f"{car['Sref_prolongee']:.3f} m²",
              help='Surface de référence — voilure prolongée jusqu\'à l\'axe (dossier Glasflügel p.7 : 9,80 m²)')
    c2.metric('Sext (exposée)', f"{car['Sext']:.3f} m²",
              help='Surface exposée hors fuselage')
    c3.metric('Envergure b', f"{car['env']:.3f} m")
    c4.metric('Allongement AR', f"{car['AR']:.2f}")
    c5.metric('Effilement λ', f"{car['lam']:.4f}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('MAC', f"{car['MAC']:.4f} m",
              help='Corde Aérodynamique Moyenne — NACA TN 1270')
    c2.metric('Position MAC (X)', f"{car['MACx']:.3f} m")
    c3.metric('SMC (corde moy.)', f"{car['SMC']:.4f} m")
    c4.metric('ki = 1/(π·AR)', f"{car['ki']:.5f}")

    st.subheader('Cordes aux sections clés')
    cols = st.columns(trap + 2)
    cols[0].metric('C[-1] axe symétrie', f"{car['cord'][-1]:.4f} m")
    cols[1].metric('C[0] bord fuselage', f"{car['cord'][0]:.4f} m",
                   help='Extrapolée à la sortie du fuselage')
    for i in range(1, trap + 1):
        cols[i+1].metric(f'C[{i}] saumon tr.{i}', f"{car['cord'][i]:.4f} m")

    st.divider()

    # ── Planforme ─────────────────────────────────────────────────────────
    st.subheader('Planforme (demi-aile)')
    spar_pct = st.slider(
        'Position du longeron (% de la corde)',
        min_value=10, max_value=60, value=35, step=1,
        help='Convention usuelle planeurs : 25–40 %. H201B : valeur à confirmer sur plans.'
    ) / 100.0
    fig = plot_planforme(wing, car, spar_pct=spar_pct)
    st.pyplot(fig)
    plt.close(fig)

    # ── Tableau des points — éditable, avec bouton Valider ───────────────
    with st.expander('Tableau des points géométriques', expanded=True):
        wing_from_tables, validated = _tables_edit_wing(
            st.session_state['geo_wing'], key_prefix='geo'
        )
        if validated:
            st.session_state['geo_wing'] = wing_from_tables
            st.session_state['geo_edit_ver'] = (
                st.session_state.get('geo_edit_ver', 0) + 1
            )
            # En mode "Définir manuellement" : rétro-calcul des paramètres de trapèzes.
            # On NE peut PAS écrire dans les clés de widget déjà instanciés (cr0, ct0…)
            # dans ce run — on passe par une clé temporaire lue au run suivant (voir haut de render).
            if source == 'Définir manuellement':
                new_segs = _wing_to_segs(wing_from_tables)
                nom_m = wing_from_tables['nom']
                C_fus_new = wing_from_tables['C']
                st.session_state['geo_pending_segs'] = {
                    'segs':  new_segs,
                    'C_fus': C_fus_new,
                    'hash':  str(new_segs) + nom_m + str(C_fus_new),
                }
            st.rerun()