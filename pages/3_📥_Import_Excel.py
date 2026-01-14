"""
Page Import Excel
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from database import DB_NAME
from constants import COTISATION_MIN
from auth import require_authentication, show_logout_button

# Configuration de la page
st.set_page_config(
    page_title="Import Excel - MEDD",
    page_icon="📥",
    layout="wide"
)

# Vérifier l'authentification
require_authentication()

# Afficher le bouton de déconnexion
show_logout_button()

# ============================================================================
# REQUÊTES POUR L'IMPORT
# ============================================================================

def get_all_participants():
    """Récupère tous les participants"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM participants ORDER BY nom, prenom", conn)
    conn.close()
    return df

def add_participant(nom, prenom, nombre_terrains=0, conn=None):
    """Ajoute un nouveau participant"""
    should_close = False
    if conn is None:
        conn = sqlite3.connect(DB_NAME)
        should_close = True
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO participants (nom, prenom, nombre_terrains, telephone, email) VALUES (?, ?, ?, ?, ?)",
            (nom, prenom, nombre_terrains, "", "")
        )
        if should_close:
            conn.commit()
            conn.close()
        return True, "Participant ajouté avec succès"
    except sqlite3.IntegrityError:
        if should_close:
            conn.close()
        return False, "Ce participant existe déjà"
    except Exception as e:
        if should_close:
            conn.close()
        return False, f"Erreur: {str(e)}"


def import_cotisations_from_excel_pivot(df, auto_mark_paid=False):
    """
    Importe des cotisations depuis un DataFrame Excel au format pivot MEDD
    Format attendu : colonnes 'nom', 'prenom', puis colonnes date format "ANNEE-MOIS"
    """
    success_count = 0
    errors = []

    # Identifier les colonnes de mois (format YYYY-MM)
    month_cols = [c for c in df.columns if "-" in str(c)]

    if not month_cols:
        return False, "Aucune colonne de date trouvée (format attendu: 2024-01, 2024-02, etc.)", []

    total_operations = len(df) * len(month_cols)
    progress_bar = st.progress(0)
    status_text = st.empty()
    current = 0

    # Utiliser une transaction pour garantir l'intégrité
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Charger tous les participants dans un dict pour éviter les requêtes répétées
        cursor.execute("SELECT id, nom, prenom, nombre_terrains FROM participants")
        participants_cache = {}
        for pid, nom, prenom, nb_terrains in cursor.fetchall():
            participants_cache[f"{nom}|{prenom}"] = {'id': pid, 'nombre_terrains': nb_terrains}
        
        for idx, row in df.iterrows():
            nom = str(row.get('nom', '')).strip()
            prenom = str(row.get('prenom', '')).strip()
            
            if not nom or not prenom:
                errors.append(f"Ligne {idx+2}: nom ou prénom manquant")
                continue
            
            # Trouver ou créer le participant
            key = f"{nom}|{prenom}"
            
            if key not in participants_cache:
                # Créer automatiquement le participant
                nombre_terrains = int(row.get('nombre_terrains', 0)) if pd.notna(row.get('nombre_terrains')) else 0
                try:
                    cursor.execute(
                        "INSERT INTO participants (nom, prenom, nombre_terrains, telephone, email) VALUES (?, ?, ?, ?, ?)",
                        (nom, prenom, nombre_terrains, "", "")
                    )
                    participant_id = cursor.lastrowid
                    participants_cache[key] = {'id': participant_id, 'nombre_terrains': nombre_terrains}
                except sqlite3.IntegrityError:
                    # Le participant existe déjà, le récupérer
                    cursor.execute("SELECT id, nombre_terrains FROM participants WHERE nom = ? AND prenom = ?", (nom, prenom))
                    result = cursor.fetchone()
                    if result:
                        participants_cache[key] = {'id': result[0], 'nombre_terrains': result[1]}
                    else:
                        errors.append(f"Ligne {idx+2}: Impossible de créer ou trouver le participant {nom} {prenom}")
                        continue
                except Exception as e:
                    errors.append(f"Ligne {idx+2}: Erreur création participant - {str(e)}")
                    continue
            
            participant_id = participants_cache[key]['id']
            nb_terrains = participants_cache[key]['nombre_terrains']
            
            # Traiter chaque colonne de mois
            for col in month_cols:
                current += 1
                progress_bar.progress(current / total_operations)
                status_text.text(f"Import en cours... {current}/{total_operations}")
                
                if pd.isna(row[col]):
                    continue
                
                try:
                    # Parser la colonne (format: YYYY-MM)
                    annee_str, mois_str = str(col).split("-")
                    annee = int(annee_str)
                    mois = int(mois_str)
                    montant = float(row[col])
                    
                    if mois < 1 or mois > 12:
                        errors.append(f"{nom} {prenom} - {col}: Mois invalide")
                        continue
                    
                    # Validation du montant
                    if montant < 0:
                        errors.append(f"{nom} {prenom} - {col}: Montant négatif")
                        continue
                    
                    if montant < COTISATION_MIN:
                        errors.append(f"{nom} {prenom} - {col}: Montant inférieur au minimum ({COTISATION_MIN} FCFA)")
                        continue
                    
                    # Insérer ou remplacer la cotisation
                    paye_value = 1 if auto_mark_paid else 0
                    date_paiement = datetime.now().strftime("%Y-%m-%d") if auto_mark_paid else None
                    
                    # Créer une cotisation par terrain ou une seule avec NULL si nb_terrains <= 1
                    if nb_terrains > 1:
                        montant_par_terrain = montant / nb_terrains
                        for terrain_num in range(1, nb_terrains + 1):
                            # Vérifier si existe déjà
                            cursor.execute("""
                                SELECT id FROM cotisations 
                                WHERE participant_id = ? AND mois = ? AND annee = ? AND numero_terrain = ?
                            """, (participant_id, mois, annee, terrain_num))
                            
                            existing = cursor.fetchone()
                            if existing:
                                cursor.execute("""
                                    UPDATE cotisations
                                    SET montant = ?, paye = ?, date_paiement = ?
                                    WHERE id = ?
                                """, (montant_par_terrain, paye_value, date_paiement, existing[0]))
                            else:
                                cursor.execute("""
                                    INSERT INTO cotisations
                                    (participant_id, mois, annee, montant, paye, date_paiement, numero_terrain)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (participant_id, mois, annee, montant_par_terrain, paye_value, date_paiement, terrain_num))
                    else:
                        # Une seule cotisation sans numéro de terrain spécifique
                        cursor.execute("""
                            SELECT id FROM cotisations 
                            WHERE participant_id = ? AND mois = ? AND annee = ? AND numero_terrain IS NULL
                        """, (participant_id, mois, annee))
                        
                        existing = cursor.fetchone()
                        if existing:
                            cursor.execute("""
                                UPDATE cotisations
                                SET montant = ?, paye = ?, date_paiement = ?
                                WHERE id = ?
                            """, (montant, paye_value, date_paiement, existing[0]))
                        else:
                            cursor.execute("""
                                INSERT INTO cotisations
                                (participant_id, mois, annee, montant, paye, date_paiement, numero_terrain)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (participant_id, mois, annee, montant, paye_value, date_paiement, None))
                    
                    success_count += 1
                    
                except ValueError as e:
                    errors.append(f"{nom} {prenom} - {col}: Format invalide ({e})")
                except Exception as e:
                    errors.append(f"{nom} {prenom} - {col}: Erreur {str(e)}")
        
        # Commit de la transaction si tout s'est bien passé
        conn.commit()
        
    except Exception as e:
        # Rollback en cas d'erreur
        conn.rollback()
        conn.close()
        return False, f"Erreur lors de l'import: {str(e)}", errors
    finally:
        conn.close()

    progress_bar.empty()
    status_text.empty()

    return True, f"{success_count} cotisation(s) importée(s)", errors


st.title("📥 Import Excel")

st.write("Importez vos cotisations depuis un fichier Excel au format pivot.")

st.divider()

# Bouton de téléchargement du fichier modèle
st.subheader("📥 Télécharger le fichier modèle")

st.info("💡 **Téléchargez le fichier Excel modèle pré-formaté avec instructions et données exemple**")

import os
modele_path = os.path.join(os.path.dirname(__file__), '..', 'modele_import_cotisations.xlsx')

if os.path.exists(modele_path):
    with open(modele_path, 'rb') as f:
        st.download_button(
            label="📥 Télécharger le fichier modèle Excel",
            data=f,
            file_name="modele_import_cotisations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
else:
    st.warning("⚠️ Le fichier modèle n'existe pas. Générez-le d'abord avec `python3 generer_modele_import.py`")

st.divider()

st.subheader("📋 Format attendu")

st.markdown("""
Le fichier Excel doit avoir le format suivant :
- **Colonne 1** : `nom` - Nom du participant
- **Colonne 2** : `prenom` - Prénom du participant
- **Colonne 3** (optionnelle) : `nombre_terrains` - Nombre de terrains
- **Colonnes suivantes** : Format `ANNEE-MOIS` (ex: `2025-08`, `2025-09`, etc.)

Les montants doivent être supérieurs ou égaux à **{:,}** FCFA.
""".format(COTISATION_MIN).replace(',', ' '))

st.info("💡 Les participants n'existant pas seront créés automatiquement lors de l'import.")

st.markdown("**Exemple de fichier valide :**")

example_data = {
    'nom': ['Dupont', 'Martin', 'Durand'],
    'prenom': ['Jean', 'Marie', 'Paul'],
    'nombre_terrains': [2, 1, 3],
    '2025-08': [2000, 1000, 3000],
    '2025-09': [2000, 1000, None],
    '2025-10': [2000, None, 3000]
}
st.dataframe(pd.DataFrame(example_data), use_container_width=True)

st.divider()

st.subheader("📤 Télécharger le fichier")

# Option pour marquer comme payé
auto_mark_paid = st.checkbox(
    "✅ Marquer toutes les cotisations importées comme payées automatiquement",
    value=False,
    help="Si coché, toutes les cotisations importées seront marquées comme payées avec la date d'aujourd'hui"
)

uploaded_file = st.file_uploader(
    "Choisir un fichier Excel (.xlsx ou .xls)", 
    type=['xlsx', 'xls'], 
    key="import_pivot"
)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Fichier chargé avec succès")
        
        st.write("**📊 Aperçu des données :**")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Statistiques du fichier
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Lignes détectées", len(df))
        
        # Validation du format
        month_cols = [c for c in df.columns if "-" in str(c)]
        with col2:
            st.metric("Colonnes de date", len(month_cols))
        
        with col3:
            total_cotis = sum(df[col].notna().sum() for col in month_cols)
            st.metric("Cotisations à importer", total_cotis)
        
        if month_cols:
            st.write(f"**📅 Colonnes de date détectées :** {', '.join(month_cols[:10])}{'...' if len(month_cols) > 10 else ''}")
        else:
            st.error("⚠️ Aucune colonne de date trouvée ! Vérifiez que vos colonnes sont au format ANNEE-MOIS (ex: 2025-08)")
        
        st.divider()
        
        if st.button("🚀 Confirmer et lancer l'import", type="primary", use_container_width=True):
            with st.spinner("Import en cours..."):
                success, msg, errors = import_cotisations_from_excel_pivot(df, auto_mark_paid)
                if success:
                    st.success(f"✅ {msg}")
                    if errors:
                        with st.expander(f"⚠️ {len(errors)} avertissement(s) / erreur(s)"):
                            for error in errors:
                                st.warning(error)
                    st.balloons()
                    st.info("💡 Rechargez la page ou consultez les autres pages pour voir les données importées")
                else:
                    st.error(f"❌ {msg}")
                    if errors:
                        with st.expander("Détails des erreurs"):
                            for error in errors:
                                st.error(error)
    except Exception as e:
        st.error(f"❌ Erreur de lecture du fichier: {str(e)}")
        st.info("💡 Assurez-vous que le fichier est bien au format Excel (.xlsx ou .xls)")
else:
    st.info("👆 Veuillez sélectionner un fichier Excel pour commencer l'import")
