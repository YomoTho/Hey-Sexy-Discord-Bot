#!/bin/bash

function rw() 
{
	while read line
	do 
		code=$line && break
    done < $1
    echo $code
}

function p() 
{
    ([[ $1 == "r" ]] && echo '../data/reboot_id') || (echo 'reboot_id')
}

function cleanup() 
{
    [[ $1 == "-d" ]] && echo "Cleaning up..."
    echo > $(p)
    echo > $(p "r")
    [[ $1 == "-d" ]] && echo "Done!"
}

function main() 
{
    if [[ $1 == "-s" ]]; then
        cleanup $1
        echo "Server Mode"
        while [[ : ]]
        do
            python3 main.py 1 2> $(p)
            echo > $(p "r")
            code=$(rw $(p))
            echo $code > $(p "r")
            echo "Rebooting..."
            sleep 1
        done
        cleanup $1
    else
        cleanup $1
        echo "Normal Mode."
        while [[ : ]]
        do
            python3 main.py 1 2> $(p) && break
            echo > $(p "r")
            code=$(rw $(p))
            [[ $(echo $code | cut -c1-3) != "1::" ]] && break
            echo $code > $(p "r")
            echo "Rebooting..."
        done
        cleanup $1
    fi
}

clear
main $@