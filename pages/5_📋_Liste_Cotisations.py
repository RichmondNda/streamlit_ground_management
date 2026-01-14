"""
Page Liste et Visualisation des Cotisations
"""

import streamlit as st
import sqlite3
import pandas as pd
from database import DB_NAME
from constants import MOIS_NOMS
from auth import require_authentication, show_logout_button

# Configuration de la page
st.set_page_config(
    page_title="Liste Cotisations - MEDD",
    page_icon="📋",
    layout="wide"
)

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# REQUÊTES
# ============================================================================

def get_cotisations_detaillees(annee=None, statut=None, participant_id=None):
    """Récupère les cotisations avec filtres"""
    conn = sqlite3.connect(DB_NAME)
    
    query = """
        SELECT 
            c.id,
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
        WHERE 1=1
    """
    
    params = []
    
    if annee:
        query += " AND c.annee = ?"
        params.append(annee)
    
    if statut == "Payées":
        query += " AND c.paye = 1"
    elif statut == "Impayées":
        query += " AND c.paye = 0"
    
    if participant_id:
        query += " AND p.id = ?"
        params.append(participant_id)
    
    query += " ORDER BY c.annee DESC, c.mois DESC, p.nom, p.prenom, c.numero_terrain"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_all_participants_with_id():
    """Récupère tous les participants avec leur ID"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, nom, prenom FROM participants ORDER BY nom, prenom", conn)
    conn.close()
    return df


def get_stats_cotisations(df):
    """Calcule les statistiques sur les cotisations"""
    if df.empty:
        return None
    
    total_cotisations = len(df)
    nb_payees = len(df[df['paye'] == 1])
    nb_impayees = len(df[df['paye'] == 0])
    montant_total = df['montant'].sum()
    montant_paye = df[df['paye'] == 1]['montant'].sum()
    montant_impaye = df[df['paye'] == 0]['montant'].sum()
    
    return {
        'total_cotisations': total_cotisations,
        'nb_payees': nb_payees,
        'nb_impayees': nb_impayees,
        'montant_total': montant_total,
        'montant_paye': montant_paye,
        'montant_impaye': montant_impaye
    }


# ============================================================================
# INTERFACE
# ============================================================================

st.title("📋 Liste et Visualisation des Cotisations")

# Filtres
st.subheader("🔍 Filtres")

col1, col2, col3 = st.columns(3)

with col1:
    # Filtre par année
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT annee FROM cotisations ORDER BY annee DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    year_options = ["Toutes"] + years
    selected_year = st.selectbox("Année", year_options)

with col2:
    # Filtre par statut
    statut_options = ["Toutes", "Payées", "Impayées"]
    selected_statut = st.selectbox("Statut", statut_options)

with col3:
    # Filtre par participant
    participants = get_all_participants_with_id()
    if not participants.empty:
        participant_options = ["Tous"] + [f"{row['nom']} {row['prenom']}" for _, row in participants.iterrows()]
        selected_participant = st.selectbox("Participant", participant_options)
        
        # Récupérer l'ID du participant sélectionné
        participant_id = None
        if selected_participant != "Tous":
            for _, row in participants.iterrows():
                if f"{row['nom']} {row['prenom']}" == selected_participant:
                    participant_id = row['id']
                    break
    else:
        st.warning("Aucun participant")
        participant_id = None

st.divider()

# Récupération des données
annee_filter = None if selected_year == "Toutes" else selected_year
statut_filter = None if selected_statut == "Toutes" else selected_statut

cotisations = get_cotisations_detaillees(annee_filter, statut_filter, participant_id)

if cotisations.empty:
    st.info("Aucune cotisation trouvée avec ces filtres")
else:
    # Statistiques
    stats = get_stats_cotisations(cotisations)
    
    st.subheader("📊 Statistiques")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total cotisations", stats['total_cotisations'])
    with col2:
        st.metric("Payées", stats['nb_payees'], 
                 delta=f"{(stats['nb_payees']/stats['total_cotisations']*100):.0f}%")
    with col3:
        st.metric("Impayées", stats['nb_impayees'],
                 delta=f"{(stats['nb_impayees']/stats['total_cotisations']*100):.0f}%",
                 delta_color="inverse")
    with col4:
        st.metric("Montant total", f"{stats['montant_total']:,.0f}".replace(',', ' ') + " FCFA")
    
    col5, col6 = st.columns(2)
    with col5:
        st.metric("💰 Montant encaissé", f"{stats['montant_paye']:,.0f}".replace(',', ' ') + " FCFA")
    with col6:
        st.metric("⏳ Montant impayé", f"{stats['montant_impaye']:,.0f}".replace(',', ' ') + " FCFA")
    
    st.divider()
    
    # Liste des cotisations
    st.subheader("📝 Liste détaillée")
    
    # Préparer le dataframe pour l'affichage
    df_display = cotisations.copy()
    df_display['Mois'] = df_display['mois'].apply(lambda x: MOIS_NOMS[x-1] if 1 <= x <= 12 else str(x))
    df_display['Statut'] = df_display['paye'].apply(lambda x: "✅ Payée" if x == 1 else "⏳ Impayée")
    df_display['Montant'] = df_display['montant'].apply(lambda x: f"{x:,.0f}".replace(',', ' ') + " FCFA")
    df_display['Terrain'] = df_display['numero_terrain'].apply(lambda x: f"n°{int(x)}" if pd.notna(x) else "Tous")
    
    # Colonnes à afficher
    df_display = df_display[['nom', 'prenom', 'nombre_terrains', 'Terrain', 'annee', 'Mois', 'Montant', 'Statut', 'date_paiement']]
    df_display.columns = ['Nom', 'Prénom', 'Nb Terrains', 'Terrain', 'Année', 'Mois', 'Montant', 'Statut', 'Date paiement']
    
    # Afficher le tableau avec alternance de couleurs
    st.dataframe(
        df_display,
        use_container_width=True,
        height=500,
        hide_index=True
    )
    
    # Option d'export CSV
    st.divider()
    col_export1, col_export2 = st.columns([1, 3])
    with col_export1:
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name=f"cotisations_{selected_year if selected_year != 'Toutes' else 'toutes'}.csv",
            mime="text/csv",
            use_container_width=True
        )
