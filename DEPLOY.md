# 🐳 Guide de Déploiement Docker

## 📋 Prérequis

- Docker installé (version 20.10+)
- Docker Compose installé (version 2.0+)

## 🚀 Déploiement rapide

### Option 1 : Avec Docker Compose (Recommandé)

```bash
# Build et démarrer l'application
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter l'application
docker-compose down
```

### Option 2 : Avec Docker seul

```bash
# Build l'image
docker build -t terrain-management .

# Lancer le conteneur
docker run -d \
  --name terrain-management \
  -p 8501:8501 \
  -v $(pwd)/database.db:/app/database.db \
  -v $(pwd)/backups:/app/backups \
  -v $(pwd)/users.json:/app/users.json \
  terrain-management

# Voir les logs
docker logs -f terrain-management

# Arrêter le conteneur
docker stop terrain-management
docker rm terrain-management
```

## 🌐 Accès à l'application

Une fois démarrée, l'application est accessible à :
- **Local** : http://localhost:8501
- **Réseau** : http://[IP-du-serveur]:8501

## 💾 Persistance des données

Les données sont persistées via des volumes Docker :
- `database.db` : Base de données SQLite
- `backups/` : Dossier des sauvegardes
- `users.json` : Fichier des utilisateurs

## 🔧 Configuration avancée

### Changer le port

Dans `docker-compose.yml`, modifier :
```yaml
ports:
  - "3000:8501"  # Utiliser le port 3000 au lieu de 8501
```

### Variables d'environnement

Ajouter dans `docker-compose.yml` :
```yaml
environment:
  - TZ=Africa/Douala
  - STREAMLIT_THEME_PRIMARY_COLOR="#fc6b03"
```

## 🔄 Mise à jour de l'application

```bash
# Arrêter l'application
docker-compose down

# Récupérer les dernières modifications
git pull

# Rebuild et redémarrer
docker-compose up -d --build
```

## 🐛 Dépannage

### Vérifier les logs
```bash
docker-compose logs -f
```

### Entrer dans le conteneur
```bash
docker exec -it terrain-management-app bash
```

### Nettoyer les ressources Docker
```bash
docker system prune -a
```

## 📊 Monitoring

Vérifier la santé du conteneur :
```bash
docker ps
docker inspect terrain-management-app
```

## 🔐 Sécurité

Pour la production :
1. Configurer un reverse proxy (Nginx/Traefik)
2. Activer HTTPS avec Let's Encrypt
3. Limiter l'accès par IP si nécessaire
4. Sauvegarder régulièrement `database.db`

## 📝 Notes

- La base de données SQLite est stockée en volume pour la persistance
- Les backups sont automatiquement créés au démarrage
- L'application redémarre automatiquement en cas d'erreur
