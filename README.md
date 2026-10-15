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

- `src/App.vue` : page vide à compléter.
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

La page initiale reste vide. Pour adapter les mises en page au mobile, utiliser
les styles fluides du projet et les options responsive des composants concernés.

Documentation : https://v4.primevue.org/
