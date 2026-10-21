import streamlit as st


def render():
    st.title("Logiciel de calcul planeur solaire")
    st.markdown("""
    Application de calcul aéronautique pour le projet **Khépri** : planeur solaire photovoltaïque
    basé sur le Glasflügel H201B Standard Libelle.

    ---

    ### Chaîne de calcul

    ```
    GEOAILE  →  LISCAR  →  Portance  →  DOMAINE  →  MECAVOL  →  EFFORTS
    ```

    | Module | Rôle | Entrées | Sorties |
    |---|---|---|---|
    | GEOAILE | [Géométrie](https://fr.wikipedia.org/wiki/Voilure) voilure | [Cordes](https://fr.wikipedia.org/wiki/Corde_(a%C3%A9ronautique)), [envergure](https://fr.wikipedia.org/wiki/Envergure), trapèzes | [Surface alaire](https://fr.wikipedia.org/wiki/Surface_alaire), [allongement](https://fr.wikipedia.org/wiki/Allongement_(a%C3%A9ronautique)) |
    | LISCAR | [Profil](https://fr.wikipedia.org/wiki/Profil_NACA) aérodynamique | Points profil bruts | Polynôme lissé |
    | Portance | [Polaire](https://fr.wikipedia.org/wiki/Polaire_(a%C3%A9ronautique)) elliptique | Géométrie + profil | Cz, Cx, [finesse](https://fr.wikipedia.org/wiki/Finesse_(a%C3%A9ronautique)) |
    | DOMAINE | Enveloppe de vol | Masse, surface, coefficients aéro | [Diagramme V-n](https://fr.wikipedia.org/wiki/Enveloppe_de_vol) (JAR-22) |
    | MECAVOL | Charges sur l'aile | Distribution [portance](https://fr.wikipedia.org/wiki/Portance_(a%C3%A9ronautique)) | Courbe des charges |
    | EFFORTS | Contraintes structure | Courbe majorante | Taux de contraintes f(y) |

    ---

    ### Données de référence H201B
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Envergure", "15 m")
        st.metric("Surface alaire", "9.80 m²")
        st.metric("Allongement λ", "23")
    with col2:
        st.metric("Masse maximale", "350 kg")
        st.metric("Corde emplanture", "0.90 m")
        st.metric("Corde saumon", "0.36 m")
    with col3:
        st.metric("Finesse max", "≈ 40")
        st.metric("Vitesse finesse max", "≈ 87 km/h")
        st.metric("Longueur", "6.20 m")

    st.markdown("""
    ---
    ### Spécificités Khépri
    - Panneaux solaires monocristallins (η = 16%) sur l'extrados des ailes
    - Batteries Li-Ion (190 Wh/kg)
    - Hélices rétractables en bord de fuite (entre aileron et emplanture, avant aérofrein)
    - **Normes JAR-22** — identiques à la certification du H201B
    """)

    with st.expander("📖 Lexique des termes aéronautiques"):
        st.markdown("""
| Terme | Définition courte | Lien |
|---|---|---|
| Corde | Longueur de l'aile mesurée du bord d'attaque au bord de fuite | [Wikipedia](https://fr.wikipedia.org/wiki/Corde_(a%C3%A9ronautique)) |
| Envergure | Distance d'un bout d'aile à l'autre | [Wikipedia](https://fr.wikipedia.org/wiki/Envergure) |
| Profil NACA | Section transversale de l'aile, normalisée par le NACA (USA) | [Wikipedia](https://fr.wikipedia.org/wiki/Profil_NACA) |
| Surface alaire | Aire totale de la voilure vue de dessus | [Wikipedia](https://fr.wikipedia.org/wiki/Surface_alaire) |
| Allongement | Rapport envergure²/surface — mesure l'élancement de l'aile | [Wikipedia](https://fr.wikipedia.org/wiki/Allongement_(a%C3%A9ronautique)) |
| Portance | Force verticale qui soutient l'avion en l'air | [Wikipedia](https://fr.wikipedia.org/wiki/Portance_(a%C3%A9ronautique)) |
| Traînée | Force qui s'oppose au mouvement de l'avion (frottement + turbulences) | [Wikipedia](https://fr.wikipedia.org/wiki/Tra%C3%AEn%C3%A9e) |
| Finesse | Rapport portance/traînée — qualité aérodynamique globale | [Wikipedia](https://fr.wikipedia.org/wiki/Finesse_(a%C3%A9ronautique)) |
| Polaire | Courbe vitesse de chute vs vitesse horizontale | [Wikipedia](https://fr.wikipedia.org/wiki/Polaire_(a%C3%A9ronautique)) |
| MAC | Corde aérodynamique moyenne — corde de référence pour les calculs | [Wikipedia](https://fr.wikipedia.org/wiki/Corde_a%C3%A9rodynamique_moyenne) |
| Longeron | Poutre principale de l'aile, supporte les efforts de flexion | [Wikipedia](https://fr.wikipedia.org/wiki/Longeron) |
| Aérofrein | Volet sur l'extrados qui augmente la traînée pour contrôler la descente | [Wikipedia](https://fr.wikipedia.org/wiki/A%C3%A9rofrein) |
| Facteur de charge n | Rapport portance/poids — mesure l'intensité d'une manœuvre | [Wikipedia](https://fr.wikipedia.org/wiki/Facteur_de_charge) |
| Diagramme V-n | Enveloppe de vol : limites de charge en fonction de la vitesse | [Wikipedia](https://fr.wikipedia.org/wiki/Enveloppe_de_vol) |
| JAR-22 | Réglementation européenne de certification des planeurs | [EASA](https://www.easa.europa.eu/en/document-library/certification-specifications/cs-22-sailplanes-and-powered-sailplanes) |
| Emplanture | Racine de l'aile, côté fuselage (section la plus large) | — |
| Saumon | Extrémité de l'aile (section la plus étroite) | — |
| Effilement | Rapport corde saumon / corde emplanture | — |
        """)

