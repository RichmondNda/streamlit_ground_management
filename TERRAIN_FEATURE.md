# Gestion des terrains individuels dans les cotisations

## Présentation

Cette fonctionnalité permet de gérer les cotisations par terrain individuel pour chaque participant.

## Fonctionnement

### Base de données

- Une nouvelle colonne `numero_terrain` a été ajoutée à la table `cotisations`
- La contrainte UNIQUE est maintenant sur `(participant_id, mois, annee, numero_terrain)`
- Les cotisations existantes ont `numero_terrain = NULL` (ancien format, tous les terrains)

### Ajout manuel de cotisation

Lors de l'ajout d'une cotisation, vous pouvez maintenant choisir :

1. **"Tous les terrains"** : Le montant saisi sera automatiquement réparti équitablement entre tous les terrains du participant
   - Exemple : 3000 FCFA pour 3 terrains = 3 cotisations de 1000 FCFA chacune
   
2. **"Terrain n°X"** : Une seule cotisation sera créée pour le terrain spécifié
   - Exemple : Terrain n°2 = une cotisation de 1000 FCFA pour le terrain 2 uniquement

### Génération mensuelle automatique

La fonction "Générer les cotisations mensuelles" crée maintenant **une cotisation par terrain** pour chaque participant :

- Participant avec 1 terrain → 1 cotisation de 1000 FCFA (terrain n°1)
- Participant avec 3 terrains → 3 cotisations de 1000 FCFA chacune (terrains n°1, 2, 3)
- Montant par terrain = 1000 FCFA (défini dans `COTISATION_PAR_TERRAIN`)

### Affichage

#### Page Cotisations (2_💰_Cotisations.py)

- **Liste des cotisations impayées** : Affiche le numéro de terrain ou "Tous les terrains"
- **Tableau annuel** : Groupé par participant, puis par terrain
  - Chaque terrain a sa propre ligne avec ses 12 mois
  - Les anciennes cotisations (sans numéro) sont affichées séparément

#### Page Liste Cotisations (5_📋_Liste_Cotisations.py)

- Nouvelle colonne "Terrain" dans le tableau
- Affiche "n°1", "n°2", etc. ou "Tous" pour les anciennes cotisations

### Import Excel

L'import Excel a été adapté pour gérer les terrains :

- Si le participant a **plusieurs terrains** (> 1), le montant importé est automatiquement divisé en cotisations par terrain
- Si le participant a **1 terrain ou moins**, une seule cotisation est créée avec `numero_terrain = NULL`

### Export Excel

Les exports agrègent automatiquement les cotisations :

- **Rapport (depuis août 2025)** : Somme des montants payés par participant et par mois
- **Export pivot** : Somme des montants par participant (tous terrains confondus)
- Une colonne "nombre_terrains" est incluse pour référence

## Migration

Pour mettre à jour une base de données existante :

```bash
python3 migrate_add_terrain_number.py
```

Cette migration :
- Ajoute la colonne `numero_terrain` à la table `cotisations`
- Les cotisations existantes conservent `numero_terrain = NULL` (tous les terrains)
- Ne supprime aucune donnée

## Exemples d'utilisation

### Cas 1 : Cotisation mensuelle standard

**Objectif** : Générer les cotisations de janvier 2026 pour tous les participants

**Actions** :
1. Aller dans "Cotisations"
2. Ouvrir "🔄 Générer les cotisations mensuelles automatiquement"
3. Sélectionner Janvier 2026
4. Cliquer sur "🚀 Générer"

**Résultat** : Chaque participant reçoit une cotisation de 1000 FCFA par terrain

### Cas 2 : Paiement partiel pour un terrain spécifique

**Objectif** : Monsieur Dupont (3 terrains) paie seulement pour son terrain n°2

**Actions** :
1. Ouvrir "➕ Ajouter une cotisation"
2. Sélectionner "Dupont Jean"
3. Choisir "Terrain n°2"
4. Saisir le montant (ex: 1000 FCFA)
5. Cocher "Déjà payée"
6. Soumettre

**Résultat** : Une seule cotisation pour le terrain n°2 est créée et marquée payée

### Cas 3 : Répartition équitable

**Objectif** : Madame Martin (2 terrains) paie 3000 FCFA pour tous ses terrains

**Actions** :
1. Ouvrir "➕ Ajouter une cotisation"
2. Sélectionner "Martin Sophie"
3. Choisir "Tous les terrains"
4. Saisir 3000 FCFA
5. Cocher "Déjà payée"
6. Soumettre

**Résultat** : 2 cotisations de 1500 FCFA chacune (terrain n°1 et n°2), toutes deux payées

## Notes importantes

- Les anciennes cotisations (sans numéro de terrain) sont conservées et affichées séparément
- Le numéro de terrain commence toujours à 1 et va jusqu'à `nombre_terrains`
- Les statistiques et exports agrègent automatiquement tous les terrains d'un participant
- Pour supprimer une cotisation, elle doit être impayée
