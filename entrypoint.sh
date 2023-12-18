#!/bin/bash

# Apply database migrations
if [ ! -f manage.py ]; then
  cd pisces
fi

# Create config.py if it doesn't exist
if [ ! -f pisces/config.py ]; then
    echo "Creating config file"
    if [[ -n $PROD ]]; then
      envsubst < pisces/config.py.deploy > pisces/config.py
    else
      cp pisces/config.py.example pisces/config.py
    fi
fi

./wait-for-it.sh $db:5432 -- echo "Apply database migrations"
python manage.py migrate

#Start server
echo "Starting server"
python manage.py runserver 0.0.0.0:${APPLICATION_PORT}
