# Base communautaire Saint-Roch

Le schéma suit `../CONTEXT.md`. Les identités Firebase sont référencées par
`user_id`; aucun mot de passe ni profil utilisateur n'est conservé ici.

`post` contient `id`, `user_id`, `title`, `description`, `content_type`,
`location`, `latitude`, `longitude`, `starts_at`, `ends_at`, `created_at`,
`expires_at` et `closed_at`. `image` référence `post.id` avec suppression en
cascade. Les images sont facultatives. Il n'y a aucun prix, livre, livraison,
acheteur ou réputation dans le nouveau modèle.

- `publication` : fil et carte si les deux coordonnées sont renseignées.
- `event` : coordonnées, début et fin obligatoires; fin après début.
- `urban_alert` : coordonnées obligatoires; fil et carte tant qu'active.
- `safety_alert` : coordonnées obligatoires; carte uniquement.

Les dates utilisent `TIMESTAMPTZ`. Les alertes expirent après deux heures par
défaut (service et trigger PostgreSQL). L'API exclut les alertes expirées ou
clôturées des listes; les données restent disponibles pour consultation directe.
`PATCH /api/v1/posts/{id}/close` permet à l'auteur de clôturer une alerte.
La route `/api/v1/posts/locations` conserve exactement les champs `id`,
`latitude`, `longitude` et exclut les publications sans coordonnées.

## Initialisation

`sql-scripts/01-create.sql` crée directement la base, les tables `post` et
`image`, leurs contraintes, les index et le trigger d'expiration des alertes.
Il est exécuté par `shell-scripts/00-init.sh` à l'initialisation PostgreSQL.
`03-insert.sql` est utilisé en production; `03-insert.test.sql` en mode test.

Les installations de test ajoutent cinq événements explicitement fictifs dans
des lieux réels de Saint-Roch. Pour les ajouter manuellement :

```sh
PGTZ=America/Toronto psql -v ON_ERROR_STOP=1 -d NOM_BASE -f post-db/sql-scripts/community-demo.sql
```

Les coordonnées de démonstration sont approximatives. Les événements n'impliquent
aucune affiliation avec les lieux. Les dates sont calculées à l'insertion et les
identifiants fixes évitent les doublons.

## Vérification ciblée

Depuis `post-backend`, avec ses dépendances installées :

```sh
CONNECTION_STR=postgresql://test:test@localhost/test python -m unittest discover -s tests/community -v
```

Ces tests utilisent SQLite pour les contrats HTTP et la logique métier. Les
scripts SQL et le trigger d'expiration doivent aussi être vérifiés sur PostgreSQL.
La suite historique des annonces de livres doit être remplacée progressivement.

Pour vérifier les routes contre le schéma SQL réel, initialiser une base PostgreSQL
**de test dédiée** avec `01-create.sql`, puis lancer depuis `post-backend` :

```sh
CONNECTION_STR="$STROCK_TEST_DATABASE_URL" \
PHOTO_SAVE_ROOT=/tmp/strock-test-images NSFW_DETECTION_ENABLED=0 \
python -m unittest discover -s tests/community -v
```

`STROCK_TEST_DATABASE_URL` doit contenir une URL SQLAlchemy PostgreSQL et être
exportée. Les tests PostgreSQL utilisent les droits du rôle applicatif, sans
`create_all`; chaque test annule ses écritures. Ils couvrent les colonnes du
schéma, création, lecture, recherche, pagination, validation des événements,
expiration SQL, visibilité des alertes, clôture, images et suppression.
Firebase et l'appel externe à la messagerie sont simulés dans ces tests.
