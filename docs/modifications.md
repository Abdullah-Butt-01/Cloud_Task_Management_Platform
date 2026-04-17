# Small modifications to test multiple things

# API and Routes

## 1.1 : Add a new route

* Moved all the routes from main flask app to routes/tasks
* Modified the flask app, routes file and models file
* Added a new route /task/status/<job_id
* Tested the new route

## 1.2 : Dynamic Job Parameters

* /task/5?delay=10
* To pass arguments to background_job 
* Modified route /task/<int:n
* Modified background_job in worker script
* Tested it

## 1.3 : Track Task Status in Database

* Modified models/task.py and added status, result
* Modified route task/n in routes file
* Error DB initialization taking time but app initialized and connecting to DB
* Added wait script in main.py to wait for db to initialize first

# Models and Database

## 2.1 : Add a New Model

* Created a new file app/models/user.py
* Created a new table with attributes: id, name, username
* Checked manually using: docker compose exec api python
* Also can be checked directly: docker compose exec db psql -U postgres -d your_dbname 
	- \l : to check databases
	- \c name : select database
	- \dt : to check tables
	- SELECT * FROM table_name

## 2.2 : Connect Task to User

* Added foreign_key and connecting Task and User
* Rebuilding the system
* Error: column does not exist -> Python model changed but db schema did not update
* Rebuilding using: docker compose down -v

## 2.3 : Assign Tasks to Users via API

* Modified route task/n to assign tasks to user
* Tested by calling the API
* Verified using Python shell
	- u = User.query.get(1)
	- u.tasks

# Background worker and Redis

## 3.1 : Add a New Background Job

* Created a new job function 'process_report' in jobs.py
* Modifed flask route to enqueue this job
* Tested the system

## 3.2 : Job Failure Simulation and Proper Handling

* Moved background_job from worker to jobs
* Modified background_job, added try-except logic
* Handled circular imports problem
* Changed the sequence of jobs in routes file from ProRep, BacJob -> BacJob, ProRep
* Tested the system

## 3.3 : Queue Behavior (Async in Action)

* Fired multiple requests with long delay
* Checked in another terminal using worker logs in real time
	- docker logs -f task-worker
* Sent multiple requests at once
	- for i in {1..10};do  curl "http://localhost:5000/task/$i?user_id=1&delay=10" & done

## 3.4 : Multiple Workers (Parallel Processing)

* Modified docker-compose, duplicated worker 
* Named them worker 1 and 2
* Rebuilt and run the system
* Checked logs from two separate 
* Redis distributes jobs automatically, we did not write any load-balancing code

# Docker and Compose

## 4.1 : Ports + Networking

* Docker-compose creates a virtual LAN, where services talk using names
* Use names, not localhost
	- local host = inside container itself
	- redis = other service in the same network
* Checked connectivity inside container
	- docker exec -it task-api sh
	- ping redis - Error because most docker images like python-slim are minimal
	- Used already available service
		- python
		- import socket
		- socket.gethostbyname("redis")

## 4.2 : Environment Varaibles and Config Layers

* Understand how same code behaves differently in dev, test, and production
* Code stays same, config changes behavior
	- Code = logic
	- Env = behavior
* Configuration: settings that control how a system behaves
* Environment Variables: external values given to a program at runtime
* Where config live:
	- Dockerfile (Build-time)
	- docker-compose (runtime)
	- .env file (environment variables)
* Why need .env? Why not just put everything in code
	- Different envrionments: if values are in code, you keep editing code again. Risk of breaking things. Messy, unsafe
	- Security: .env not uploaded (ignore it in git), you can put passwords and secret info there.

* What I did
	- Created .env file
	- Added .env in docker-compose in containers
	- Changed configuratiuon method from host+port to url

## 4.3 : Docker Volumes (Data Persistence)

* Containers are temporary, data lost when containers stop
* Volumes save data outside containers
* Added and declared volume in db service

## 4.4 : Scaling workers properly instead of manually

* Instead of manual duplication of workers, use flag during build
	- docker compose up --build -d --scale worker=n

# Logging and Observability

## 5.1 : Logging and Observability

* Added logging in API routes
* Added logging in worker jobs
* Ran the system and observed using logs


## Completed! Date: 12/04/2026 
