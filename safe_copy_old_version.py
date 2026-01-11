"""
Application Streamlit - Gestion de Cotisations Mensuelles
Développé avec Python et SQLite
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

# Configuration de la page
st.set_page_config(
    page_title="Gestion Cotisations",
    page_icon="💰",
    layout="wide"
)

# ============================================================================
# GESTION DE LA BASE DE DONNÉES
# ============================================================================

def init_database():
    """Initialise la base de données SQLite avec les tables nécessaires"""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Table participants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            telephone TEXT,
            email TEXT,
            date_inscription TEXT NOT NULL,
            nombre_terrains INTEGER DEFAULT 0,
            UNIQUE(nom, prenom)
        )
    ''')
    
    # Ajouter la colonne nombre_terrains si elle n'existe pas (migration)
    cursor.execute("PRAGMA table_info(participants)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'nombre_terrains' not in columns:
        cursor.execute("ALTER TABLE participants ADD COLUMN nombre_terrains INTEGER DEFAULT 0")
    
    # Table cotisations
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cotisations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER NOT NULL,
            mois INTEGER NOT NULL,
            annee INTEGER NOT NULL,
            montant REAL NOT NULL,
            paye INTEGER NOT NULL DEFAULT 0,
            date_paiement TEXT,
            FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
            UNIQUE(participant_id, mois, annee)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    """Retourne une connexion à la base de données"""
    return sqlite3.connect('database.db')

# ============================================================================
# REQUÊTES PARTICIPANTS
# ============================================================================

@st.cache_data(ttl=1)
def get_all_participants():
    """Récupère tous les participants"""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM participants ORDER BY nom, prenom", conn)
    conn.close()
    return df

def add_participant(nom, prenom, telephone, email, nombre_terrains=0):
    """Ajoute un nouveau participant"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        date_inscription = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO participants (nom, prenom, telephone, email, date_inscription, nombre_terrains) VALUES (?, ?, ?, ?, ?, ?)",
            (nom, prenom, telephone, email, date_inscription, nombre_terrains)
        )
        conn.commit()
        conn.close()
        get_all_participants.clear()
        return True, "Participant ajouté avec succès"
    except sqlite3.IntegrityError:
        return False, "Ce participant existe déjà"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def update_participant(participant_id, nom, prenom, telephone, email, nombre_terrains):
    """Met à jour les informations d'un participant"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE participants SET nom = ?, prenom = ?, telephone = ?, email = ?, nombre_terrains = ? WHERE id = ?",
            (nom, prenom, telephone, email, nombre_terrains, participant_id)
        )
        conn.commit()
        conn.close()
        get_all_participants.clear()
        return True, "Participant mis à jour avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def delete_participant(participant_id):
    """Supprime un participant et ses cotisations"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cotisations WHERE participant_id = ?", (participant_id,))
        cursor.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
        conn.commit()
        conn.close()
        get_all_participants.clear()
        get_all_cotisations.clear()
        return True, "Participant supprimé avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

# ============================================================================
# REQUÊTES COTISATIONS
# ============================================================================

@st.cache_data(ttl=1)
def get_all_cotisations():
    """Récupère toutes les cotisations avec les informations des participants"""
    conn = get_connection()
    query = """
        SELECT 
            c.id, 
            c.participant_id,
            p.nom || ' ' || p.prenom as participant,
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

def add_cotisation(participant_id, mois, annee, montant, paye, date_paiement=None):
    """Ajoute une nouvelle cotisation"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cotisations (participant_id, mois, annee, montant, paye, date_paiement) VALUES (?, ?, ?, ?, ?, ?)",
            (participant_id, mois, annee, montant, 1 if paye else 0, date_paiement)
        )
        conn.commit()
        conn.close()
        get_all_cotisations.clear()
        get_dashboard_stats.clear()
        return True, "Cotisation ajoutée avec succès"
    except sqlite3.IntegrityError:
        return False, "Une cotisation existe déjà pour ce participant, ce mois et cette année"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def update_cotisation_status(cotisation_id, paye):
    """Met à jour le statut de paiement d'une cotisation"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        date_paiement = datetime.now().strftime("%Y-%m-%d") if paye else None
        cursor.execute(
            "UPDATE cotisations SET paye = ?, date_paiement = ? WHERE id = ?",
            (1 if paye else 0, date_paiement, cotisation_id)
        )
        conn.commit()
        conn.close()
        get_all_cotisations.clear()
        get_dashboard_stats.clear()
        return True
    except Exception as e:
        return False

# ============================================================================
# STATISTIQUES DASHBOARD
# ============================================================================

@st.cache_data(ttl=1)
def get_dashboard_stats(annee=None):
    """Calcule les statistiques pour le tableau de bord"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Nombre total de participants
    cursor.execute("SELECT COUNT(*) FROM participants")
    nb_participants = cursor.fetchone()[0]
    
    # Filtrer par année si spécifié
    annee_filter = f"AND annee = {annee}" if annee else ""
    
    # Total des cotisations encaissées
    cursor.execute(f"SELECT SUM(montant) FROM cotisations WHERE paye = 1 {annee_filter}")
    total_encaisse = cursor.fetchone()[0] or 0
    
    # Cotisations impayées
    cursor.execute(f"SELECT COUNT(*), SUM(montant) FROM cotisations WHERE paye = 0 {annee_filter}")
    result = cursor.fetchone()
    nb_impayees = result[0] or 0
    montant_impaye = result[1] or 0
    
    conn.close()
    
    return {
        'nb_participants': nb_participants,
        'total_encaisse': total_encaisse,
        'nb_impayees': nb_impayees,
        'montant_impaye': montant_impaye
    }

def get_available_years():
    """Récupère la liste des années disponibles dans les cotisations"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT annee FROM cotisations ORDER BY annee DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    return years

# ============================================================================
# IMPORT / EXPORT EXCEL
# ============================================================================

def import_participants_from_excel(df):
    """Importe des participants depuis un DataFrame Excel"""
    required_cols = ['nom', 'prenom']
    if not all(col in df.columns for col in required_cols):
        return False, "Le fichier doit contenir les colonnes: nom, prenom"
    
    success_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        nom = str(row['nom']).strip()
        prenom = str(row['prenom']).strip()
        telephone = str(row.get('telephone', '')).strip() if pd.notna(row.get('telephone')) else ''
        email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else ''
        nombre_terrains = int(row.get('nombre_terrains', 0)) if pd.notna(row.get('nombre_terrains')) else 0
        
        if not nom or not prenom:
            errors.append(f"Ligne {idx+2}: nom ou prénom manquant")
            continue
        
        success, msg = add_participant(nom, prenom, telephone, email, nombre_terrains)
        if success:
            success_count += 1
        else:
            errors.append(f"Ligne {idx+2}: {msg}")
    
    return True, f"{success_count} participant(s) importé(s). {len(errors)} erreur(s).", errors

def import_cotisations_from_excel(df):
    """Importe des cotisations depuis un DataFrame Excel"""
    required_cols = ['nom', 'prenom', 'mois', 'annee', 'montant']
    if not all(col in df.columns for col in required_cols):
        return False, "Le fichier doit contenir: nom, prenom, mois, annee, montant", []
    
    participants = get_all_participants()
    success_count = 0
    errors = []
    
    for idx, row in df.iterrows():
        nom = str(row['nom']).strip()
        prenom = str(row['prenom']).strip()
        
        # Trouver le participant
        participant = participants[(participants['nom'] == nom) & (participants['prenom'] == prenom)]
        if participant.empty:
            errors.append(f"Ligne {idx+2}: Participant {nom} {prenom} introuvable")
            continue
        
        participant_id = participant.iloc[0]['id']
        
        try:
            mois = int(row['mois'])
            annee = int(row['annee'])
            montant = float(row['montant'])
            paye = bool(row.get('paye', False)) if 'paye' in row else False
            date_paiement = row.get('date_paiement') if paye else None
            
            if mois < 1 or mois > 12:
                errors.append(f"Ligne {idx+2}: Mois invalide ({mois})")
                continue
            
            success, msg = add_cotisation(participant_id, mois, annee, montant, paye, date_paiement)
            if success:
                success_count += 1
            else:
                errors.append(f"Ligne {idx+2}: {msg}")
        except Exception as e:
            errors.append(f"Ligne {idx+2}: Erreur de format - {str(e)}")
    
    return True, f"{success_count} cotisation(s) importée(s). {len(errors)} erreur(s).", errors

def export_cotisations_to_excel(annee=None, participant_id=None):
    """Exporte les cotisations vers Excel"""
    conn = get_connection()
    
    query = """
        SELECT 
            p.nom,
            p.prenom,
            c.mois,
            c.annee,
            c.montant,
            CASE WHEN c.paye = 1 THEN 'Oui' ELSE 'Non' END as paye,
            c.date_paiement
        FROM cotisations c
        JOIN participants p ON c.participant_id = p.id
        WHERE 1=1
    """
    
    params = []
    if annee:
        query += " AND c.annee = ?"
        params.append(annee)
    if participant_id:
        query += " AND c.participant_id = ?"
        params.append(participant_id)
    
    query += " ORDER BY c.annee DESC, p.nom, p.prenom, c.mois"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

# ============================================================================
# INTERFACE STREAMLIT
# ============================================================================

def page_dashboard():
    """Page du tableau de bord"""
    st.title("📊 Tableau de Bord")
    
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
    
    # Affichage des métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Participants", stats['nb_participants'])
    
    with col2:
        st.metric("Total encaissé", f"{stats['total_encaisse']:.2f} FCFA")
    
    with col3:
        st.metric("Cotisations impayées", stats['nb_impayees'])
    
    with col4:
        st.metric("Montant impayé", f"{stats['montant_impaye']:.2f} FCFA")
    
    # Graphique récapitulatif par mois si une année est sélectionnée
    if annee:
        st.subheader(f"Détail des cotisations pour {annee}")
        
        conn = get_connection()
        query = f"""
            SELECT mois, 
                   SUM(CASE WHEN paye = 1 THEN montant ELSE 0 END) as paye,
                   SUM(CASE WHEN paye = 0 THEN montant ELSE 0 END) as impaye
            FROM cotisations
            WHERE annee = {annee}
            GROUP BY mois
            ORDER BY mois
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            mois_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                         'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
            df['mois_nom'] = df['mois'].apply(lambda x: mois_names[x-1] if 1 <= x <= 12 else str(x))
            
            chart_data = df.set_index('mois_nom')[['paye', 'impaye']]
            st.bar_chart(chart_data)

def page_participants():
    """Page de gestion des participants"""
    st.title("👤 Gestion des Participants")
    
    # Initialiser session_state pour le mode édition
    if 'edit_participant_id' not in st.session_state:
        st.session_state.edit_participant_id = None
    
    # Formulaire d'ajout
    with st.expander("➕ Ajouter un participant", expanded=False):
        with st.form("form_participant", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom *")
                telephone = st.text_input("Téléphone")
                nombre_terrains = st.number_input("Nombre de terrains", min_value=0, value=0, step=1)
            with col2:
                prenom = st.text_input("Prénom *")
                email = st.text_input("Email")
            
            submitted = st.form_submit_button("Ajouter")
            
            if submitted:
                if not nom or not prenom:
                    st.error("Le nom et le prénom sont obligatoires")
                else:
                    success, msg = add_participant(nom, prenom, telephone, email, nombre_terrains)
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
            search_term = st.text_input("🔍 Rechercher un participant (nom, prénom, téléphone, email)", 
                                       placeholder="Tapez pour rechercher...",
                                       key="search_participant")
        
        # Filtrer les participants selon la recherche
        if search_term:
            mask = (
                participants['nom'].str.contains(search_term, case=False, na=False) |
                participants['prenom'].str.contains(search_term, case=False, na=False) |
                participants['telephone'].fillna('').str.contains(search_term, case=False, na=False) |
                participants['email'].fillna('').str.contains(search_term, case=False, na=False)
            )
            participants = participants[mask]
        
        with col_total:
            st.write(f"**{len(participants)} participant(s)**")
        
        if participants.empty:
            st.warning("Aucun participant ne correspond à votre recherche")
            return
        
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
                            edit_telephone = st.text_input("Téléphone", value=row['telephone'] if row['telephone'] else "")
                            edit_terrains = st.number_input("Nombre de terrains", min_value=0, value=int(row.get('nombre_terrains', 0)), step=1)
                        with col2:
                            edit_prenom = st.text_input("Prénom *", value=row['prenom'])
                            edit_email = st.text_input("Email", value=row['email'] if row['email'] else "")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            save_btn = st.form_submit_button("💾 Enregistrer", use_container_width=True)
                        with col_cancel:
                            cancel_btn = st.form_submit_button("❌ Annuler", use_container_width=True)
                        
                        if save_btn:
                            if not edit_nom or not edit_prenom:
                                st.error("Le nom et le prénom sont obligatoires")
                            else:
                                success, msg = update_participant(row['id'], edit_nom, edit_prenom, 
                                                                edit_telephone, edit_email, edit_terrains)
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
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1.5, 1, 1])
                with col1:
                    st.write(f"**{row['nom']} {row['prenom']}**")
                with col2:
                    st.write(row['telephone'] if row['telephone'] else "-")
                with col3:
                    st.write(row['email'] if row['email'] else "-")
                with col4:
                    st.write(f"🏠 {int(row.get('nombre_terrains', 0))} terrain(s)")
                with col5:
                    if st.button("✏️", key=f"edit_part_{row['id']}", help="Modifier"):
                        st.session_state.edit_participant_id = row['id']
                        st.rerun()
                with col6:
                    if st.button("🗑️", key=f"del_part_{row['id']}", help="Supprimer"):
                        success, msg = delete_participant(row['id'])
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

def page_cotisations():
    """Page de gestion des cotisations"""
    st.title("💰 Gestion des Cotisations")
    
    participants = get_all_participants()
    
    if participants.empty:
        st.warning("Veuillez d'abord ajouter des participants")
        return
    
    # Formulaire d'ajout
    with st.expander("➕ Ajouter une cotisation", expanded=False):
        with st.form("form_cotisation", clear_on_submit=True):
            participant_options = {f"{row['nom']} {row['prenom']}": row['id'] 
                                 for _, row in participants.iterrows()}
            
            col1, col2, col3 = st.columns(3)
            with col1:
                participant_name = st.selectbox("Participant *", list(participant_options.keys()))
                mois = st.selectbox("Mois *", list(range(1, 13)), 
                                   format_func=lambda x: [
                                       'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                                       'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
                                   ][x-1])
            with col2:
                annee = st.number_input("Année *", min_value=2000, max_value=2100, 
                                       value=datetime.now().year)
                montant = st.number_input("Montant (€) *", min_value=0.0, value=0.0, step=0.01)
            with col3:
                paye = st.checkbox("Payé", value=False)
            
            submitted = st.form_submit_button("Ajouter")
            
            if submitted:
                participant_id = participant_options[participant_name]
                date_paiement = datetime.now().strftime("%Y-%m-%d") if paye else None
                
                success, msg = add_cotisation(participant_id, mois, annee, montant, paye, date_paiement)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
    
    # Section pour marquer une cotisation comme payée
    with st.expander("💳 Marquer une cotisation comme payée", expanded=False):
        cotisations = get_all_cotisations()
        cotisations_impayees = cotisations[cotisations['paye'] == 0]
        
        if cotisations_impayees.empty:
            st.info("Aucune cotisation impayée")
        else:
            # Barre de recherche pour les cotisations impayées
            search_unpaid = st.text_input("🔍 Rechercher dans les cotisations impayées", 
                                         placeholder="Nom du participant...",
                                         key="search_unpaid_cotis")
            
            if search_unpaid:
                mask = cotisations_impayees['participant'].str.contains(search_unpaid, case=False, na=False)
                cotisations_impayees = cotisations_impayees[mask]
            
            st.write(f"**{len(cotisations_impayees)} cotisation(s) impayée(s)**")
            
            if cotisations_impayees.empty:
                st.warning("Aucune cotisation impayée ne correspond à votre recherche")
                return
            
            for idx, row in cotisations_impayees.iterrows():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 1])
                with col1:
                    st.write(f"**{row['participant']}**")
                with col2:
                    mois_nom = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                               'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'][row['mois']-1]
                    st.write(f"{mois_nom} {row['annee']}")
                with col3:
                    st.write(f"{row['montant']:.2f} €")
                with col4:
                    st.write("❌ Non payé")
                with col5:
                    if st.button("✅ Payé", key=f"pay_{row['id']}", type="primary"):
                        if update_cotisation_status(row['id'], True):
                            st.success("Cotisation marquée comme payée")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la mise à jour")
    
    # Affichage des cotisations
    st.subheader("Cotisations par année")
    
    cotisations = get_all_cotisations()
    
    if cotisations.empty:
        st.info("Aucune cotisation enregistrée")
        return
    
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
            return
    
    # Créer un tableau pivotant (participants x mois)
    mois_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 
                 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
    
    # Obtenir la liste unique des participants pour cette année
    participants_year = cotis_year['participant'].unique()
    
    for participant_name in sorted(participants_year):
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
                        button_label = f"✓ {montant:.0f}€"
                        button_type = "primary"
                    else:
                        button_label = f"✗ {montant:.0f}€"
                        button_type = "secondary"
                    
                    if st.button(button_label, key=f"cotis_{cotis_id}", 
                               type=button_type, use_container_width=True):
                        # Toggle le statut
                        update_cotisation_status(cotis_id, not paye)
                        st.rerun()
                else:
                    st.write(mois_names[mois_num - 1])
        
        st.divider()

def page_import():
    """Page d'import Excel"""
    st.title("📥 Import Excel")
    
    tab1, tab2 = st.tabs(["Import Participants", "Import Cotisations"])
    
    with tab1:
        st.subheader("Import de participants")
        st.write("Format attendu: colonnes **nom**, **prenom** (obligatoires), telephone, email (optionnels)")
        
        uploaded_file = st.file_uploader("Choisir un fichier Excel", type=['xlsx', 'xls'], key="import_part")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                st.write("**Aperçu des données:**")
                st.dataframe(df.head(10))
                
                if st.button("Confirmer l'import", key="confirm_import_part"):
                    with st.spinner("Import en cours..."):
                        success, msg, errors = import_participants_from_excel(df)
                        if success:
                            st.success(msg)
                            if errors:
                                with st.expander("Voir les erreurs"):
                                    for error in errors:
                                        st.warning(error)
                            st.rerun()
                        else:
                            st.error(msg)
            except Exception as e:
                st.error(f"Erreur de lecture du fichier: {str(e)}")
    
    with tab2:
        st.subheader("Import de cotisations")
        st.write("Format attendu: **nom**, **prenom**, **mois** (1-12), **annee**, **montant** (obligatoires), paye (optionnel)")
        
        uploaded_file = st.file_uploader("Choisir un fichier Excel", type=['xlsx', 'xls'], key="import_cotis")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                st.write("**Aperçu des données:**")
                st.dataframe(df.head(10))
                
                if st.button("Confirmer l'import", key="confirm_import_cotis"):
                    with st.spinner("Import en cours..."):
                        success, msg, errors = import_cotisations_from_excel(df)
                        if success:
                            st.success(msg)
                            if errors:
                                with st.expander("Voir les erreurs"):
                                    for error in errors:
                                        st.warning(error)
                            st.rerun()
                        else:
                            st.error(msg)
            except Exception as e:
                st.error(f"Erreur de lecture du fichier: {str(e)}")

def page_export():
    """Page d'export Excel"""
    st.title("📤 Export Excel")
    
    st.subheader("Export des cotisations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtrer par année
        years = get_available_years()
        year_options = ["Toutes"] + years
        selected_year = st.selectbox("Année", year_options, key="export_year")
    
    with col2:
        # Filtrer par participant
        participants = get_all_participants()
        participant_options = ["Tous"] + [f"{row['nom']} {row['prenom']}" 
                                         for _, row in participants.iterrows()]
        selected_participant = st.selectbox("Participant", participant_options, key="export_part")
    
    if st.button("Générer l'export Excel"):
        annee = None if selected_year == "Toutes" else selected_year
        
        participant_id = None
        if selected_participant != "Tous":
            for _, row in participants.iterrows():
                if f"{row['nom']} {row['prenom']}" == selected_participant:
                    participant_id = row['id']
                    break
        
        df = export_cotisations_to_excel(annee, participant_id)
        
        if df.empty:
            st.warning("Aucune cotisation à exporter avec ces filtres")
        else:
            st.write(f"**{len(df)} cotisation(s) à exporter**")
            st.dataframe(df.head(20))
            
            # Créer le fichier Excel en mémoire
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Cotisations')
            
            output.seek(0)
            
            filename = f"cotisations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            st.download_button(
                label="📥 Télécharger le fichier Excel",
                data=output,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ============================================================================
# APPLICATION PRINCIPALE
# ============================================================================

def main():
    """Fonction principale de l'application"""
    
    # Initialiser la base de données
    init_database()
    
    # Sidebar - Sélecteur de thème
    st.sidebar.title("⚙️ Paramètres")
    
    theme = st.sidebar.radio(
        "Mode d'affichage",
        ["🌞 Clair", "🌙 Sombre"],
        index=0
    )
    
    # Appliquer le thème via CSS custom
    if "🌙 Sombre" in theme:
        st.markdown("""
            <style>
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
            }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {
                background-color: #ffffff;
                color: #000000;
            }
            </style>
        """, unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    # Sidebar - Menu
    st.sidebar.title("📋 Menu")
    
    menu_options = {
        "Tableau de bord": "📊",
        "Participants": "👤",
        "Cotisations": "💰",
        "Import Excel": "📥",
        "Export Excel": "📤"
    }
    
    selection = st.sidebar.radio(
        "Navigation",
        list(menu_options.keys()),
        format_func=lambda x: f"{menu_options[x]} {x}"
    )
    
    st.sidebar.divider()
    st.sidebar.info("**Gestion de Cotisations**\nVersion 1.0\n\nDéveloppé avec Streamlit")
    
    # Afficher la page sélectionnée
    if selection == "Tableau de bord":
        page_dashboard()
    elif selection == "Participants":
        page_participants()
    elif selection == "Cotisations":
        page_cotisations()
    elif selection == "Import Excel":
        page_import()
    elif selection == "Export Excel":
        page_export()

if __name__ == "__main__":
    main()
