#!/bin/bash

WORKDIR=/tmp/scripts
FILE=$WORKDIR'/*.sql'

sed -i "s/{{DB_USER}}/$DB_USER/g" $FILE

sed -i "s/{{DB_PASSWORD}}/$DB_PASSWORD/g" $FILE

sed -i "s/{{DB_NAME}}/$DB_NAME/g" $FILE

sed -i "s/{{RELEASES_DB_USER}}/$RELEASES_DB_USER/g" $FILE

sed -i "s/{{RELEASES_DB_PASSWORD}}/$RELEASES_DB_PASSWORD/g" $FILE

sed -i "s/{{RELEASES_DB_NAME}}/$RELEASES_DB_NAME/g" $FILE

if [[ -n "$PHOTO_SAVE_ROOT" ]] && [[ -d "/tmp/images" ]]; then
  echo "Copying images to $PHOTO_SAVE_ROOT ..."
  mkdir -p "$PHOTO_SAVE_ROOT"
  cp -r /tmp/images/* "$PHOTO_SAVE_ROOT/"
fi

if [[ "${ENVIRONMENT:-}" == "TEST" ]]; then
  FILES=(
    "$WORKDIR/01-create.sql"
    "$WORKDIR/02-create-releases.sql"
    "$WORKDIR/03-insert.test.sql"
  )
else
  FILES=(
    "$WORKDIR/01-create.sql"
    "$WORKDIR/02-create-releases.sql"
    "$WORKDIR/03-insert.sql"
    )
fi

for file in $(printf "%s\n" "${FILES[@]}" | sort); do
  echo "Running $file"
  psql -U postgres -d postgres -f "$file"
done
