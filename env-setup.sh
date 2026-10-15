#!/bin/bash

find . -type f -name "env.example" -execdir cp {} .env \;
