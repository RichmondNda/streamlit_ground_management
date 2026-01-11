"""
Gestion de la base de données SQLite
"""

import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
from constants import ANNEE_MIN, ANNEE_MAX, MOIS_MIN, MOIS_MAX, MONTANT_MIN

DB_NAME = "database.db"

# ============================================================================
# CONNEXION ET INITIALISATION
# ============================================================================

def get_connection():
    """Retourne une connexion à la base de données avec row_factory"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialise la base de données SQLite avec les tables nécessaires"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table participants (version simplifiée sans téléphone/email/date_inscription)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            nombre_terrains INTEGER DEFAULT 0,
            UNIQUE(nom, prenom)
        )
    ''')
    
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
    
    # Créer des index pour améliorer les performances
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cotisations_participant 
        ON cotisations(participant_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cotisations_annee 
        ON cotisations(annee)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_cotisations_paye 
        ON cotisations(paye)
    ''')
    
    conn.commit()
    conn.close()

# ============================================================================
# REQUÊTES PARTICIPANTS
# ============================================================================

def get_all_participants():
    """Récupère tous les participants"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM participants ORDER BY nom, prenom", conn)
    conn.close()
    return df

def add_participant(nom, prenom, nombre_terrains=0):
    """Ajoute un nouveau participant"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO participants (nom, prenom, nombre_terrains) VALUES (?, ?, ?)",
            (nom, prenom, nombre_terrains)
        )
        conn.commit()
        conn.close()
        return True, "Participant ajouté avec succès"
    except sqlite3.IntegrityError:
        return False, "Ce participant existe déjà"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def update_participant(participant_id, nom, prenom, nombre_terrains):
    """Met à jour les informations d'un participant"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE participants SET nom = ?, prenom = ?, nombre_terrains = ? WHERE id = ?",
            (nom, prenom, nombre_terrains, participant_id)
        )
        conn.commit()
        conn.close()
        return True, "Participant mis à jour avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def delete_participant(participant_id):
    """Supprime un participant et ses cotisations"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cotisations WHERE participant_id = ?", (participant_id,))
        cursor.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
        conn.commit()
        conn.close()
        return True, "Participant supprimé avec succès"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

# ============================================================================
# REQUÊTES COTISATIONS
# ============================================================================

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

def add_cotisation(participant_id, mois, annee, montant, paye, date_paiement=None):
    """Ajoute une nouvelle cotisation"""
    # Validation des données
    if not isinstance(mois, int) or mois < MOIS_MIN or mois > MOIS_MAX:
        return False, f"Le mois doit être entre {MOIS_MIN} et {MOIS_MAX}"
    if not isinstance(annee, int) or annee < ANNEE_MIN or annee > ANNEE_MAX:
        return False, f"L'année doit être entre {ANNEE_MIN} et {ANNEE_MAX}"
    if not isinstance(montant, (int, float)) or montant < MONTANT_MIN:
        return False, "Le montant doit être positif"
    
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cotisations (participant_id, mois, annee, montant, paye, date_paiement) VALUES (?, ?, ?, ?, ?, ?)",
            (participant_id, mois, annee, montant, 1 if paye else 0, date_paiement)
        )
        conn.commit()
        conn.close()
        return True, "Cotisation ajoutée avec succès"
    except sqlite3.IntegrityError:
        return False, "Une cotisation existe déjà pour ce participant, ce mois et cette année"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def update_cotisation_status(cotisation_id, paye):
    """Met à jour le statut de paiement d'une cotisation"""
    try:
        conn = sqlite3.connect(DB_NAME)
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
# STATISTIQUES
# ============================================================================

def get_dashboard_stats(annee=None):
    """Calcule les statistiques pour le tableau de bord"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Nombre total de participants
    cursor.execute("SELECT COUNT(*) FROM participants")
    nb_participants = cursor.fetchone()[0]
    
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
    
    return {
        'nb_participants': nb_participants,
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
