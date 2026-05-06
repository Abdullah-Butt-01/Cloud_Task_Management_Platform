# Polishing Project 

## Started! Date: 12/04/2024

## 1.1 : Clean Task Status API

* Modified task/n and tasks, added if-else condition
* Used GET method to take response
	
## 1.2 : Standardize API response

* Until now, API endpoints return different formats
* Created functions successResponse(), errorResponse() in app/utils/response.py
* Created a serialize function to_dict() inside app/model/task.py
* Used standard response in /tasks, /task/n

## 2.1 Retry Failed Jobs (Fault Tolerence)

* Failure happens due to:
	- network issues
	- DB connection drops
	- temporary bugs
* Updated model/task and added a new column retry_count
* Updated worker job logic, added retry upto 3 times if failed
* Incorporated logging for visibility

## 2.2 : Prevent Stucked Tasks (No infinite started)

* Tasks can stuck with status "started" due to temporary errors, which can lead to confusion
	- worker crashes
	- container restarts
* Every task must end as finished or failed
* Added a new colum "started_at" in the Task model for timestamp
* Modified worker, added timestamp commit
* Created a new fucntion stale_tasks() in /utils/taskService.py to check if a task is in "started" state for 5 min, if yes marked as failed
* Created a scheduler script to check stale_tasks every 1 min automatically
* Added logs for visibility
* Handled multiple errors:
	- DB error
	- Circular imports error
	- Identation error
	- Module not found error
	- app out of context
* Tested it by intentionally creating an error during task processing

## 3.1 : Structured Logging (Debugging)

* Created logging config app/utils/logger.py
* Initialized logger in main app
* Used logger in worker, API
* Watched real time logs

## 4.1 : Debug Endpoint (System Visibility API)

* Created a new route /debug/tasks
* Tested it
* Added filtering "status"
* Added summary
