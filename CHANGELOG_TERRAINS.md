# Changelog - Gestion des terrains individuels

## Version 2.0 - Janvier 2026

### 🎯 Nouvelle fonctionnalité majeure : Gestion des terrains individuels

Chaque participant peut maintenant avoir plusieurs terrains, et les cotisations sont gérées individuellement par terrain.

---

## Modifications apportées

### 📊 Base de données

**Fichier modifié : `database.py`**
- Ajout de la colonne `numero_terrain` (INTEGER, nullable) à la table `cotisations`
- Modification de la contrainte UNIQUE : `(participant_id, mois, annee, numero_terrain)`
- Ancienne contrainte : `(participant_id, mois, annee)`

**Script de migration : `migrate_add_terrain_number.py`** (nouveau)
- Ajoute la colonne `numero_terrain` aux bases existantes
- Conserve les données existantes avec `numero_terrain = NULL`
- Vérification de l'existence de la colonne avant migration

**Script de test : `test_db_structure.py`** (nouveau)
- Vérifie la structure de la base de données
- Affiche les colonnes, index et statistiques
- Utile pour diagnostiquer les problèmes

---

### 💰 Page Cotisations (2_💰_Cotisations.py)

#### Modifications des requêtes

**`get_all_participants()`**
- Ajout de la colonne `nombre_terrains` dans la requête

**`get_all_cotisations()`**
- Ajout de la colonne `c.numero_terrain`
- Tri par terrain : `ORDER BY ... c.numero_terrain`

#### Modification de `add_cotisation()`

**Nouveau paramètre : `numero_terrain=None`**
- Si `None` : Répartition équitable entre tous les terrains
  - Crée N cotisations (N = nombre de terrains)
  - Montant par terrain = montant total / N
- Si spécifié : Une seule cotisation pour ce terrain

**Exemple :**
```python
# Avant : 1 cotisation de 3000 FCFA
add_cotisation(participant_id=1, mois=1, annee=2026, montant=3000)

# Maintenant : 3 cotisations de 1000 FCFA chacune (si 3 terrains)
add_cotisation(participant_id=1, mois=1, annee=2026, montant=3000, numero_terrain=None)

# Ou : 1 cotisation de 3000 FCFA pour le terrain n°2
add_cotisation(participant_id=1, mois=1, annee=2026, montant=3000, numero_terrain=2)
```

#### Modification de `generer_cotisations_mensuelles()`

**Nouvelle logique : Une cotisation par terrain**
- Avant : 1 cotisation par participant (montant = nb_terrains × 1000)
- Maintenant : N cotisations par participant (N = nb_terrains, montant = 1000 chacune)

**Avantages :**
- Permet le paiement terrain par terrain
- Meilleur suivi des paiements partiels
- Alignement avec la réalité des paiements

#### Interface utilisateur

**Formulaire d'ajout :**
- Nouveau champ : Sélection du terrain
  - Options : "Tous les terrains", "Terrain n°1", "Terrain n°2", etc.
  - Le nombre d'options dépend du participant sélectionné
  - Tooltip explicatif sur la répartition équitable

**Liste des cotisations impayées :**
- Affichage du numéro de terrain à côté du nom
- Format : "Nom Prénom - Terrain n°2" ou "Nom Prénom - Tous les terrains"

**Tableau annuel :**
- Groupement par participant, puis par terrain
- Chaque terrain a sa propre ligne avec 12 colonnes (mois)
- Section séparée pour les anciennes cotisations (sans numéro)
- Format : "🏞️ Terrain n°1", "🏞️ Terrain n°2", etc.

---

### 📋 Page Liste Cotisations (5_📋_Liste_Cotisations.py)

**`get_cotisations_detaillees()`**
- Ajout de `c.numero_terrain` dans la requête
- Tri par terrain

**Affichage :**
- Nouvelle colonne "Terrain" dans le tableau
- Format : "n°1", "n°2", "n°3", ou "Tous"

---

### 📥 Page Import Excel (3_📥_Import_Excel.py)

**`import_cotisations_from_excel_pivot()`**

**Nouvelle logique d'import :**
1. Si `nombre_terrains > 1` :
   - Divise le montant par le nombre de terrains
   - Crée une cotisation par terrain
   - Utilise UPDATE si existe, INSERT sinon

2. Si `nombre_terrains ≤ 1` :
   - Crée une seule cotisation avec `numero_terrain = NULL`

**Gestion des doublons :**
- Avant : `INSERT OR REPLACE` (pouvait causer des pertes de données)
- Maintenant : Vérification explicite avec UPDATE ou INSERT

---

### 📤 Page Export Excel (4_📤_Export_Excel.py)

**`generate_cotisations_report()`**
- Ajout de `nombre_terrains` dans la requête participants
- Utilisation de `SUM(montant)` pour agréger les terrains
- Nouvelle colonne "nombre_terrains" dans l'export

**`export_cotisations_to_excel_pivot()`**
- Utilisation de `aggfunc='sum'` pour agréger automatiquement
- Colonne "nombre_terrains" ajoutée pour référence

---

### 📊 Page Dashboard (0_📊_Dashboard.py)

**Aucune modification requise**
- Les requêtes utilisent déjà `SUM(montant)`
- Agrégation automatique des terrains

---

## 🔄 Compatibilité ascendante

### Cotisations existantes
- Les cotisations créées avant cette mise à jour ont `numero_terrain = NULL`
- Elles sont interprétées comme "tous les terrains" (ancien format)
- Affichées séparément dans le tableau annuel

### Import Excel
- Les fichiers Excel existants continuent de fonctionner
- L'import détecte automatiquement le nombre de terrains et crée les cotisations appropriées

---

## 📝 Documentation

**Fichiers créés :**
- `TERRAIN_FEATURE.md` : Documentation complète de la fonctionnalité
- `CHANGELOG_TERRAINS.md` : Ce fichier (détail des modifications)
- `test_db_structure.py` : Script de test de la base de données

---

## 🧪 Tests recommandés

1. **Vérifier la migration :**
   ```bash
   python3 test_db_structure.py
   ```

2. **Tester l'ajout manuel :**
   - Ajouter une cotisation pour "Tous les terrains"
   - Vérifier que N cotisations sont créées
   - Ajouter une cotisation pour un terrain spécifique
   - Vérifier qu'une seule cotisation est créée

3. **Tester la génération mensuelle :**
   - Générer les cotisations d'un mois
   - Vérifier qu'il y a bien N cotisations par participant
   - Vérifier que le montant est 1000 FCFA par terrain

4. **Tester l'import Excel :**
   - Importer un fichier avec des participants multi-terrains
   - Vérifier la répartition des montants

5. **Tester les exports :**
   - Exporter le rapport depuis août 2025
   - Vérifier l'agrégation des montants
   - Exporter en format pivot
   - Vérifier que la colonne nombre_terrains est présente

---

## ⚠️ Points d'attention

1. **Contrainte UNIQUE modifiée**
   - Impossible d'avoir deux cotisations identiques pour le même terrain
   - Erreur si tentative de créer un doublon

2. **Répartition équitable**
   - Division du montant peut créer des décimales
   - Exemple : 1000 FCFA / 3 terrains = 333.33 FCFA par terrain

3. **Ancienne interface vs nouvelle**
   - Les anciennes cotisations (NULL) sont toujours visibles
   - Pas de migration automatique vers le nouveau format
   - Possibilité d'avoir un mix des deux formats

---

## 🚀 Migration recommandée pour utilisateurs existants

1. **Sauvegarder la base de données**
   ```bash
   cp database.db database_backup_$(date +%Y%m%d).db
   ```

2. **Exécuter la migration**
   ```bash
   python3 migrate_add_terrain_number.py
   ```

3. **Vérifier la structure**
   ```bash
   python3 test_db_structure.py
   ```

4. **Tester avec Streamlit**
   ```bash
   streamlit run Home.py
   ```

5. **Régénérer les cotisations futures**
   - Utiliser la nouvelle génération mensuelle
   - Les nouvelles cotisations auront des numéros de terrain

---

## 📞 Support

En cas de problème :
1. Vérifier les logs de la migration
2. Exécuter le script de test
3. Vérifier que `numero_terrain` existe dans la table cotisations
4. S'assurer que la contrainte UNIQUE inclut `numero_terrain`
