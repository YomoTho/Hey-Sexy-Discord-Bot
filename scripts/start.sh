#!/bin/bash

function main()
{
    clear
    while [[ : ]]
    do
        reboot_id=$(cat reboot_id)
        echo "" > reboot_id
        python3 main.py $reboot_id
        sleep 1
    done
}

main