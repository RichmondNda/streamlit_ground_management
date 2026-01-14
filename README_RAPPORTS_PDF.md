# Génération de Rapports PDF

## Vue d'ensemble

La fonctionnalité de génération de rapports PDF permet de créer des documents professionnels pour chaque participant, contenant un résumé complet de leurs cotisations et de leur évolution par rapport aux attentes.

## Fonctionnalités du rapport PDF

Le rapport généré contient les sections suivantes :

### 1. En-tête
- Titre du rapport
- Date de génération
- Logo/Branding MEDD

### 2. Informations du participant
- Nom et prénom
- Nombre de terrains
- Téléphone
- Email
- Coût total des terrains (nombre de terrains × 2 500 000 FCFA)

### 3. Résumé financier
- Nombre total de cotisations
- Cotisations payées (avec taux en %)
- Cotisations impayées
- Montant attendu total
- Montant encaissé
- Reste à payer (avec mise en évidence)

### 4. Détail des cotisations
Les cotisations sont organisées par année, puis par mois et par terrain, avec :
- Nom du mois
- Numéro du terrain (ou "Tous" pour les anciennes cotisations globales)
- Montant de la cotisation
- Statut (✓ Payée / ✗ Impayée)
- Date de paiement (si applicable)

**Codes couleur :**
- Vert : Cotisations payées
- Rouge : Cotisations impayées

### 5. Pied de page
- Date et heure de génération
- Mention "Gestion des cotisations MEDD"

## Comment utiliser

### Depuis la page Participants

1. Accédez à la page "👤 Participants"
2. Dans la liste des participants, repérez la colonne avec l'icône 📄
3. Cliquez sur le bouton 📄 pour le participant souhaité
4. Le PDF se télécharge automatiquement avec le nom `rapport_NOM_PRENOM.pdf`

### Depuis la page Cotisations

1. Accédez à la page "💰 Cotisations"
2. En haut du tableau, développez la section "📄 Générer un rapport PDF pour un participant"
3. Sélectionnez le participant dans la liste déroulante
4. Cliquez sur "📥 Générer et télécharger le rapport PDF"
5. Un bouton de téléchargement apparaît pour récupérer le fichier

## Cas d'usage

### Communication avec les participants
Le rapport peut être :
- Envoyé par email aux participants pour les tenir informés
- Imprimé et remis en main propre lors des réunions
- Utilisé comme justificatif de paiement

### Suivi interne
- Facilite la revue des dossiers individuels
- Permet d'identifier rapidement les retards de paiement
- Aide à préparer les relances

### Documentation officielle
- Sert de preuve des montants payés
- Peut être utilisé pour les audits
- Archive l'historique des transactions

## Format technique

- **Type de fichier :** PDF (Portable Document Format)
- **Taille moyenne :** 4-10 KB (selon le nombre de cotisations)
- **Bibliothèque utilisée :** ReportLab
- **Format de page :** A4
- **Marges :** 2 cm sur tous les côtés

## Personnalisation future

Le module `generate_report_pdf.py` peut être facilement personnalisé pour :
- Ajouter un logo de l'organisation
- Modifier les couleurs et le style
- Inclure des graphiques d'évolution
- Ajouter des commentaires ou notes
- Créer des rapports groupés pour plusieurs participants
