"""
Script de test pour vérifier la structure de la base de données après migration
"""

import sqlite3
from database import DB_NAME

def test_database_structure():
    """Teste la structure de la base de données"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("TEST DE LA STRUCTURE DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    # Vérifier la structure de la table cotisations
    print("\n📋 Structure de la table 'cotisations' :")
    cursor.execute("PRAGMA table_info(cotisations)")
    columns = cursor.fetchall()
    
    expected_columns = ['id', 'participant_id', 'mois', 'annee', 'montant', 'paye', 'date_paiement', 'numero_terrain']
    found_columns = [col[1] for col in columns]
    
    print("\nColonnes trouvées :")
    for col in columns:
        col_id, col_name, col_type, not_null, default_val, pk = col
        nullable = "NOT NULL" if not_null else "NULL"
        pk_info = " (PRIMARY KEY)" if pk else ""
        print(f"  - {col_name}: {col_type} {nullable}{pk_info}")
    
    # Vérifier que toutes les colonnes attendues sont présentes
    missing_columns = set(expected_columns) - set(found_columns)
    if missing_columns:
        print(f"\n❌ Colonnes manquantes : {missing_columns}")
    else:
        print("\n✅ Toutes les colonnes attendues sont présentes")
    
    # Vérifier les index
    print("\n📊 Index sur la table 'cotisations' :")
    cursor.execute("PRAGMA index_list(cotisations)")
    indexes = cursor.fetchall()
    for idx in indexes:
        idx_name = idx[1]
        cursor.execute(f"PRAGMA index_info({idx_name})")
        idx_cols = cursor.fetchall()
        col_names = [col[2] for col in idx_cols]
        print(f"  - {idx_name}: {', '.join(col_names)}")
    
    # Vérifier quelques cotisations
    print("\n📝 Échantillon de cotisations :")
    cursor.execute("""
        SELECT c.id, p.nom, p.prenom, c.mois, c.annee, c.montant, c.numero_terrain
        FROM cotisations c
        JOIN participants p ON c.participant_id = p.id
        LIMIT 5
    """)
    
    cotisations = cursor.fetchall()
    if cotisations:
        print("  ID | Participant | Mois | Année | Montant | Terrain")
        print("  " + "-" * 60)
        for cot in cotisations:
            cot_id, nom, prenom, mois, annee, montant, terrain = cot
            terrain_str = f"n°{terrain}" if terrain else "Tous"
            print(f"  {cot_id:3d} | {nom} {prenom:10s} | {mois:2d} | {annee} | {montant:7.0f} | {terrain_str}")
    else:
        print("  Aucune cotisation dans la base")
    
    # Statistiques
    print("\n📈 Statistiques :")
    cursor.execute("SELECT COUNT(*) FROM participants")
    nb_participants = cursor.fetchone()[0]
    print(f"  - Participants : {nb_participants}")
    
    cursor.execute("SELECT COUNT(*) FROM cotisations")
    nb_cotisations = cursor.fetchone()[0]
    print(f"  - Cotisations : {nb_cotisations}")
    
    cursor.execute("SELECT COUNT(*) FROM cotisations WHERE numero_terrain IS NOT NULL")
    nb_avec_terrain = cursor.fetchone()[0]
    print(f"  - Cotisations avec numéro de terrain : {nb_avec_terrain}")
    
    cursor.execute("SELECT COUNT(*) FROM cotisations WHERE numero_terrain IS NULL")
    nb_sans_terrain = cursor.fetchone()[0]
    print(f"  - Cotisations sans numéro (ancien format) : {nb_sans_terrain}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Test terminé")
    print("=" * 60)

if __name__ == "__main__":
    test_database_structure()
