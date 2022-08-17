# pisces
A service for fetching, merging and transforming data for discovery.

pisces is part of [Project Electron](https://github.com/RockefellerArchiveCenter/project_electron), an initiative to build sustainable, open and user-centered infrastructure for the archival management of digital records at the [Rockefeller Archive Center](http://rockarch.org/).

[![Build Status](https://travis-ci.org/RockefellerArchiveCenter/pisces.svg?branch=base)](https://travis-ci.org/RockefellerArchiveCenter/pisces)

## Setup
Install [git](https://git-scm.com/) and clone the repository

    $ git clone https://github.com/RockefellerArchiveCenter/pisces.git

Install [Docker](https://store.docker.com/search?type=edition&offering=community) and run docker-compose from the root directory

    $ cd pisces
    $ docker-compose up

Once the application starts successfully, you should be able to access the application in your browser at `http://localhost:8007`

When you're done, shut down docker-compose

    $ docker-compose down

Or, if you want to remove all data

    $ docker-compose down -v

## Development
This repository contains a configuration file for git [pre-commit](https://pre-commit.com/) hooks which help ensure that code is linted before it is checked into version control. It is strongly recommended that you install these hooks locally by installing pre-commit and running `pre-commit install`.

## Configuring
Pisces configurations are stored in `/pisces/config.py`. This file is excluded from version control, and you will need to update this file with values for your local instance.

The first time the container is started, the example config file (`/pisces/config.py.example`) will be copied to create the config file if it doesn't already exist.

## Services
pisces has three main sets of services, all of which are exposed via HTTP endpoints (see [Routes](#routes) section below):

* Fetch data from data sources
* Merge data from different sources into a unified SourceData object
* Transform source data into target data

![Pisces diagram](pisces-services.png)

### Routes

| Method | URL | Parameters | Response  | Behavior  |
|--------|-----|---|---|---|
|GET, PUT, POST, DELETE|/fetches/||200|Returns data about FetchRun routines|
|POST|/fetch/archivesspace/updates|`object_type` (required) - target object type, one of `resources`, `objects`, `subjects`, `agents`|200|Fetches updated data from ArchivesSpace|
|POST|/fetch/archivesspace/deletes|`object_type` (required) - target object type, one of `resources`, `objects`, `subjects`, `agents`|200|Fetches deleted data from ArchivesSpace|
|POST|/fetch/cartographer/updates|`object_type` (required) - target object type, one of `arrangement_map`|200|Fetches updated data from Cartographer|
|POST|/fetch/cartographer/deletes|`object_type` (required) - target object type, one of `arrangement_map`|200|Fetches deleted data from Cartographer|
|POST|/transform/||200|Transforms data|
|POST|/merge/||200|Merges data|
|GET|/status||200|Return the status of the service|
|GET|/schema.json||200|Returns the OpenAPI schema for this service|

### Custom JSON Schemas

This service depends on JSON schemas defined for your archival data.  [Rockefeller Archive Center's schemas](https://github.com/RockefellerArchiveCenter/rac_schemas) can be used as a basis for your schemas.  An easy way to incorporate your own schemas is to fork Rockefeller Archive Center's repository, clone it into this directory under the rac-schema folder, and edit the requirements.in/requirements.txt to use this local repository.

For example:
```
git clone https://github.com/ulsdevteam/rac_schemas rac-schemas
sed 's/rac-schemas.*/.\/rac-schemas/' -i requirements.in
sed 's/rac-schemas.*/.\/rac-schemas/' -i requirements.txt
```

## License
This code is released under an [MIT License](LICENSE).
