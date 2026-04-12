# Project: Cloud Task Management Platform

## Objective

* Create a Task Management System where users can:
	- sign up
	- login
	- create tasks
	- list tasks
	- delete tasks
* Infrastructure includes:
	- API service
	- PostgreSQL database
	- Redis cache
	- Reverse Proxy
	- CI/CD pipeline
	- auto deployement

# Phase 1 - Building the Backend API
 
## What I did

* Created folder structure
* Created Virual Environment
* Creating .gitignore file
* Installed dependencies
* Freezed dependencies into requirements file
* Created flask app and added database
* After updating files, app ran but error occured -> Database issue
* Modified _ init _.py file and updated all files
* Working

## Problems faced

* Error while installing dependencies
* Error while running app locally
* Error when running /tasks on web -> PostgreSQL not installed

## How I solved

* Upgraded pip
* Created empty file in app/ and updated the files 
* Installed PostgreSQL, created database and tested locally

## Commands Practiced

* python3 -m venv venv 
	- source venv/bin/activate
* pip freeze > requirements.txt

## Key Learnings

* Routes folder contains API endpoints
* Models folder defines database structure
* Package: folder containing modules 
	- _ init _.py tells python to treat this folder as package
		- app/ -> package
		- models -> subpackage
		- tasks.py -> module
		- tasks_bp -> class

# Phase 2 - Containerize the Flask API

## What I did

* Created Dockerfile to docerize the flask app
* Created image and tested locally

## Problems faced

* When running container, it immidiately stopped, giving error 'SQLAlchemy OperationalError: connection refused'

## How I solved

* The app tried to connect to PostgreSQL inside the same container which does not exist there
	- DB is in host machine
	- Containers are isolated environments
	* The Next Phase will automatically fix this (Docker Compose)

## Key Learnings

* Containers are isolated environments. They don't see local machine unless explicitly connected

# Phase 3 - Multi-Container System

## What I did

* Modified flask app to add redis connection
* Created docker-compose file
* Ran the system
* System working
	- api
	- PostgreSQL
	- redis

## Problems faced

* Two errors:
	- Wrong Identation
	- Variable name error 

## How I solved

* Corrected:
	- Identation
	- Variable name

## Key Learnings

* InternalServerError (500): App running but code crashed
* Why needed redis if PostgreSQL there:
	- PostgreSQL: permanent storage (slow)
	- Redis: temporary storage (very fast)
	- used in caching, counters and sessions
* Dokcer-compose purpose: define and run multiple containers as one system

# Phase 4 - Background Worker

## Commands practiced

* docker compose exec api bash - running python inside container


## What I did

* Added rq inside requirements.txt, rq: redis queue
* Created worker script and updated flask app
* Added worker service in docker compose
* 

## Problems faced

* When running the system, import error, ModuleNotFound
* Worker script was not working, name connection is not defined
* Route was not working, route defined after return statement
* Queue working but keyError

## How I solved

* Removed the Connection class since it was used in older versions
* Removed the connection line from worker script 
* Moved return statement after route
* Updated dokcer compose to use worker script as module

## Key Learnings

* Why we needed worker?
	- The worker does heavy/slow work in the background
	- If more tasks added, they pushed to queue and user gets a response
	- Without worker, the user must wait for the current process to be done first, which is slow (bad UX design)

# Phase 5 - CI/CD pipelining

## What I did

* Created folder structure for CI
* Updated Dockerfile for clean auromated workflow
* Created workflow file 

## Problems faced

* CI failed: Incorrect user name or password

## How I solved

* In secrets, enter DockerHub username and password


# Phase 6 - Continuous Deployement

## Commands Practiced

* git commit --allow-empty -m ""

## What I did

* Due to local VM, not accesible by GitHub Actions. I need real server on the internet. I will do it later.

