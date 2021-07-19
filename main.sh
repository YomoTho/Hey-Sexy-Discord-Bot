#!/bin/bash

function main()
{
    clear

    if [[ $1 == 'loop' ]]; then
        echo "Server Mode."
        while [ : ]
        do
            reboot_id=$(cat reboot_id)
            echo "" > reboot_id
            python3 scripts/main.py $reboot_id
            # sleep 1
        done
    else
        echo "Normal Mode."
        python3 scripts/main.py
    fi

}

main $@
