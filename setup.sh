#!/bin/bash

function pip_installs()
{
    pip install discord.py
    pip install matplotlib
    pip install asyncpraw
    pip install pytz
    pip install python-dotenv
    pip install aioconsole
    pip install BeautifulSoup4
}


function set_env()
{
    echo "Creating .env..."

    touch .env

    echo "TOKEN=
CLIENT_ID=
CLIENT_SECRET=
USERNAME=
PASSWORD=" > .env
}


function data()
{
    (python3.9 setup_config.py) && ( $(ls .env >> /dev/null 2>&1) && echo ".env already exists" ) || set_env
}


read -p "Do you want to continue? (Y/N): " YN

if [[ $YN == "y" || $YN == "Y" ]]; then
    pip_installs
    data
else
    echo "Nope."
fi

echo "Done."
