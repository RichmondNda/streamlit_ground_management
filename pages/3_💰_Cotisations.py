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

st.title("Liste des Cotisations")

# Initialiser session_state pour le paiement en cours
if 'paiement_cotisation_id' not in st.session_state:
    st.session_state.paiement_cotisation_id = None
if 'delete_cotisation_id' not in st.session_state:
    st.session_state.delete_cotisation_id = None


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
    
st.divider()

# Tableau annuel (participants x mois)
st.subheader(f"Tableau des cotisations {selected_year}")

mois_names = MOIS_NOMS

# Grouper par participant
for participant_name in sorted(cotis_year['participant'].unique()):
    cotis_participant = cotis_year[cotis_year['participant'] == participant_name]
    
    # Récupérer le nombre de terrains
    nb_terrains = cotis_participant['nombre_terrains'].iloc[0]
    
    # Afficher le nom du participant
    st.write(f"**{participant_name}** ({nb_terrains} terrain(s))")
    
    # Afficher par terrain
    for terrain_num in range(1, nb_terrains + 1):
        cotis_terrain = cotis_participant[cotis_participant['numero_terrain'] == terrain_num]
        
        # Si des cotisations existent pour ce terrain
        if not cotis_terrain.empty:
            st.write(f"  🏞️ Terrain n°{terrain_num}")
            
            cols = st.columns(12)
            for mois_num in range(1, 13):
                cotis_mois = cotis_terrain[cotis_terrain['mois'] == mois_num]
                
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
                        st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.75em;'>{mois_names[mois_num - 1][:3]}</p>", unsafe_allow_html=True)
    
    # Ligne de total par mois pour ce participant
    st.write(f"  💰 **Total**")
    cols_total = st.columns(12)
    for mois_num in range(1, 13):
        # Calculer le total pour ce mois (tous terrains confondus)
        cotis_mois_all = cotis_participant[cotis_participant['mois'] == mois_num]
        
        with cols_total[mois_num - 1]:
            if not cotis_mois_all.empty:
                total_montant = cotis_mois_all['montant'].sum()
                total_paye = cotis_mois_all[cotis_mois_all['paye'] == 1]['montant'].sum()
                nb_cotis = len(cotis_mois_all)
                nb_payees = len(cotis_mois_all[cotis_mois_all['paye'] == 1])
                
                # Afficher le total avec indication du statut
                total_format = f"{total_montant:,.0f}".replace(',', ' ')
                if nb_payees == nb_cotis:
                    # Tout est payé
                    st.markdown(f"<div style='background-color: #d4edda; padding: 5px; border-radius: 5px; text-align: center;'>"
                              f"<strong>{total_format}</strong><br/>"
                              f"<small style='color: #155724;'>✓ {nb_cotis}/{nb_cotis}</small></div>", 
                              unsafe_allow_html=True)
                elif nb_payees == 0:
                    # Rien n'est payé
                    st.markdown(f"<div style='background-color: #f8d7da; padding: 5px; border-radius: 5px; text-align: center;'>"
                              f"<strong>{total_format}</strong><br/>"
                              f"<small style='color: #721c24;'>✗ 0/{nb_cotis}</small></div>", 
                              unsafe_allow_html=True)
                else:
                    # Partiellement payé
                    paye_format = f"{total_paye:,.0f}".replace(',', ' ')
                    st.markdown(f"<div style='background-color: #fff3cd; padding: 5px; border-radius: 5px; text-align: center;'>"
                              f"<strong>{total_format}</strong><br/>"
                              f"<small style='color: #856404;'>⚠ {nb_payees}/{nb_cotis}<br/>{paye_format} payé</small></div>", 
                              unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.75em;'>-</p>", unsafe_allow_html=True)
    
    # Afficher aussi les cotisations sans numéro de terrain (anciennes)
    cotis_sans_terrain = cotis_participant[cotis_participant['numero_terrain'].isna()]
    if not cotis_sans_terrain.empty:
        st.write(f"  📊 Cotisations globales (ancien format)")
        
        cols = st.columns(12)
        for mois_num in range(1, 13):
            cotis_mois = cotis_sans_terrain[cotis_sans_terrain['mois'] == mois_num]
            
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
                    st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.75em;'>{mois_names[mois_num - 1][:3]}</p>", unsafe_allow_html=True)
    
    st.divider()
