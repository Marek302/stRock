#!/bin/bash

if [ ! -f "serviceAccountKey.json" ]; then
    echo "Erreur: serviceAccount.json introuvable."
    exit 1
fi

JSON_STRING=$(jq -c . serviceAccountKey.json)

echo "" >> .env
echo "FIREBASE_SERVICE_ACCOUNT_JSON='$JSON_STRING'" >> .env

echo "Clé injectée avec succès dans .env"
