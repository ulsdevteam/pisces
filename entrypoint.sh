#!/bin/bash

# Apply database migrations
if [ ! -f manage.py ]; then
  cd pisces
fi

# Create config.py if it doesn't exist
if [ ! -f pisces/config.py ]; then
    echo "Creating config file"
    cp pisces/config.py.example pisces/config.py
fi

./wait-for-it.sh db:5432 -- echo "Apply database migrations"
python manage.py migrate

#Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:8007

#Start cron tasks
#env >> /etc/environment
#exec "cron -f"
