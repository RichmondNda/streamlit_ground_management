"""
Script de migration de la base de données
Ajoute les colonnes telephone et email à la table participants
"""

import sqlite3
from database import DB_NAME, init_database

def migrate_database():
    """Ajoute les colonnes telephone et email si elles n'existent pas"""
    # Initialiser la base de données si elle n'existe pas
    init_database()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Vérifier les colonnes existantes
    cursor.execute("PRAGMA table_info(participants)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Ajouter telephone si elle n'existe pas
    if 'telephone' not in columns:
        print("Ajout de la colonne 'telephone'...")
        cursor.execute("ALTER TABLE participants ADD COLUMN telephone TEXT")
        print("✓ Colonne 'telephone' ajoutée")
    else:
        print("✓ La colonne 'telephone' existe déjà")
    
    # Ajouter email si elle n'existe pas
    if 'email' not in columns:
        print("Ajout de la colonne 'email'...")
        cursor.execute("ALTER TABLE participants ADD COLUMN email TEXT")
        print("✓ Colonne 'email' ajoutée")
    else:
        print("✓ La colonne 'email' existe déjà")
    
    conn.commit()
    conn.close()
    print("\n✅ Migration terminée avec succès!")

if __name__ == "__main__":
    migrate_database()
