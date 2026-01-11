"""
Page Cotisations
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from database import DB_NAME
from constants import MOIS_NOMS, COTISATION_MIN, COTISATION_PAR_TERRAIN

# ============================================================================
# REQUÊTES COTISATIONS
# ============================================================================

def get_all_participants():
    """Récupère tous les participants"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT id, nom, prenom FROM participants ORDER BY nom, prenom"
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
            c.mois,
            c.annee,
            c.montant,
            c.paye,
            c.date_paiement
        FROM cotisations c
        JOIN participants p ON c.participant_id = p.id
        ORDER BY c.annee DESC, c.mois DESC, p.nom, p.prenom
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_cotisation(participant_id, mois, annee, montant, paye=False):
    """Ajoute une nouvelle cotisation"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        date_paiement = datetime.now().strftime("%Y-%m-%d") if paye else None
        cursor.execute(
            "INSERT INTO cotisations (participant_id, mois, annee, montant, paye, date_paiement) VALUES (?, ?, ?, ?, ?, ?)",
            (participant_id, mois, annee, montant, 1 if paye else 0, date_paiement)
        )
        conn.commit()
        conn.close()
        return True, "Cotisation ajoutée avec succès"
    except sqlite3.IntegrityError:
        return False, "Cette cotisation existe déjà pour ce participant"
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
        conn.close()
        return True
    except Exception as e:
        return False


def delete_cotisation(cotisation_id):
    """Supprime une cotisation"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cotisations WHERE id = ?", (cotisation_id,))
        conn.commit()
        conn.close()
        return True, "Cotisation supprimée avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"


def generer_cotisations_mensuelles(mois, annee):
    """Génère les cotisations impayées pour tous les participants pour un mois donné"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Récupérer tous les participants avec leur nombre de terrains
        cursor.execute("SELECT id, nom, prenom, nombre_terrains FROM participants WHERE nombre_terrains > 0")
        participants = cursor.fetchall()
        
        nb_ajoutes = 0
        nb_existent = 0
        
        for participant_id, nom, prenom, nb_terrains in participants:
            # Vérifier si la cotisation existe déjà
            cursor.execute(
                "SELECT id FROM cotisations WHERE participant_id = ? AND mois = ? AND annee = ?",
                (participant_id, mois, annee)
            )
            
            if cursor.fetchone() is None:
                # Calculer le montant basé sur le nombre de terrains
                montant = nb_terrains * COTISATION_PAR_TERRAIN
                
                # Créer la cotisation impayée
                cursor.execute(
                    "INSERT INTO cotisations (participant_id, mois, annee, montant, paye) VALUES (?, ?, ?, ?, 0)",
                    (participant_id, mois, annee, montant)
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

st.title("Cotisations")

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

# Formulaire d'ajout de cotisation
with st.expander("➕ Ajouter une cotisation", expanded=False):
    participants_df = get_all_participants()
    
    if participants_df.empty:
        st.warning("Aucun participant enregistré. Veuillez d'abord ajouter des participants.")
    else:
        with st.form("form_cotisation", clear_on_submit=True):
            # Créer un dictionnaire pour le selectbox
            participants_dict = {f"{row['nom']} {row['prenom']}": row['id'] 
                               for _, row in participants_df.iterrows()}
            
            col1, col2 = st.columns(2)
            with col1:
                selected_participant = st.selectbox("Participant *", options=list(participants_dict.keys()))
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
                participant_id = participants_dict[selected_participant]
                mois_num = mois_dict[selected_mois]
                
                success, msg = add_cotisation(participant_id, mois_num, annee, montant, paye)
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
with st.expander("💳 Marquer des cotisations comme payées", expanded=False):
    cotisations_impayees = cotis_year[cotis_year['paye'] == 0]
    
    if cotisations_impayees.empty:
        st.info("Aucune cotisation impayée pour cette année")
    else:
        st.write(f"**{len(cotisations_impayees)} cotisation(s) impayée(s)**")
        
        for idx, row in cotisations_impayees.iterrows():
            # Si ce n'est pas la cotisation en cours de paiement
            if st.session_state.paiement_cotisation_id != row['id']:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                with col1:
                    st.write(f"**{row['participant']}**")
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
                    st.write(f"{row['participant']} - {mois_nom} {row['annee']} - {row['montant']:,.0f}".replace(',', ' ') + " FCFA")
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
                st.info(f"💰 **Enregistrer le paiement de {row['participant']}**")
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
st.subheader(f"Tableau des cotisations {selected_year}")

mois_names = MOIS_NOMS

participants_year = sorted(cotis_year['participant'].unique())

for participant_name in participants_year:
    st.write(f"**{participant_name}**")
    
    cotis_participant = cotis_year[cotis_year['participant'] == participant_name]
    
    cols = st.columns(12)
    for mois_num in range(1, 13):
        cotis_mois = cotis_participant[cotis_participant['mois'] == mois_num]
        
        with cols[mois_num - 1]:
            if not cotis_mois.empty:
                cotis_row = cotis_mois.iloc[0]
                paye = cotis_row['paye']
                cotis_id = cotis_row['id']
                montant = cotis_row['montant']
                
                # Bouton avec couleur selon statut
                if paye:
                    montant_format = f"{montant:,.0f}".replace(',', ' ')
                    button_label = f"✓\n{montant_format}"
                    button_type = "primary"
                else:
                    montant_format = f"{montant:,.0f}".replace(',', ' ')
                    button_label = f"✗\n{montant_format}"
                    button_type = "secondary"
                
                if st.button(button_label, key=f"cotis_{cotis_id}", 
                           type=button_type, use_container_width=True):
                    # Toggle le statut
                    update_cotisation_status(cotis_id, not paye)
                    st.rerun()
            else:
                st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.85em;'>{mois_names[mois_num - 1]}</p>", unsafe_allow_html=True)
    
    st.divider()
