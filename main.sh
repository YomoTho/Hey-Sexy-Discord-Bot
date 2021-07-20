#!/bin/bash

function main()
{
    clear

    if [[ $1 == 'loop' || $1 == '-l' ]]; then
        echo "Always looping."
        while [[ : ]]
        do
            reboot_id=$(cat reboot_id)
            /dev/null > reboot_id
            python3 scripts/main.py $reboot_id
            sleep 0.5
        done
    elif [[ $1 == 'errors' || $1 == '-e' ]]; then
        echo "Show errors only"

        python3 scripts/main.py 1> /dev/null 
    else
        echo "Normal Mode."
        python3 scripts/main.py
    fi

}

main $@
