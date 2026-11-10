#!/bin/sh
# Simulation du firmware sur PC (aucun matériel requis) : ./run.sh
cd "$(dirname "$0")" && g++ -std=c++17 -O1 -Wall -Istubs -I../../src sim.cpp -o /tmp/treuil_sim && /tmp/treuil_sim
