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

