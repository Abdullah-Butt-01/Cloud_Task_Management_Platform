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

## Phase 1 - Building the Backend API

* 

## Commands Practiced

* git tag <name
* git push origin tag <name
* git tag -d <name
* git push tag --delete <name

## Problems Faced

* Two pipelines ran at the same time, for previous project also

## How I solved

* Added branched in previous project workflow
	- It only contained push trigger and path filter, so when i pushed the current project, this push also triggered

## Key Learnings

* Triggers are based on events:
	- push
	- pull_request
	- tag
* Then you narrow them down using filters
	- branches
	- tags
	- paths
