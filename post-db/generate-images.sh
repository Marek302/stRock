#!/bin/bash

# Configuration
SQL_FILE="./listing-db/sql-scripts/02-insert.test.sql"
OUTPUT_DIR="./10books-listing-api/dev_images" 

if [ ! -f "$SQL_FILE" ]; then
    echo "Error: SQL file not found at $SQL_FILE"
    exit 1
fi

echo "--- Starting Image Generation ---"

# Extraction des chemins : capture tout ce qui commence par / suivi de caractères alphanumériques, tirets ou slashs
grep -oE "/[a-zA-Z0-9/-]+" "$SQL_FILE" | grep -vE "^/($|bin|dev|etc|home|lib|usr|proc)" | while read -r db_path; do
    
    local_file="${OUTPUT_DIR}${db_path}"
    local_dir=$(dirname "$local_file")

    mkdir -p "$local_dir"

    filename=$(basename "$db_path")
    
    # Dimensions aléatoires
    WIDTH=1080
    HEIGHT=1920
    if [[ $((RANDOM % 2)) -eq 0 ]]; then
        WIDTH=1920
        HEIGHT=1080
    fi

    # Utilisation de Picsum avec le hash de l'image comme seed
    image_url="https://picsum.photos/seed/${filename}/${WIDTH}/${HEIGHT}"

    echo "Downloading photo for: $db_path"
    curl -s -L "$image_url" -o "$local_file"

done

echo "--- Done! Images generated in $OUTPUT_DIR ---"