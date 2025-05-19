#!/bin/bash

echo -e "List the mosaic series that have the word Global in their name"
planet mosaics series list --name-contains=Global | jq .[].name

echo -e "\nWhat is the latest mosaic in the series named Global Monthly, with output indented"
planet mosaics series list-mosaics "Global Monthly" --latest --pretty

echo -e "\nHow many quads are in the mosaic with this ID (name also accepted!)?"
planet mosaics search 09462e5a-2af0-4de3-a710-e9010d8d4e58 --bbox=-100,40,-100,40.1 | jq .[].id

echo -e "\nWhat scenes contributed to this quad in the mosaic with this ID (name also accepted)?"
planet mosaics contributions 09462e5a-2af0-4de3-a710-e9010d8d4e58 455-1273

echo -e "\nDownload them to a directory named quads!"
planet mosaics download 09462e5a-2af0-4de3-a710-e9010d8d4e58 --bbox=-100,40,-100,40.1 --output-dir=quads