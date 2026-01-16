"""
Page Dashboard - Vue d'ensemble et indicateurs clés
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from database import DB_NAME, init_database
from constants import PRIX_TERRAIN, COTISATION_PAR_TERRAIN, MOIS_NOMS
from auth import require_authentication, show_logout_button
import plotly.graph_objects as go
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="Dashboard - MEDD",
    page_icon="📊",
    layout="wide"
)

# Initialiser la base de données
init_database()

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# FONCTIONS DE RÉCUPÉRATION DES DONNÉES
# ============================================================================

@st.cache_data(ttl=60)  # Cache de 60 secondes
def get_kpi_data():
    """Récupère les indicateurs clés de performance"""
    conn = sqlite3.connect(DB_NAME)
    
    # Total participants
    total_participants = pd.read_sql_query(
        "SELECT COUNT(*) as count FROM participants", 
        conn
    ).iloc[0]['count']
    
    # Total terrains
    total_terrains = pd.read_sql_query(
        "SELECT SUM(nombre_terrains) as count FROM participants", 
        conn
    ).iloc[0]['count'] or 0
    
    # Cotisations
    cotisations_df = pd.read_sql_query("""
        SELECT 
            montant,
            paye,
            annee,
            mois,
            date_paiement
        FROM cotisations
    """, conn)
    
    conn.close()
    
    # Calculs
    total_attendu = cotisations_df['montant'].sum()
    total_encaisse = cotisations_df[cotisations_df['paye'] == 1]['montant'].sum()
    reste_a_payer = total_attendu - total_encaisse
    
    nb_cotisations_total = len(cotisations_df)
    nb_cotisations_payees = len(cotisations_df[cotisations_df['paye'] == 1])
    nb_cotisations_impayees = nb_cotisations_total - nb_cotisations_payees
    
    taux_recouvrement = (total_encaisse / total_attendu * 100) if total_attendu > 0 else 0
    
    return {
        'total_participants': total_participants,
        'total_terrains': total_terrains,
        'total_attendu': total_attendu,
        'total_encaisse': total_encaisse,
        'reste_a_payer': reste_a_payer,
        'taux_recouvrement': taux_recouvrement,
        'nb_cotisations_total': nb_cotisations_total,
        'nb_cotisations_payees': nb_cotisations_payees,
        'nb_cotisations_impayees': nb_cotisations_impayees,
        'cotisations_df': cotisations_df
    }

@st.cache_data(ttl=60)
def get_evolution_paiements():
    """Récupère l'évolution des paiements par mois"""
    conn = sqlite3.connect(DB_NAME)
    
    df = pd.read_sql_query("""
        SELECT 
            annee,
            mois,
            SUM(montant) as montant_total,
            SUM(CASE WHEN paye = 1 THEN montant ELSE 0 END) as montant_paye
        FROM cotisations
        GROUP BY annee, mois
        ORDER BY annee, mois
    """, conn)
    
    conn.close()
    return df


# ============================================================================
# PAGE DASHBOARD
# ============================================================================

st.title("📊 Dashboard - Vue d'ensemble détaillée")

# Récupérer les données
data = get_kpi_data()

# ============================================================================
# INDICATEURS CLÉS
# ============================================================================

st.subheader("📈 Indicateurs clés de performance")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "👥 Participants", 
        data['total_participants'],
        help="Nombre total de participants enregistrés"
    )
    st.metric(
        "🏞️ Terrains", 
        int(data['total_terrains']),
        help="Nombre total de terrains"
    )

with col2:
    st.metric(
        "💰 Total attendu", 
        f"{data['total_attendu']:,.0f}".replace(',', ' ') + " FCFA",
        help="Montant total de toutes les cotisations"
    )
    st.metric(
        "📊 Cotisations", 
        data['nb_cotisations_total'],
        help="Nombre total de cotisations créées"
    )

with col3:
    st.metric(
        "✅ Total encaissé", 
        f"{data['total_encaisse']:,.0f}".replace(',', ' ') + " FCFA",
        delta=f"{data['taux_recouvrement']:.1f}%",
        delta_color="normal",
        help="Montant total des cotisations payées"
    )
    st.metric(
        "✓ Payées", 
        data['nb_cotisations_payees'],
        delta=f"{(data['nb_cotisations_payees']/data['nb_cotisations_total']*100) if data['nb_cotisations_total'] > 0 else 0:.0f}%",
        help="Nombre de cotisations payées"
    )

with col4:
    st.metric(
        "⏳ Reste à payer", 
        f"{data['reste_a_payer']:,.0f}".replace(',', ' ') + " FCFA",
        delta=f"-{100-data['taux_recouvrement']:.1f}%",
        delta_color="inverse",
        help="Montant restant à encaisser"
    )
    st.metric(
        "✗ Impayées", 
        data['nb_cotisations_impayees'],
        delta=f"{(data['nb_cotisations_impayees']/data['nb_cotisations_total']*100) if data['nb_cotisations_total'] > 0 else 0:.0f}%",
        delta_color="inverse",
        help="Nombre de cotisations impayées"
    )

st.divider()

# ============================================================================
# GRAPHIQUES
# ============================================================================

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 Répartition des cotisations")
    
    # Graphique en camembert
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Payées', 'Impayées'],
        values=[data['nb_cotisations_payees'], data['nb_cotisations_impayees']],
        hole=0.4,
        marker=dict(colors=['#28a745', '#dc3545']),
        textinfo='label+percent',
        textfont=dict(size=14)
    )])
    
    fig_pie.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("💵 Montants financiers")
    
    # Graphique en barres
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        name='Encaissé',
        x=['Montants'],
        y=[data['total_encaisse']],
        marker_color='#28a745',
        text=[f"{data['total_encaisse']:,.0f}".replace(',', ' ') + " FCFA"],
        textposition='inside'
    ))
    
    fig_bar.add_trace(go.Bar(
        name='Reste à payer',
        x=['Montants'],
        y=[data['reste_a_payer']],
        marker_color='#dc3545',
        text=[f"{data['reste_a_payer']:,.0f}".replace(',', ' ') + " FCFA"],
        textposition='inside'
    ))
    
    fig_bar.update_layout(
        height=350,
        barmode='stack',
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        yaxis_title="Montant (FCFA)"
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ============================================================================
# ÉVOLUTION TEMPORELLE
# ============================================================================

st.subheader("📈 Évolution des paiements par mois")

evolution_df = get_evolution_paiements()

if not evolution_df.empty:
    # Créer une colonne période pour l'affichage
    evolution_df['periode'] = evolution_df.apply(
        lambda row: f"{MOIS_NOMS[int(row['mois'])-1][:3]} {int(row['annee'])}", 
        axis=1
    )
    
    fig_evolution = go.Figure()
    
    fig_evolution.add_trace(go.Scatter(
        x=evolution_df['periode'],
        y=evolution_df['montant_paye'],
        mode='lines+markers',
        name='Montant payé',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(40, 167, 69, 0.2)'
    ))
    
    fig_evolution.add_trace(go.Scatter(
        x=evolution_df['periode'],
        y=evolution_df['montant_total'],
        mode='lines+markers',
        name='Montant attendu',
        line=dict(color='#007bff', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    fig_evolution.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Période",
        yaxis_title="Montant (FCFA)",
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_evolution, use_container_width=True)
else:
    st.info("Aucune donnée d'évolution disponible")

st.divider()
