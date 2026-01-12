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

st.title("Gestion de Cotisations MEDD")

st.markdown("""
## Bienvenue dans l'application de gestion des cotisations

Cette application vous permet de :

- 📊 **Tableau de bord** : Visualiser les statistiques et indicateurs clés
- 👤 **Participants** : Gérer la liste des participants
- 💰 **Cotisations** : Consulter et modifier l'état des paiements
- 📥 **Import Excel** : Importer des données depuis un fichier Excel
- 📤 **Export Excel** : Exporter les données vers Excel

### 🚀 Pour commencer

Utilisez le menu de navigation dans la barre latérale pour accéder aux différentes fonctionnalités.

### 📌 Informations

- **Version** : 2.3
- **Fonctionnalités** :
  - ✅ Suivi des participants
  - ✅ Gestion des cotisations mensuelles
  - ✅ Import/Export Excel
  - ✅ Statistiques détaillées
  - ✅ Backup automatique
  - ✅ Navigation par URL
  
### 💡 Astuces

- Utilisez les URLs directes pour accéder rapidement aux pages :
  - `/Dashboard` : Tableau de bord
  - `/Participants` : Liste des participants
  - `/Cotisations` : Gestion des cotisations
  - `/Import_Excel` : Import de données
  - `/Export_Excel` : Export de données

- Les modifications sont sauvegardées automatiquement
- Un backup est créé à chaque démarrage de l'application
""")

# Sidebar
with st.sidebar:
    st.markdown("---")
    st.info("👈 Utilisez le menu ci-dessus pour naviguer")
    
    st.markdown("---")
    st.caption("Développé avec ❤️ en Python & Streamlit")
