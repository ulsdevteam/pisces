#!/bin/bash

# Run database migrations
env/bin/python manage.py migrate

# Collect static files
env/bin/python manage.py collectstatic --noinput
