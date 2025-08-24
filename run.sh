#!/bin/bash

echo "== LightIoT Simulation Runner =="

echo "Choose scenario:"
echo "1. Secure"
echo "2. NoSecurity"
echo "3. Replay Attack"
echo "4. 20 Nodes"
echo "5. 50 Nodes"
read -p "Enter choice [1-5]: " opt

echo "Run with GUI? [y/n]"
read gui

case $opt in
    1) CONFIG="SecureMode";;
    2) CONFIG="NoSecurityMode";;
    3) CONFIG="ReplayAttackMode";;
    4) CONFIG="Scale20";;
    5) CONFIG="Scale50";;
    *) echo "Invalid option"; exit 1;;
esac

if [[ "$gui" == "y" || "$gui" == "Y" ]]; then
    ENV="-u Qtenv"
else
    ENV="-u Cmdenv"
fi

echo "Running simulation with config: $CONFIG in environment: $ENV"
./LightIoTSimulation $ENV -c $CONFIG -n . -f omnetpp.ini