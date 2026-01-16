"""
Application Streamlit - Gestion de Cotisations MEDD
Page d'accueil
"""

import streamlit as st
import os
from database import init_database, DB_NAME
from backup_db import backup_database
from auth import require_authentication, show_logout_button

# Configuration de la page
st.set_page_config(
    page_title="Gestion Cotisations MEDD",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    /* Amélioration du titre principal */
    h1 {
        color: #fc6b03;
        font-size: 3rem !important;
        font-weight: 700 !important;
        padding-bottom: 1rem;
        border-bottom: 3px solid #fc6b03;
        margin-bottom: 2rem;
    }
    
    /* Amélioration des sous-titres */
    h2, h3 {
        color: #fc6b03;
        font-weight: 600 !important;
        margin-top: 1.5rem !important;
    }
    
    /* Style des liens et éléments markdown */
    a {
        color: #fc6b03;
        text-decoration: none;
    }
    
    a:hover {
        color: #e35f02;
        text-decoration: underline;
    }
    
    /* Style des listes */
    ul li {
        margin-bottom: 0.5rem;
        line-height: 1.6;
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
    
    /* Messages d'info dans la sidebar */
    .stSidebar .stInfo {
        background-color: #fff3e0;
        border-left: 4px solid #fc6b03;
        border-radius: 8px;
    }
    
    /* Amélioration du conteneur principal */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Style des dividers */
    hr {
        border-color: #fc6b03;
        margin: 2rem 0;
    }
    
    /* Effet de carte pour les sections */
    .stMarkdown {
        line-height: 1.8;
    }
    
    /* Style des code blocks */
    code {
        background-color: #f5f5f5;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        color: #fc6b03;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# Initialiser la base de données
init_database()

# Backup automatique au démarrage (une fois par session)
if 'backup_done' not in st.session_state:
    if os.path.exists(DB_NAME):
        backup_database()
    st.session_state.backup_done = True

# ================================================================================
# PAGE D'ACCUEIL
# ================================================================================

st.title("💰 Gestion de Cotisations MEDD")

st.markdown("""
## 👋 Bienvenue dans l'application de gestion des cotisations

Cette application vous permet de :

- 📊 **Tableau de bord** : Visualiser les statistiques et indicateurs clés
- 👤 **Participants** : Gérer la liste des participants et leurs terrains
- 💰 **Cotisations** : Consulter et modifier l'état des paiements
- 📥 **Import Excel** : Importer des données depuis un fichier Excel
- 📤 **Export Excel** : Exporter les données vers Excel
- 📱 **Relances WhatsApp** : Générer des messages de relance

### 🚀 Pour commencer

Utilisez le menu de navigation dans la barre latérale pour accéder aux différentes fonctionnalités.

### 📌 Informations système

- **Version** : 2.3
- **Fonctionnalités disponibles** :
  - ✅ Suivi multi-terrains par participant
  - ✅ Gestion des cotisations mensuelles avec montants personnalisables
  - ✅ Import/Export Excel avancé
  - ✅ Statistiques détaillées et rapports PDF
  - ✅ Backup automatique de la base de données
  - ✅ Navigation rapide par URL
  - ✅ Historique des modifications
  
### 💡 Astuces d'utilisation

- **Accès rapide** : Utilisez les URLs directes pour naviguer :
  - `/Dashboard` : Tableau de bord global
  - `/Participants` : Gestion des participants
  - `/Cotisations` : Suivi des paiements
  - `/Import_Excel` : Import de données
  - `/Export_Excel` : Export de données

- **Sécurité** : Les modifications sont sauvegardées automatiquement
- **Backup** : Un backup est créé à chaque démarrage de l'application
- **Support multi-terrains** : Gérez plusieurs terrains par participant avec des cotisations individuelles
""")

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.info("👈 **Utilisez le menu ci-dessus pour naviguer**")
    
    st.markdown("### 📊 Statistiques rapides")
    
    # Ajouter quelques statistiques si la base existe
    import sqlite3
    if os.path.exists(DB_NAME):
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Nombre de participants
            cursor.execute("SELECT COUNT(*) FROM participants")
            nb_participants = cursor.fetchone()[0]
            st.metric("👥 Participants", nb_participants)
            
            # Nombre de cotisations impayées
            cursor.execute("SELECT COUNT(*) FROM cotisations WHERE paye = 0")
            nb_impayees = cursor.fetchone()[0]
            st.metric("⚠️ Cotisations impayées", nb_impayees)
            
            conn.close()
        except:
            pass
    
    st.markdown("---")
    st.caption("💻 Développé avec ❤️ en Python & Streamlit")
    st.caption("🎨 Design optimisé pour une meilleure expérience")
