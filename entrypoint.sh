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

if [[ -n $CRON ]]; then
  cron -f -L 2
else  
  ./wait-for-it.sh $db:5432 -- echo "Apply database migrations"
  python manage.py migrate

  # Collect static files
  echo "Collecting static files"
  python manage.py collectstatic

  chmod 775 /var/www/html/pisces/static
  chown www-data:www-data /var/www/html/pisces/static

  #Start server
  echo "Starting server"
  if [[ -n $PROD ]]; then
      apache2ctl -D FOREGROUND
  else
      python manage.py runserver 0.0.0.0:${APPLICATION_PORT}
  fi
fi