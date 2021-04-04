#! /bin/bash

clear; python3 main.py
exit_code=$?

while [ true ]; do
    if [[ $exit_code -eq 69 ]]; then
        echo "Rebooting..."
        python3 main.py $exit_code
        exit_code=$?
    else
        break
    fi
done

