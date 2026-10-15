## Fonctions

- **beforecreated** : custom claims à la création d'un utilisateur Auth.
- **onUserCreated** : crée le document Firestore `users/{uid}` (vendor_reputation, preferences).
- **onVendorReviewWrite** : recalcule `users/{vendorId}.vendor_reputation` quand une review est créée/modifiée/supprimée.
- **onUserProfileUpdate** : quand `users/{uid}.vendor_reputation` change, appelle le listing-api pour mettre à jour `seller_rep` sur tous les listings du vendeur.
- **validateAddress** : fonction callable HTTPS qui valide et normalise une adresse via Google Geocoding.

**Filtre par réputation (listings)** : le filtre « min réputation / étoiles » utilise **uniquement** `vendor_reputation` (réputation en tant que vendeur). La `buyer_reputation` n’est pas utilisée pour ce filtre.

## Configuration

Pour **onUserProfileUpdate**, ces secrets Firebase doivent être définis :

- `LISTING_API_URL` (ex. `https://listing-api.example.com`)
- `INTERNAL_API_SECRET`

Pour **validateAddress**, définissez :

- `GOOGLE_MAPS_API_KEY`

## Déploiement

Depuis la racine de `10books-docker-infrastructure` :

```bash
cd firebase-functions
npm install
firebase functions:secrets:set LISTING_API_URL
firebase functions:secrets:set INTERNAL_API_SECRET
firebase functions:secrets:set GOOGLE_MAPS_API_KEY
cd ..
firebase deploy --only functions
```



Test:

Ça fonctionnait quand j'ai créé un compte et que je suis allé décodé le jwt puis allé checké les permissions
