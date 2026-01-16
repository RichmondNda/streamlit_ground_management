"""
Page Gestion des participants
"""

import streamlit as st
import sqlite3
import pandas as pd
from database import DB_NAME
from constants import PRIX_TERRAIN
from auth import require_authentication, show_logout_button
from generate_report_pdf import generer_rapport_participant
from historique import ajouter_historique

# Configuration de la page
st.set_page_config(
    page_title="Participants - MEDD",
    page_icon="👤",
    layout="wide"
)

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# REQUÊTES PARTICIPANTS
# ============================================================================

def get_all_participants():
    """Récupère tous les participants"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM participants ORDER BY nom, prenom", conn)
    conn.close()
    return df

def get_participant_stats(participant_id):
    """Récupère les statistiques d'un participant"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Somme totale des cotisations payées
    cursor.execute("""
        SELECT SUM(montant), COUNT(*) 
        FROM cotisations 
        WHERE participant_id = ? AND paye = 1
    """, (participant_id,))
    result = cursor.fetchone()
    total_paye = result[0] or 0
    nb_mensualites = result[1] or 0
    
    conn.close()
    return {
        'total_paye': total_paye,
        'nb_mensualites': nb_mensualites
    }

def add_participant(nom, prenom, nombre_terrains=0, telephone="", email=""):
    """Ajoute un nouveau participant"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO participants (nom, prenom, nombre_terrains, telephone, email) VALUES (?, ?, ?, ?, ?)",
            (nom, prenom, nombre_terrains, telephone, email)
        )
        participant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Enregistrer dans l'historique
        ajouter_historique(
            'CREATE',
            'participants',
            participant_id,
            f"Création du participant {nom} {prenom}",
            None,
            {'nom': nom, 'prenom': prenom, 'nombre_terrains': nombre_terrains, 'telephone': telephone, 'email': email}
        )
        
        return True, "Participant ajouté avec succès"
    except sqlite3.IntegrityError:
        return False, "Ce participant existe déjà"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def update_participant(participant_id, nom, prenom, nombre_terrains, telephone="", email=""):
    """Met à jour les informations d'un participant"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Récupérer les anciennes valeurs
        cursor.execute("SELECT nom, prenom, nombre_terrains, telephone, email FROM participants WHERE id = ?", (participant_id,))
        old_values = cursor.fetchone()
        
        cursor.execute(
            "UPDATE participants SET nom = ?, prenom = ?, nombre_terrains = ?, telephone = ?, email = ? WHERE id = ?",
            (nom, prenom, nombre_terrains, telephone, email, participant_id)
        )
        conn.commit()
        conn.close()
        
        # Enregistrer dans l'historique
        ajouter_historique(
            'UPDATE',
            'participants',
            participant_id,
            f"Modification du participant {nom} {prenom}",
            {'nom': old_values[0], 'prenom': old_values[1], 'nombre_terrains': old_values[2], 
             'telephone': old_values[3], 'email': old_values[4]},
            {'nom': nom, 'prenom': prenom, 'nombre_terrains': nombre_terrains, 
             'telephone': telephone, 'email': email}
        )
        
        return True, "Participant mis à jour avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def delete_participant(participant_id):
    """Supprime un participant et ses cotisations"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Récupérer les infos avant suppression
        cursor.execute("SELECT nom, prenom, nombre_terrains FROM participants WHERE id = ?", (participant_id,))
        participant_info = cursor.fetchone()
        
        cursor.execute("DELETE FROM cotisations WHERE participant_id = ?", (participant_id,))
        cursor.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
        conn.commit()
        conn.close()
        
        # Enregistrer dans l'historique
        if participant_info:
            ajouter_historique(
                'DELETE',
                'participants',
                participant_id,
                f"Suppression du participant {participant_info[0]} {participant_info[1]}",
                {'nom': participant_info[0], 'prenom': participant_info[1], 'nombre_terrains': participant_info[2]},
                None
            )
        
        return True, "Participant supprimé avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"


# ============================================================================
# PAGE PARTICIPANTS
# ============================================================================

st.title("Gestion des Participants")

# Initialiser session_state pour le mode édition et suppression
if 'edit_participant_id' not in st.session_state:
    st.session_state.edit_participant_id = None
if 'delete_participant_id' not in st.session_state:
    st.session_state.delete_participant_id = None
if 'view_details_participant_id' not in st.session_state:
    st.session_state.view_details_participant_id = None

# Formulaire d'ajout
with st.expander("➕ Ajouter un participant", expanded=False):
    with st.form("form_participant", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom *")
            nombre_terrains = st.number_input("Nombre de terrains", min_value=0, value=0, step=1)
            telephone = st.text_input("Téléphone", placeholder="06 12 34 56 78")
        with col2:
            prenom = st.text_input("Prénom *")
            email = st.text_input("Email", placeholder="exemple@email.com")
        
        submitted = st.form_submit_button("Ajouter")
        
        if submitted:
            if not nom or not prenom:
                st.error("Le nom et le prénom sont obligatoires")
            else:
                success, msg = add_participant(nom, prenom, nombre_terrains, telephone, email)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# Liste des participants
st.subheader("Liste des participants")
participants = get_all_participants()

if participants.empty:
    st.info("Aucun participant enregistré")
else:
    # Barre de recherche
    col_search, col_total = st.columns([3, 1])
    with col_search:
        search_term = st.text_input("🔍 Rechercher un participant (nom, prénom)", 
                                   placeholder="Tapez pour rechercher...",
                                   key="search_participant")
    
    # Filtrer les participants selon la recherche
    if search_term:
        mask = (
            participants['nom'].str.contains(search_term, case=False, na=False) |
            participants['prenom'].str.contains(search_term, case=False, na=False)
        )
        participants = participants[mask]
    
    with col_total:
        st.write(f"**{len(participants)} participant(s)**")
    
    if participants.empty:
        st.warning("Aucun participant ne correspond à votre recherche")
    else:
        # Affichage avec possibilité de modification et suppression
        for idx, row in participants.iterrows():
            # Mode édition pour ce participant
            if st.session_state.edit_participant_id == row['id']:
                with st.container():
                    st.write("✏️ **Mode édition**")
                    with st.form(f"form_edit_{row['id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_nom = st.text_input("Nom *", value=row['nom'])
                            edit_terrains = st.number_input("Nombre de terrains", min_value=0, value=int(row.get('nombre_terrains', 0)), step=1)
                            edit_telephone = st.text_input("Téléphone", value=row.get('telephone', '') or '', placeholder="06 12 34 56 78")
                        with col2:
                            edit_prenom = st.text_input("Prénom *", value=row['prenom'])
                            edit_email = st.text_input("Email", value=row.get('email', '') or '', placeholder="exemple@email.com")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_btn = st.form_submit_button("💾 Enregistrer", use_container_width=True)
                        with col_cancel:
                            cancel_btn = st.form_submit_button("❌ Annuler", use_container_width=True)
                        
                        if save_btn:
                            if not edit_nom or not edit_prenom:
                                st.error("Le nom et le prénom sont obligatoires")
                            else:
                                success, msg = update_participant(row['id'], edit_nom, edit_prenom, edit_terrains, edit_telephone, edit_email)
                                if success:
                                    st.success(msg)
                                    st.session_state.edit_participant_id = None
                                    st.rerun()
                                else:
                                    st.error(msg)
                        
                        if cancel_btn:
                            st.session_state.edit_participant_id = None
                            st.rerun()
                    st.divider()
            else:
                # Mode affichage normal
                with st.container():
                    nb_terrains = int(row.get('nombre_terrains', 0))
                    
                    # Définir le nombre de colonnes selon si le participant a des terrains
                    if nb_terrains > 0:
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 1.5, 1.5, 1, 0.7, 0.7, 0.7, 0.7])
                    else:
                        col1, col2, col3, col4, col5, col6 = st.columns([2, 1.5, 1.5, 1, 0.7, 0.7])
                    
                    with col1:
                        st.write(f"**{row['nom']} {row['prenom']}**")
                    with col2:
                        if row.get('telephone'):
                            st.write(f"📞 {row['telephone']}")
                    with col3:
                        if row.get('email'):
                            st.write(f"✉️ {row['email']}")
                    with col4:
                        st.write(f"🏠 {nb_terrains} terrain(s)")
                    with col5:
                        if nb_terrains > 0:
                            if st.button("💰", key=f"view_part_{row['id']}", help="Voir détails financiers"):
                                if st.session_state.view_details_participant_id == row['id']:
                                    st.session_state.view_details_participant_id = None
                                else:
                                    st.session_state.view_details_participant_id = row['id']
                                st.rerun()
                    with col6 if nb_terrains > 0 else col5:
                        if nb_terrains > 0:
                            # Bouton pour télécharger le rapport PDF
                            pdf_buffer = generer_rapport_participant(row['id'])
                            if pdf_buffer:
                                st.download_button(
                                    label="📄",
                                    data=pdf_buffer,
                                    file_name=f"rapport_{row['nom']}_{row['prenom']}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_{row['id']}",
                                    help="Télécharger le rapport PDF"
                                )
                    with col7 if nb_terrains > 0 else col5:
                        if st.button("✏️", key=f"edit_part_{row['id']}", help="Modifier"):
                            st.session_state.edit_participant_id = row['id']
                            st.rerun()
                    with col8 if nb_terrains > 0 else col6:
                        if st.button("🗑️", key=f"del_part_{row['id']}", help="Supprimer"):
                            st.session_state.delete_participant_id = row['id']
                            st.rerun()
                    
                    # Modal de confirmation de suppression
                    if st.session_state.delete_participant_id == row['id']:
                        st.warning(f"⚠️ **Confirmer la suppression de {row['nom']} {row['prenom']} ?**")
                        st.write("Cette action supprimera également toutes les cotisations associées.")
                        col_confirm, col_cancel = st.columns(2)
                        with col_confirm:
                            if st.button("✅ Confirmer la suppression", key=f"confirm_del_{row['id']}", type="primary"):
                                success, msg = delete_participant(row['id'])
                                if success:
                                    st.success(msg)
                                    st.session_state.delete_participant_id = None
                                    st.rerun()
                                else:
                                    st.error(msg)
                                    st.session_state.delete_participant_id = None
                        with col_cancel:
                            if st.button("❌ Annuler", key=f"cancel_del_{row['id']}"):
                                st.session_state.delete_participant_id = None
                                st.rerun()
                    
                    # Afficher les détails financiers si le bouton a été cliqué
                    if nb_terrains > 0 and st.session_state.view_details_participant_id == row['id']:
                        st.info(f"💰 **Détails financiers de {row['nom']} {row['prenom']}**")
                        stats = get_participant_stats(row['id'])
                        cout_total = nb_terrains * PRIX_TERRAIN
                        reste_a_payer = cout_total - stats['total_paye']
                        
                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric("Coût total", 
                                     f"{cout_total:,.0f}".replace(',', ' ') + " FCFA")
                        with col_b:
                            st.metric("Total payé", 
                                     f"{stats['total_paye']:,.0f}".replace(',', ' ') + " FCFA")
                        with col_c:
                            st.metric("Reste à payer", 
                                     f"{reste_a_payer:,.0f}".replace(',', ' ') + " FCFA")
                        with col_d:
                            st.metric("Mensualités payées", stats['nb_mensualites'])
                        
                        # Barre de progression
                        if cout_total > 0:
                            progression = (stats['total_paye'] / cout_total) * 100
                            st.progress(min(progression / 100, 1.0))
                            st.caption(f"Progression: {progression:.1f}%")
                    
                    st.divider()
