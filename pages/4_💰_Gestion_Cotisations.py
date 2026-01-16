"""
Page Cotisations
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from database import DB_NAME
from constants import MOIS_NOMS, COTISATION_MIN, COTISATION_PAR_TERRAIN
from auth import require_authentication, show_logout_button
from generate_report_pdf import generer_rapport_participant
from historique import ajouter_historique

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# REQUÊTES COTISATIONS
# ============================================================================

def get_all_participants():
    """Récupère tous les participants"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, nom, prenom, nombre_terrains FROM participants ORDER BY nom, prenom"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_all_cotisations():
    """Récupère toutes les cotisations avec les informations des participants"""
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT 
            c.id, 
            c.participant_id,
            p.nom || ' ' || p.prenom as participant,
            p.nom,
            p.prenom,
            p.nombre_terrains,
            c.mois,
            c.annee,
            c.montant,
            c.paye,
            c.date_paiement,
            c.numero_terrain
        FROM cotisations c
        JOIN participants p ON c.participant_id = p.id
        ORDER BY c.annee DESC, c.mois DESC, p.nom, p.prenom, c.numero_terrain
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_cotisation(participant_id, mois, annee, montant, paye=False, numero_terrain=None):
    """Ajoute une nouvelle cotisation"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        date_paiement = datetime.now().strftime("%Y-%m-%d") if paye else None
        
        # Si numero_terrain est None (tous les terrains), on obtient le nombre de terrains
        if numero_terrain is None:
            cursor.execute("SELECT nombre_terrains FROM participants WHERE id = ?", (participant_id,))
            nb_terrains = cursor.fetchone()[0]
            
            if nb_terrains == 0:
                return False, "Ce participant n'a aucun terrain"
            
            # Montant par terrain
            montant_par_terrain = montant / nb_terrains
            
            # Créer une cotisation pour chaque terrain
            for i in range(1, nb_terrains + 1):
                cursor.execute(
                    "INSERT INTO cotisations (participant_id, mois, annee, montant, paye, date_paiement, numero_terrain) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (participant_id, mois, annee, montant_par_terrain, 1 if paye else 0, date_paiement, i)
                )
            message = f"Cotisation ajoutée avec succès ({nb_terrains} terrains, {montant_par_terrain:,.0f} FCFA chacun)".replace(',', ' ')
        else:
            # Créer une seule cotisation pour le terrain spécifique
            cursor.execute(
                "INSERT INTO cotisations (participant_id, mois, annee, montant, paye, date_paiement, numero_terrain) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (participant_id, mois, annee, montant, 1 if paye else 0, date_paiement, numero_terrain)
            )
            message = f"Cotisation ajoutée avec succès (Terrain n°{numero_terrain})"
        
        conn.commit()
        
        # Enregistrer dans l'historique
        ajouter_historique(
            'CREATE',
            'cotisations',
            participant_id,
            f"Création cotisation(s) mois {mois}/{annee} - Montant: {montant} FCFA",
            None,
            {'mois': mois, 'annee': annee, 'montant': montant, 'paye': paye, 'numero_terrain': numero_terrain}
        )
        
        conn.close()
        return True, message
    except sqlite3.IntegrityError:
        return False, "Cette cotisation existe déjà pour ce terrain"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def update_cotisation_status(cotisation_id, paye, montant_paye=None):
    """Met à jour le statut de paiement d'une cotisation"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        date_paiement = datetime.now().strftime("%Y-%m-%d") if paye else None
        
        # Si un montant est spécifié, on le met à jour
        if montant_paye is not None:
            cursor.execute(
                "UPDATE cotisations SET paye = ?, date_paiement = ?, montant = ? WHERE id = ?",
                (1 if paye else 0, date_paiement, montant_paye, cotisation_id)
            )
        else:
            cursor.execute(
                "UPDATE cotisations SET paye = ?, date_paiement = ? WHERE id = ?",
                (1 if paye else 0, date_paiement, cotisation_id)
            )
        
        conn.commit()
        
        # Enregistrer dans l'historique
        statut_txt = "payée" if paye else "non payée"
        montant_txt = f" - Montant: {montant_paye} FCFA" if montant_paye else ""
        ajouter_historique(
            'UPDATE',
            'cotisations',
            cotisation_id,
            f"Cotisation marquée comme {statut_txt}{montant_txt}",
            {'paye': not paye},
            {'paye': paye, 'montant': montant_paye}
        )
        
        conn.close()
        return True
    except Exception as e:
        return False


def delete_cotisation(cotisation_id):
    """Supprime une cotisation"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Récupérer les infos avant suppression
        cursor.execute("SELECT participant_id, mois, annee, montant FROM cotisations WHERE id = ?", (cotisation_id,))
        cotis_info = cursor.fetchone()
        
        cursor.execute("DELETE FROM cotisations WHERE id = ?", (cotisation_id,))
        conn.commit()
        
        # Enregistrer dans l'historique
        if cotis_info:
            ajouter_historique(
                'DELETE',
                'cotisations',
                cotisation_id,
                f"Suppression cotisation {cotis_info[1]}/{cotis_info[2]} - Montant: {cotis_info[3]} FCFA",
                {'participant_id': cotis_info[0], 'mois': cotis_info[1], 'annee': cotis_info[2], 'montant': cotis_info[3]},
                None
            )
        
        conn.close()
        return True, "Cotisation supprimée avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"


def generer_cotisations_mensuelles(mois, annee):
    """Génère les cotisations impayées pour tous les participants pour un mois donné (une par terrain)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Récupérer tous les participants avec leur nombre de terrains
        cursor.execute("SELECT id, nom, prenom, nombre_terrains FROM participants WHERE nombre_terrains > 0")
        participants = cursor.fetchall()
        
        nb_ajoutes = 0
        nb_existent = 0
        
        for participant_id, nom, prenom, nb_terrains in participants:
            # Créer une cotisation pour chaque terrain
            for numero_terrain in range(1, nb_terrains + 1):
                # Vérifier si la cotisation existe déjà pour ce terrain
                cursor.execute(
                    "SELECT id FROM cotisations WHERE participant_id = ? AND mois = ? AND annee = ? AND numero_terrain = ?",
                    (participant_id, mois, annee, numero_terrain)
                )
                
                if cursor.fetchone() is None:
                    # Créer la cotisation impayée pour ce terrain
                    cursor.execute(
                        "INSERT INTO cotisations (participant_id, mois, annee, montant, paye, numero_terrain) VALUES (?, ?, ?, ?, 0, ?)",
                        (participant_id, mois, annee, COTISATION_PAR_TERRAIN, numero_terrain)
                    )
                    nb_ajoutes += 1
                else:
                    nb_existent += 1
        
        conn.commit()
        conn.close()
        
        return True, f"✅ {nb_ajoutes} cotisation(s) créée(s). {nb_existent} existait(ent) déjà."
    except Exception as e:
        return False, f"Erreur: {str(e)}"


# Configuration de la page
st.set_page_config(
    page_title="Cotisations - MEDD",
    page_icon="💰",
    layout="wide"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    /* Amélioration du titre principal */
    h1 {
        color: #fc6b03;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        padding-bottom: 1rem;
        border-bottom: 3px solid #fc6b03;
        margin-bottom: 2rem;
    }
    
    /* Amélioration des sous-titres */
    h2, h3 {
        color: #fc6b03;
        font-weight: 600 !important;
    }
    
    /* Style des cartes/conteneurs */
    .stExpander {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Style des métriques */
    [data-testid="stMetricValue"] {
        color: #fc6b03;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* Amélioration des conteneurs */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Style des boutons primaires */
    .stButton > button[kind="primary"] {
        background-color: #fc6b03;
        border-color: #fc6b03;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #e35f02;
        border-color: #e35f02;
    }
    
    /* Style des dividers */
    hr {
        border-color: #fc6b03;
        margin: 2rem 0;
    }
    
    /* Style du conteneur avec scroll */
    [data-testid="stVerticalBlock"] > div:has(> div > div > div.stMarkdown) {
        background-color: #fafafa;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Amélioration des inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border-color: #e0e0e0;
    }
    
    /* Messages de succès */
    .stSuccess {
        background-color: #e8f5e9;
        color: #2e7d32;
        border-left: 4px solid #4caf50;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Messages d'erreur */
    .stError {
        background-color: #ffebee;
        color: #c62828;
        border-left: 4px solid #f44336;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Messages d'avertissement */
    .stWarning {
        background-color: #fff3e0;
        color: #e65100;
        border-left: 4px solid #ff9800;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Messages d'info */
    .stInfo {
        background-color: #e3f2fd;
        color: #0d47a1;
        border-left: 4px solid #2196f3;
        border-radius: 8px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Gestion des Cotisations")

# Initialiser session_state pour le paiement en cours
if 'paiement_cotisation_id' not in st.session_state:
    st.session_state.paiement_cotisation_id = None
if 'delete_cotisation_id' not in st.session_state:
    st.session_state.delete_cotisation_id = None

# Génération automatique des cotisations mensuelles
with st.expander("🔄 Générer les cotisations mensuelles automatiquement", expanded=False):
    st.write(f"**Génère des cotisations impayées pour tous les participants ayant des terrains.**")
    st.write(f"Montant calculé : {COTISATION_PAR_TERRAIN:,.0f}".replace(',', ' ') + f" FCFA × nombre de terrains")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        gen_mois_dict = {nom: i+1 for i, nom in enumerate(MOIS_NOMS)}
        gen_mois = st.selectbox("Mois", options=list(gen_mois_dict.keys()), 
                                index=datetime.now().month - 1, key="gen_mois")
    with col2:
        gen_annee = st.number_input("Année", min_value=2025, max_value=2100, 
                                   value=datetime.now().year, step=1, key="gen_annee")
    with col3:
        st.write("")  # Espacement
        if st.button("🚀 Générer", type="primary", use_container_width=True):
            mois_num = gen_mois_dict[gen_mois]
            success, msg = generer_cotisations_mensuelles(mois_num, gen_annee)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

# Formulaire d'ajout rapide pour plusieurs terrains avec montants différents
with st.expander("➕➕ Ajouter des cotisations avec montants différents par terrain", expanded=False):
    st.info("💡 **Ajoutez rapidement plusieurs cotisations pour le même mois avec des montants différents par terrain**")
    
    participants_df = get_all_participants()
    
    if participants_df.empty:
        st.warning("Aucun participant enregistré. Veuillez d'abord ajouter des participants.")
    else:
        # Créer un dictionnaire pour le selectbox
        participants_dict = {f"{row['nom']} {row['prenom']}": (row['id'], row['nombre_terrains']) 
                           for _, row in participants_df.iterrows()}
        
        col1, col2 = st.columns(2)
        with col1:
            selected_participant_multi = st.selectbox("Participant *", options=list(participants_dict.keys()), key="multi_participant")
            participant_id_multi, nb_terrains_multi = participants_dict[selected_participant_multi]
        with col2:
            mois_dict = {nom: i+1 for i, nom in enumerate(MOIS_NOMS)}
            selected_mois_multi = st.selectbox("Mois *", options=list(mois_dict.keys()),
                                        index=datetime.now().month - 1, key="multi_mois")
        
        annee_multi = st.number_input("Année *", min_value=2000, max_value=2100, 
                               value=datetime.now().year, step=1, key="multi_annee")
        
        paye_multi = st.checkbox("Déjà payées", value=False, key="multi_paye")
        
        st.divider()
        
        if nb_terrains_multi > 0:
            st.write(f"**Montants par terrain ({nb_terrains_multi} terrain(s))**")
            
            # Créer des inputs pour chaque terrain
            montants_terrains = {}
            cols_terrains = st.columns(min(4, nb_terrains_multi))
            for i in range(1, nb_terrains_multi + 1):
                col_idx = (i - 1) % 4
                with cols_terrains[col_idx]:
                    montant_terrain = st.number_input(
                        f"Terrain n°{i} (FCFA)",
                        min_value=0.0,
                        value=float(COTISATION_PAR_TERRAIN),
                        step=10.0,
                        format="%.0f",
                        key=f"terrain_{i}_montant_multi"
                    )
                    montants_terrains[i] = montant_terrain
            
            # Afficher le total
            total_multi = sum(montants_terrains.values())
            st.metric("💰 Total", f"{total_multi:,.0f}".replace(',', ' ') + " FCFA")
        else:
            st.warning("⚠️ Ce participant n'a aucun terrain")
            montants_terrains = {}
        
        st.divider()
        
        if st.button("Ajouter toutes les cotisations", type="primary", key="submit_multi"):
            if nb_terrains_multi == 0:
                st.error("❌ Impossible d'ajouter des cotisations : ce participant n'a aucun terrain")
            elif not montants_terrains:
                st.error("❌ Aucun montant saisi")
            else:
                mois_num_multi = mois_dict[selected_mois_multi]
                
                # Ajouter une cotisation pour chaque terrain avec son montant
                nb_ajoutees = 0
                nb_erreurs = 0
                erreurs_details = []
                
                for terrain_num, montant_val in montants_terrains.items():
                    if montant_val > 0:  # Seulement si le montant est supérieur à 0
                        success, msg = add_cotisation(
                            participant_id_multi, 
                            mois_num_multi, 
                            annee_multi, 
                            montant_val, 
                            paye_multi, 
                            terrain_num
                        )
                        if success:
                            nb_ajoutees += 1
                        else:
                            nb_erreurs += 1
                            erreurs_details.append(f"Terrain n°{terrain_num}: {msg}")
                
                # Afficher le résultat
                if nb_ajoutees > 0:
                    st.success(f"✅ {nb_ajoutees} cotisation(s) ajoutée(s) avec succès")
                if nb_erreurs > 0:
                    st.warning(f"⚠️ {nb_erreurs} erreur(s) :")
                    for err in erreurs_details:
                        st.write(f"  - {err}")
                
                if nb_ajoutees > 0:
                    st.rerun()

# Formulaire d'ajout de cotisation
with st.expander("➕ Ajouter une cotisation", expanded=False):
    participants_df = get_all_participants()
    
    if participants_df.empty:
        st.warning("Aucun participant enregistré. Veuillez d'abord ajouter des participants.")
    else:
        with st.form("form_cotisation", clear_on_submit=True):
            # Créer un dictionnaire pour le selectbox
            participants_dict = {f"{row['nom']} {row['prenom']}": (row['id'], row['nombre_terrains']) 
                               for _, row in participants_df.iterrows()}
            
            col1, col2 = st.columns(2)
            with col1:
                selected_participant = st.selectbox("Participant *", options=list(participants_dict.keys()))
                participant_id, nb_terrains = participants_dict[selected_participant]
                
                # Sélection du terrain
                if nb_terrains > 0:
                    terrains_options = ["Tous les terrains"] + [f"Terrain n°{i}" for i in range(1, nb_terrains + 1)]
                    selected_terrain = st.selectbox(
                        f"Terrain * ({nb_terrains} terrain(s) disponible(s))",
                        options=terrains_options,
                        help="Si 'Tous les terrains' est sélectionné, le montant sera réparti équitablement entre tous les terrains"
                    )
                else:
                    st.warning("⚠️ Ce participant n'a aucun terrain")
                    selected_terrain = "Tous les terrains"
                
                annee = st.number_input("Année *", min_value=2000, max_value=2100, 
                                       value=datetime.now().year, step=1)
            with col2:
                mois_dict = {nom: i+1 for i, nom in enumerate(MOIS_NOMS)}
                selected_mois = st.selectbox("Mois *", options=list(mois_dict.keys()),
                                            index=datetime.now().month - 1)
                montant = st.number_input(f"Montant (FCFA) * (min: {COTISATION_MIN:,.0f} FCFA)".replace(',', ' '), 
                                         min_value=float(COTISATION_MIN), value=1000.0, step=100.0, format="%.0f")
            
            paye = st.checkbox("Déjà payée", value=False)
            
            submitted = st.form_submit_button("Ajouter la cotisation")
            
            if submitted:
                if nb_terrains == 0:
                    st.error("❌ Impossible d'ajouter une cotisation : ce participant n'a aucun terrain")
                else:
                    mois_num = mois_dict[selected_mois]
                    
                    # Déterminer le numéro de terrain
                    if selected_terrain == "Tous les terrains":
                        numero_terrain = None
                    else:
                        numero_terrain = int(selected_terrain.split('n°')[1])
                    
                    success, msg = add_cotisation(participant_id, mois_num, annee, montant, paye, numero_terrain)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

st.divider()

cotisations = get_all_cotisations()

if cotisations.empty:
    st.info("Aucune cotisation enregistrée. Utilisez l'import Excel pour commencer.")
    st.stop()
    
# Sélection de l'année et recherche
col_year, col_search = st.columns([1, 2])

with col_year:
    years = sorted(cotisations['annee'].unique(), reverse=True)
    selected_year = st.selectbox("Année", years, key="cotis_year")

with col_search:
    search_cotis = st.text_input("🔍 Rechercher un participant", 
                                placeholder="Nom du participant...",
                                key="search_cotis_year")

# Filtrer par année
cotis_year = cotisations[cotisations['annee'] == selected_year]

# Filtrer par recherche si applicable
if search_cotis:
    mask = cotis_year['participant'].str.contains(search_cotis, case=False, na=False)
    cotis_year = cotis_year[mask]
    
    if cotis_year.empty:
        st.warning("Aucune cotisation ne correspond à votre recherche pour cette année")
        st.stop()

# Section pour marquer des cotisations comme payées
st.subheader("💳 Marquer des cotisations comme payées")

cotisations_impayees = cotis_year[cotis_year['paye'] == 0]

if cotisations_impayees.empty:
    st.info("Aucune cotisation impayée pour cette année")
else:
    st.write(f"**{len(cotisations_impayees)} cotisation(s) impayée(s)**")
    
    # Conteneur avec scroll
    with st.container(height=600):
        for idx, row in cotisations_impayees.iterrows():
                # Si ce n'est pas la cotisation en cours de paiement
                if st.session_state.paiement_cotisation_id != row['id']:
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                    with col1:
                        terrain_info = f" - Terrain n°{row['numero_terrain']}" if pd.notna(row['numero_terrain']) else " - Tous les terrains"
                        st.write(f"**{row['participant']}**{terrain_info}")
                    with col2:
                        mois_nom = MOIS_NOMS[row['mois']-1]
                        st.write(f"{mois_nom} {row['annee']}")
                    with col3:
                        st.write(f"{row['montant']:,.0f}".replace(',', ' ') + " FCFA")
                    with col4:
                        if st.button("✅ Payé", key=f"pay_{row['id']}", type="primary"):
                            st.session_state.paiement_cotisation_id = row['id']
                            st.rerun()
                    with col5:
                        if st.button("🗑️", key=f"del_cotis_{row['id']}", help="Supprimer"):
                            st.session_state.delete_cotisation_id = row['id']
                            st.rerun()
                    
                    # Confirmation de suppression
                    if st.session_state.delete_cotisation_id == row['id']:
                        st.warning(f"⚠️ **Confirmer la suppression de cette cotisation ?**")
                        terrain_info = f" - Terrain n°{row['numero_terrain']}" if pd.notna(row['numero_terrain']) else " - Tous les terrains"
                        st.write(f"{row['participant']}{terrain_info} - {mois_nom} {row['annee']} - {row['montant']:,.0f}".replace(',', ' ') + " FCFA")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✅ Confirmer la suppression", key=f"confirm_del_cotis_{row['id']}", type="primary"):
                                success, msg = delete_cotisation(row['id'])
                                if success:
                                    st.success(msg)
                                    st.session_state.delete_cotisation_id = None
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with col_cancel:
                            if st.button("❌ Annuler", key=f"cancel_del_cotis_{row['id']}"):
                                st.session_state.delete_cotisation_id = None
                                st.rerun()
                else:
                    # Afficher le formulaire de saisie du montant
                    terrain_info = f" - Terrain n°{row['numero_terrain']}" if pd.notna(row['numero_terrain']) else " - Tous les terrains"
                    st.info(f"💰 **Enregistrer le paiement de {row['participant']}**{terrain_info}")
                    mois_nom = MOIS_NOMS[row['mois']-1]
                    st.write(f"📅 {mois_nom} {row['annee']} - Montant prévu : {row['montant']:,.0f}".replace(',', ' ') + " FCFA")
                    
                    col_montant, col_confirm, col_cancel = st.columns([2, 1, 1])
                    with col_montant:
                        montant_paye = st.number_input(
                            "Montant payé (FCFA)", 
                            min_value=float(COTISATION_MIN), 
                            value=float(row['montant']),
                            step=100.0, 
                            format="%.0f",
                            key=f"montant_paye_{row['id']}"
                        )
                    with col_confirm:
                        st.write("")  # Espacement
                        if st.button("✅ Confirmer", key=f"confirm_pay_{row['id']}", type="primary"):
                            if update_cotisation_status(row['id'], True, montant_paye):
                                st.success("Cotisation marquée comme payée")
                                st.session_state.paiement_cotisation_id = None
                                st.rerun()
                    with col_cancel:
                        st.write("")  # Espacement
                        if st.button("❌ Annuler", key=f"cancel_pay_{row['id']}"):
                            st.session_state.paiement_cotisation_id = None
                            st.rerun()
                    
                    st.divider()

st.divider()

# Tableau annuel (participants x mois)
st.subheader(f"Générer le Rapport des cotisations ")

# Section pour générer des rapports PDF
with st.expander("📄 Générer un rapport PDF pour un participant", expanded=False):
    participants_df = get_all_participants()
    if not participants_df.empty:
        participants_dict = {f"{row['nom']} {row['prenom']}": row['id'] 
                           for _, row in participants_df.iterrows()}
        
        selected_participant_pdf = st.selectbox(
            "Sélectionner un participant", 
            options=list(participants_dict.keys()),
            key="participant_pdf"
        )
        
        if st.button("📥 Générer et télécharger le rapport PDF", type="primary"):
            participant_id = participants_dict[selected_participant_pdf]
            pdf_buffer = generer_rapport_participant(participant_id)
            
            if pdf_buffer:
                nom_fichier = selected_participant_pdf.replace(' ', '_')
                st.download_button(
                    label="📥 Télécharger le PDF",
                    data=pdf_buffer,
                    file_name=f"rapport_{nom_fichier}.pdf",
                    mime="application/pdf",
                    key="download_pdf_cotis"
                )
                st.success("✅ Rapport PDF généré avec succès !")
            else:
                st.error("❌ Erreur lors de la génération du rapport")
    else:
        st.info("Aucun participant disponible")
