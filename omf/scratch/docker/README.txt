DETAILS
================
	Docker Version 1.12.3 (8488) 
	Channel: Stable

INSTRUCTIONS
================
Navigate to this directory
Build image with command 'docker -t <give it a local name> build .'
Run image in backgroudn with 'docker run -d -p 5000:5000 <local name given above>'
View at http://127.0.0.1:5000
Close it with 'docker stop $(docker ps -a -q)' and 'docker rm $(docker ps -a -q)'

HELP
================
Can't load the page http://127.0.0.1:5000
	Add the argument host='0.0.0.0' to web.py in app.run so that it becomes app.run(debug=True, host='0.0.0.0', extra_files=template_files + model_files)

Command won't run (containers are open)
	docker stop <id>
	docker rm <id>
		where id is found by docker ps -a -q

	or close them all:
	docker stop $(docker ps -a -q)
	docker rm $(docker ps -a -q)

The image failed to build
	remove old images with:
	docker rmi <image id from 'docker images' command>


FEATURE IDEAS
================
Python script to create, start and exit the image
Modify Dockerfile to use a network drive containing the omf repo instead of doing a fresh git pull
