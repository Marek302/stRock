#!/bin/bash

docker compose down

docker rmi books-api:latest 2>/dev/null

docker rmi listing-api:latest 2>/dev/null

docker rmi messaging-api:latest 2>/dev/null

docker rmi firebase-admin-management-api:latest 2>/dev/null

docker rmi nginx:latest 2>/dev/null
