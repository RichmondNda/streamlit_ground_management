"""
Page Tableau de bord
"""

import streamlit as st
import sqlite3
import pandas as pd
from database import DB_NAME
from constants import MOIS_NOMS, PRIX_TERRAIN
from auth import require_authentication, show_logout_button

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# REQUÊTES STATISTIQUES
# ============================================================================

def get_dashboard_stats(annee=None):
    """Calcule les statistiques pour le tableau de bord"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Nombre total de participants
    cursor.execute("SELECT COUNT(*) FROM participants")
    nb_participants = cursor.fetchone()[0]
    
    # Nombre total de terrains
    cursor.execute("SELECT SUM(nombre_terrains) FROM participants")
    total_terrains = cursor.fetchone()[0] or 0
    
    # Total des cotisations encaissées
    if annee:
        cursor.execute("SELECT SUM(montant) FROM cotisations WHERE paye = 1 AND annee = ?", (annee,))
    else:
        cursor.execute("SELECT SUM(montant) FROM cotisations WHERE paye = 1")
    total_encaisse = cursor.fetchone()[0] or 0
    
    # Cotisations impayées
    if annee:
        cursor.execute("SELECT COUNT(*), SUM(montant) FROM cotisations WHERE paye = 0 AND annee = ?", (annee,))
    else:
        cursor.execute("SELECT COUNT(*), SUM(montant) FROM cotisations WHERE paye = 0")
    result = cursor.fetchone()
    nb_impayees = result[0] or 0
    montant_impaye = result[1] or 0
    
    conn.close()
    
    # Calcul du montant total attendu
    montant_total_attendu = total_terrains * PRIX_TERRAIN
    
    return {
        'nb_participants': nb_participants,
        'total_terrains': total_terrains,
        'montant_total_attendu': montant_total_attendu,
        'total_encaisse': total_encaisse,
        'nb_impayees': nb_impayees,
        'montant_impaye': montant_impaye
    }

def get_available_years():
    """Récupère la liste des années disponibles dans les cotisations"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT annee FROM cotisations ORDER BY annee DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    return years

# Configuration de la page
st.set_page_config(
    page_title="Dashboard - MEDD",
    page_icon="📊",
    layout="wide"
)

st.title("Tableau de Bord")

# Filtres
years = get_available_years()
col1, col2 = st.columns([1, 3])
with col1:
    annee_filter = st.selectbox(
        "Filtrer par année",
        ["Toutes les années"] + years,
        key="dashboard_year_filter"
    )

annee = None if annee_filter == "Toutes les années" else annee_filter

# Récupération des stats
stats = get_dashboard_stats(annee)

# Section Vue d'ensemble
st.subheader("📊 Vue d'ensemble")

# Première ligne de métriques
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👥 Participants", stats['nb_participants'])

with col2:
    st.metric("🏠 Terrains total", stats['total_terrains'])

with col3:
    st.metric("💰 Montant total attendu", 
              f"{stats['montant_total_attendu']:,.0f}".replace(',', ' ') + " FCFA")

with col4:
    st.metric("✅ Total encaissé", 
              f"{stats['total_encaisse']:,.0f}".replace(',', ' ') + " FCFA")

# Deuxième ligne : Progression et reste
st.divider()

col_prog, col_reste = st.columns([3, 1])

with col_prog:
    if stats['montant_total_attendu'] > 0:
        progression = (stats['total_encaisse'] / stats['montant_total_attendu']) * 100
        st.metric("📈 Progression globale", f"{progression:.1f}%")
        st.progress(min(progression / 100, 1.0))
        reste_total = stats['montant_total_attendu'] - stats['total_encaisse']
        st.caption(f"Reste à encaisser : {reste_total:,.0f}".replace(',', ' ') + " FCFA")

with col_reste:
    st.metric("⏳ Cotisations impayées", stats['nb_impayees'])
    if stats['montant_impaye'] > 0:
        st.caption(f"{stats['montant_impaye']:,.0f}".replace(',', ' ') + " FCFA")

st.divider()

st.divider()

# Graphique récapitulatif par mois si une année est sélectionnée
if annee:
    st.subheader(f"📅 Évolution des cotisations pour {annee}")
    
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT mois, 
               SUM(CASE WHEN paye = 1 THEN montant ELSE 0 END) as paye,
               SUM(CASE WHEN paye = 0 THEN montant ELSE 0 END) as impaye
        FROM cotisations
        WHERE annee = ?
        GROUP BY mois
        ORDER BY mois
    """
    df = pd.read_sql_query(query, conn, params=(annee,))
    conn.close()
    
    if not df.empty:
        df['mois_nom'] = df['mois'].apply(lambda x: MOIS_NOMS[x-1] if 1 <= x <= 12 else str(x))
        
        chart_data = df.set_index('mois_nom')[['paye', 'impaye']]
        chart_data.columns = ['Payées', 'Impayées']
        st.bar_chart(chart_data)
        
        # Tableau récapitulatif
        with st.expander("📋 Détails par mois"):
            df_display = df.copy()
            df_display['Total'] = df_display['paye'] + df_display['impaye']
            df_display['paye'] = df_display['paye'].apply(lambda x: f"{x:,.0f}".replace(',', ' ') + " FCFA")
            df_display['impaye'] = df_display['impaye'].apply(lambda x: f"{x:,.0f}".replace(',', ' ') + " FCFA")
            df_display['Total'] = df_display['Total'].apply(lambda x: f"{x:,.0f}".replace(',', ' ') + " FCFA")
            df_display = df_display[['mois_nom', 'paye', 'impaye', 'Total']]
            df_display.columns = ['Mois', 'Payées', 'Impayées', 'Total']
            st.dataframe(df_display, hide_index=True, use_container_width=True)
else:
    st.subheader("📅 Évolution des cotisations")
    st.info("Sélectionnez une année pour voir l'évolution mensuelle des cotisations")
