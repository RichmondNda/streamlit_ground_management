"""
Gestion de la base de données SQLite
Ce module contient uniquement l'initialisation de la base de données.
Chaque page contient ses propres requêtes spécifiques.
"""

import sqlite3

DB_NAME = "database.db"

# ============================================================================
# INITIALISATION
# ============================================================================

def init_database():
    """Initialise la base de données SQLite avec les tables nécessaires"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Table participants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            nombre_terrains INTEGER DEFAULT 0,
            telephone TEXT,
            email TEXT,
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
