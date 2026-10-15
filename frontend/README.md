# stRock

Base vide Vue 3 + TypeScript avec Vite, adaptée aux écrans mobiles.

## Démarrage

```sh
npm install
npm run dev
```

Pour ouvrir le site depuis un mobile connecté au même réseau :

```sh
npm run dev -- --host 0.0.0.0
```

Utiliser sur le mobile l’adresse réseau affichée par Vite.

## Production

```sh
npm run build
npm run preview
```

La commande `build` vérifie TypeScript et génère le site dans `dist/`.

## Fichiers principaux

- `src/App.vue` : page contenant la carte plein écran.
- `src/style.css` : styles globaux fluides et hauteur adaptée aux navigateurs mobiles.
- `index.html` : langue française et viewport mobile sans restriction de zoom.

## Composants PrimeVue

PrimeVue 4 est configuré dans `src/main.ts` avec le thème Aura en mode clair.
Les icônes PrimeIcons sont également disponibles.

Importer les composants nécessaires directement dans chaque composant Vue :

```vue
<script setup lang="ts">
import Button from 'primevue/button'
</script>

<template>
  <Button label="Enregistrer" icon="pi pi-check" />
</template>
```

Pour adapter les mises en page au mobile, utiliser
les styles fluides du projet et les options responsive des composants concernés.

Documentation : https://v4.primevue.org/

## Tailwind CSS

Tailwind est activé via le plugin Vite et importé dans `src/style.css`.
La couche CSS PrimeVue est placée après les styles de base et avant les utilitaires Tailwind.

Exemple de grille responsive :

```html
<div class="grid grid-cols-1 gap-4 p-4 md:grid-cols-2 md:p-8">
  <!-- Contenu -->
</div>
```

## Carte plein écran

La page d’accueil affiche une carte Leaflet avec un fond OpenStreetMap.
Elle occupe toute la fenêtre sur ordinateur et mobile, avec des boutons de zoom
adaptés au tactile. Sa taille se recalcule lors des changements d’orientation
ou de hauteur du navigateur mobile.

Le centre initial et le zoom sont définis dans `src/components/BackgroundMap.vue`.
Le fond de carte nécessite une connexion Internet. L’attribution doit rester visible.
Conditions du serveur de tuiles : https://operations.osmfoundation.org/policies/tiles/

La carte démarre au centre du quartier Saint-Roch à Québec, avec un niveau de
zoom minimum de 16, ajusté à la taille de l’écran pour explorer ses rues. Elle ne demande pas la géolocalisation et ne suit pas
l’utilisateur : les déplacements et le zoom sont contrôlés manuellement.

## Limites de Saint-Roch

Le contour provient du jeu de données **Quartiers**, Ville de Québec,
distribué sur Données Québec sous licence CC BY 4.0 :
https://www.donneesquebec.ca/recherche/dataset/5b1ae6f2-6719-46df-bd2f-e57a7034c917

Le seul quartier Saint-Roch est conservé dans `src/data/saint-roch.json`.
Le dézoom minimum s’adapte à l’écran. Saint-Roch conserve ses couleurs normales ;
les alentours visibles sont affichés en niveaux de gris et assombris pour signaler
la limite du quartier, sans agrandir la carte ni changer les déplacements.
Chaque tuile utilise une seule image : un fond désaturé via CSS et un rendu canvas
en couleurs découpé au contour officiel. Seules les tuiles visibles sont chargées.

Le déplacement est bloqué avant affichage à la frontière du quartier, sans
recentrage après relâchement. Le zoom reste centré et l’inertie est désactivée
pour éviter tout dépassement. L’adaptateur `constrainMovement.ts` utilise
l’événement `predrag` et la position interne Leaflet 1.9 du déplacement en cours.
