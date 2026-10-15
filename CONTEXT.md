# Contexte du Projet : Plateforme Sociale Saint-Roch

## 1. Vision et Objectif
Application web communautaire destinée au quartier Saint-Roch (Québec). L'objectif est d'informer et de connecter les résidents, les entreprises locales et les travailleurs du quartier autour des actualités locales, des événements et de la sécurité urbaine en temps réel.

## 2. Utilisateurs et Authentification
- **Cibles :** Résidents, travailleurs et entreprises de Saint-Roch (droits standards identiques pour le MVP).
- **Authentification :** Gérée à l'externe via **Firebase Auth**.
- **Permissions :**
  - **Visiteurs (non connectés) :** Accès en lecture seule à la Carte et au fil des Publications.
  - **Utilisateurs connectés :** Création de contenu (publications, événements, alertes) et accès à la Messagerie.

## 3. Typologie des Contenus et Visibilité
Tous les contenus sont gérés par le microservice `Post API` et se divisent en 4 catégories :

1. **Événement** (fête de quartier, spectacle, promotion locale)
   - *Visibilité :* Carte + Page Publications.
   - *Spécificité :* Comprend une date/heure de début et de fin.
2. **Publication générale** (objet perdu, entraide, question, annonce)
   - *Visibilité :* Page Publications + Carte (optionnel, seulement si géolocalisé).
3. **Alerte info / Urbaine** (rue barrée, travaux, bris d'aqueduc, panne)
   - *Visibilité :* Carte + Page Publications.
4. **Alerte de sécurité / Danger** (individu agressif, incident en cours, intervention)
   - *Visibilité :* **Carte UNIQUEMENT** (exclue du fil des publications pour ne pas le polluer).
   - *Spécificité :* Géolocalisation obligatoire.

### Cycle de vie des alertes
- **Expiration automatique :** Durée de vie par défaut de **2 heures** après la création.
- **Clôture manuelle :** Le créateur de l'alerte peut la désactiver/clôturer manuellement avant l'expiration des 2 heures.

## 4. Structure de l'Application Web (Frontend)
L'interface est divisée en 3 sections principales :
- **Carte :** Visualisation interactive du quartier Saint-Roch affichant les alertes actives (sécurité et urbaines), les événements et les publications géolocalisées.
- **Publications :** Fil d'actualité permettant de visualiser et de rechercher les publications, événements et alertes urbaines par **mots-clés**. Aucun commentaire public ; l'interaction se fait en contactant l'auteur. *(Évolution future : système d'upvotes).*
- **Messages :** Interface regroupant toutes les conversations privées de l'utilisateur connecté.

## 5. Architecture Backend (Microservices)
- **Post API :**
  - Gère le CRUD de toutes les catégories de contenus (Publications, Événements, Alertes urbaines, Alertes de sécurité).
  - Gère la logique de visibilité (filtrage Carte vs Fil de publications), la recherche par mots-clés et l'expiration automatique (TTL de 2h) ou manuelle des alertes.
- **Messaging API :**
  - Gère la messagerie privée **1-à-1** (style Marketplace).
  - Chaque conversation est liée à une publication spécifique, permettant à un utilisateur intéressé de discuter en privé avec le créateur de la publication.
