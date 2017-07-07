DETAILS
================
Docker Version 1.12.3 (8488) 
Channel: Stable

INSTRUCTIONS
================
Navigate to this directory
Build image with command `docker -t <chooseAnImageName> build .`
Run image in background with `docker run -d -p 5000:5000 --name <chooseContainerName> <imageNameFromAbove>`
View at http://127.0.0.1:5000
Stop it with `docker stop <containerNameFromAbove` and remove it with `docker rm <containerNameFromAbove>`. Delete the images with `docker rmi <imageNameFromAbove>`

HELP
================
Can't load the page http://127.0.0.1:5000
	Add the argument host='0.0.0.0' to web.py in app.run so that it becomes app.run(debug=True, host='0.0.0.0', extra_files=template_files + model_files)
	(This enables external communication to the web server on the container. A sed command has been added to the Dockerfile to hopefully do this automatically.)

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
