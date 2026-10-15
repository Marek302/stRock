# 10Books Post API

Cette API est un service de gestion d'annonces de livres pour la plateforme 10Books. Elle permet aux utilisateurs de créer, consulter, supprimer des annonces et de gérer les images associées.

Ce projet est un sous-module de [10books-docker-infrastructure](https://gitlab.com/10books/10books-docker-infrastructure).

## Description Générale

L'API Post gère le cycle de vie des annonces de livres, incluant les informations sur l'état du livre, le prix, l'emplacement, et les images. Elle s'intègre avec Firebase pour l'authentification et utilise une base de données PostgreSQL pour le stockage des données.

## Routes de l'API

### Annonces (Posts)

- `GET /api/v1/posts` : Récupère toutes les annonces avec support pour la pagination et les filtres.
- `POST /api/v1/posts` : Crée une nouvelle annonce (authentification requise).
- `GET /api/v1/posts/{post_id}` : Récupère les détails d'une annonce spécifique par son ID.
- `DELETE /api/v1/posts/{post_id}` : Supprime une annonce (propriétaire uniquement).
- `GET /api/v1/posts/{post_id}/sold-status` : Récupère le statut de vente d'une annonce.
- `PATCH /api/v1/posts/{post_id}/sold` : Marque une annonce comme vendue.
- `GET /api/v1/posts/user/{user_id}` : Récupère toutes les annonces d'un utilisateur spécifique.
- `PATCH /api/v1/posts/user/{user_id}/reputation` : Met à jour la réputation d'un vendeur (réservé aux administrateurs).

### Images

- `PUT /api/v1/images/{image_id}` : Téléverse une image pour un emplacement réservé dans une annonce. Les images sont analysées par un modèle de détection de contenu NSFW ([Marqo/nsfw-image-detection-384](https://huggingface.co/Marqo/nsfw-image-detection-384)) ; si le contenu est jugé inapproprié, l’upload est rejeté (422).
- `GET /api/v1/images/{image_id}` : Récupère le fichier image par son ID.

## Détection de contenu NSFW

L’upload d’images (PUT `/api/v1/images/{image_id}`) est soumis à une détection NSFW basée sur le modèle [Marqo/nsfw-image-detection-384](https://huggingface.co/Marqo/nsfw-image-detection-384). En cas de détection au-dessus du seuil configuré, l’API renvoie **422 Unprocessable Content** avec un message explicite.

Variables d’environnement optionnelles :

- **`NSFW_DETECTION_ENABLED`** : `1` (défaut) pour activer la détection, `0` pour la désactiver.
- **`NSFW_THRESHOLD`** : seuil de probabilité NSFW entre 0 et 1 (défaut : `0.5`). Une image est rejetée si P(NSFW) ≥ ce seuil.

Au premier appel, le modèle est téléchargé depuis le Hugging Face Hub ; un accès réseau est donc nécessaire au démarrage (ou au premier upload).

## Comment lancer le service

### Configuration

1. Copiez le fichier d'exemple des variables d'environnement :
   ```bash
   cp env.example .env
   ```
2. Ajustez les valeurs dans le fichier `.env` selon votre configuration locale.

### Lancement Local

1. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
2. Lancez le serveur de développement :
   ```bash
   fastapi dev main.py
   ```

### Lancement avec Docker

1. Construisez l'image :
   ```bash
   docker build -t 10books-post-api .
   ```
2. Lancez le conteneur :
   ```bash
   docker run -p 8000:8000 --env-file .env 10books-post-api
   ```

Le service sera alors accessible sur `http://localhost:8000`. La documentation Swagger interactive est disponible sur `http://localhost:8000/docs`.

Les réponses GET des posts (détail et listes) incluent `latitude` et `longitude`. Ces champs sont optionnels à la création et valent `null` si absents. La latitude doit être comprise entre -90 et 90 et la longitude entre -180 et 180.

Pour une base existante, ajouter les colonnes avant de démarrer cette version :

```sql
ALTER TABLE post ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;
ALTER TABLE post ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
```
