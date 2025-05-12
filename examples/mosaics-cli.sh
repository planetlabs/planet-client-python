#!/bin/bash

echo -e "Global Basemap Series"
planet mosaics series list --name-contains=Global | jq .[].name

echo -e "\nLatest Global Monthly"
planet mosaics series list-mosaics "Global Monthly" --latest --pretty

echo -e "\nHow Many Quads?"
planet mosaics search 09462e5a-2af0-4de3-a710-e9010d8d4e58 --bbox=-100,40,-100,40.1

echo -e "\nWhat Scenes Contributed to Quad?"
planet mosaics contributions 09462e5a-2af0-4de3-a710-e9010d8d4e58 455-1273

echo -e "\nDownload Them!"
planet mosaics download 09462e5a-2af0-4de3-a710-e9010d8d4e58 --bbox=-100,40,-100,40.1 --output-dir=quads