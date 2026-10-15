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
