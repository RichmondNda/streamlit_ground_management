# Guide pratique : Cotisations avec montants différents par terrain

## Cas d'usage

Vous avez un participant qui possède plusieurs terrains et vous souhaitez enregistrer des cotisations avec des montants différents pour chaque terrain pour le même mois.

### Exemple concret

**Participant :** Jean Dupont (3 terrains)  
**Mois :** Janvier 2026

**Cotisations :**
- Terrain n°1 : 10 FCFA
- Terrain n°2 : 50 FCFA
- Terrain n°3 : 80 FCFA
- **Total : 140 FCFA**

---

## Méthode 1 : Ajout rapide (RECOMMANDÉ) ➕➕

### Étapes :

1. **Ouvrir la page Cotisations** (💰 Cotisations)

2. **Développer la section** : "➕➕ Ajouter des cotisations avec montants différents par terrain"

3. **Sélectionner le participant** : Jean Dupont

4. **Choisir le mois et l'année** : Janvier 2026

5. **Saisir les montants pour chaque terrain** :
   - Terrain n°1 : 10
   - Terrain n°2 : 50
   - Terrain n°3 : 80
   
6. **Vérifier le total** : 140 FCFA s'affiche automatiquement

7. **(Optionnel) Cocher "Déjà payées"** si les cotisations sont déjà réglées

8. **Cliquer sur "Ajouter toutes les cotisations"**

### Résultat :
✅ 3 cotisations créées pour Janvier 2026 :
- Cotisation 1 : Terrain n°1 - 10 FCFA
- Cotisation 2 : Terrain n°2 - 50 FCFA  
- Cotisation 3 : Terrain n°3 - 80 FCFA

---

## Méthode 2 : Ajout individuel ➕

Si vous préférez ajouter les cotisations une par une :

### Étapes :

1. **Ouvrir la section** : "➕ Ajouter une cotisation"

2. **Pour chaque terrain** :
   - Sélectionner le participant : Jean Dupont
   - Choisir le terrain : "Terrain n°1"
   - Saisir le montant : 10 FCFA
   - Cliquer sur "Ajouter la cotisation"
   
3. **Répéter pour les autres terrains** :
   - Terrain n°2 : 50 FCFA
   - Terrain n°3 : 80 FCFA

---

## Visualisation du total

### Dans le tableau annuel

Le tableau des cotisations affiche maintenant :

```
Jean Dupont (3 terrains)
  🏞️ Terrain n°1
    [Jan] [Fév] [Mar] [Avr] [Mai] [Jun] [Jul] [Aoû] [Sep] [Oct] [Nov] [Déc]
     10     -     -     -     -     -     -     -     -     -     -     -
  
  🏞️ Terrain n°2
    [Jan] [Fév] [Mar] [Avr] [Mai] [Jun] [Jul] [Aoû] [Sep] [Oct] [Nov] [Déc]
     50     -     -     -     -     -     -     -     -     -     -     -
  
  🏞️ Terrain n°3
    [Jan] [Fév] [Mar] [Avr] [Mai] [Jun] [Jul] [Aoû] [Sep] [Oct] [Nov] [Déc]
     80     -     -     -     -     -     -     -     -     -     -     -
  
  💰 Total
    [Jan] [Fév] [Mar] [Avr] [Mai] [Jun] [Jul] [Aoû] [Sep] [Oct] [Nov] [Déc]
     140    -     -     -     -     -     -     -     -     -     -     -
```

### Ligne de total

La ligne **"💰 Total"** affiche pour chaque mois :
- **Montant total** de toutes les cotisations du mois
- **Statut** :
  - 🟢 **Vert** : Toutes les cotisations payées (✓ 3/3)
  - 🔴 **Rouge** : Aucune cotisation payée (✗ 0/3)
  - 🟡 **Jaune** : Paiement partiel (⚠ 1/3 - 50 payé)

---

## Dans la page "Liste Cotisations"

Tableau détaillé :

| Nom     | Prénom | Nb Terrains | Terrain | Année | Mois    | Montant  | Statut      |
|---------|--------|-------------|---------|-------|---------|----------|-------------|
| Dupont  | Jean   | 3           | n°1     | 2026  | Janvier | 10 FCFA  | ⏳ Impayée |
| Dupont  | Jean   | 3           | n°2     | 2026  | Janvier | 50 FCFA  | ⏳ Impayée |
| Dupont  | Jean   | 3           | n°3     | 2026  | Janvier | 80 FCFA  | ⏳ Impayée |

**Total pour Janvier 2026 :** 140 FCFA (visible dans les statistiques en filtrant par participant)

---

## Export Excel

Lors de l'export, les montants sont automatiquement **agrégés par participant et par mois** :

| Nom    | Prénom | Nb Terrains | Janvier 2026 | Février 2026 | ... | TOTAL PAYÉ |
|--------|--------|-------------|--------------|--------------|-----|------------|
| Dupont | Jean   | 3           | 140          | -            | ... | 140        |

Si seulement le terrain n°2 est payé (50 FCFA), l'export affichera :
- Colonne "Janvier 2026" : 50 (montant payé)

---

## Cas particuliers

### Terrain avec montant 0

Si vous saisissez 0 FCFA pour un terrain, **aucune cotisation ne sera créée** pour ce terrain.

Exemple :
- Terrain n°1 : 10 FCFA ✅ Créée
- Terrain n°2 : 0 FCFA ❌ Non créée
- Terrain n°3 : 80 FCFA ✅ Créée

**Résultat :** 2 cotisations créées (terrains 1 et 3)

### Cotisation déjà existante

Si une cotisation existe déjà pour un terrain donné et un mois donné, vous obtiendrez une erreur :

```
⚠️ 1 erreur(s) :
  - Terrain n°2: Cette cotisation existe déjà pour ce terrain
```

**Solution :** Supprimez d'abord la cotisation existante (si impayée) ou modifiez-la via "Marquer comme payée".

---

## Avantages de cette méthode

✅ **Rapidité** : Saisir tous les montants en une fois  
✅ **Flexibilité** : Montants différents selon les terrains  
✅ **Visibilité** : Total calculé automatiquement  
✅ **Suivi précis** : Voir quel terrain est payé ou non  
✅ **Paiements partiels** : Payer terrain par terrain  

---

## Exemples réels

### Exemple 1 : Paiement échelonné

Marie Martin (4 terrains) paie progressivement :
- **Janvier :** Terrains 1 et 2 (2000 FCFA chacun)
- **Février :** Terrain 3 (2000 FCFA)
- **Mars :** Terrain 4 (2000 FCFA)

→ Facilité de suivi avec la ligne de total par mois

### Exemple 2 : Tarifs différenciés

Pierre Dubois (2 terrains) avec tarifs différents :
- Terrain n°1 (terrain agricole) : 500 FCFA/mois
- Terrain n°2 (terrain commercial) : 2500 FCFA/mois
- **Total mensuel :** 3000 FCFA

→ Montants personnalisés par terrain

### Exemple 3 : Promotion

Sophie Legrand (3 terrains) bénéficie d'une réduction sur un terrain :
- Terrain n°1 : 1000 FCFA
- Terrain n°2 : 500 FCFA (promotion -50%)
- Terrain n°3 : 1000 FCFA
- **Total :** 2500 FCFA au lieu de 3000 FCFA

---

## Résumé

Cette fonctionnalité vous permet de gérer des cotisations **flexibles et personnalisées** par terrain, avec un **suivi précis** et une **visualisation claire du total** par participant et par mois.
