#!/bin/sh

login=$(echo "sandra")
password=$(echo "Password!")
bloodhound-python -d megacorp.local  -u "$login" -p "$password" -c all -ns 10.10.10.30
