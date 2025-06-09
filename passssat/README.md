# KoNaR PassAt App

Webpanel for controlling the boat and 

Repo have some large files, so make sure that your `git-lfs` works.

## Docker Instalation

To run application make sure that you have `Docker`, `Poetry` and `Python3.10`.  
Then use below commands:

```shell
$ docker build -t pa-app .
$ docker run -p 8000:8000 pa-app
```

## Basic Instalation

To run application without docker first make sure that you have `Poetry` and `Python3.10`.  
Then use below commands:

```shell
$ poetry env use python3.10
$ poetry install
$ poetry shell
(venv) $ uvicorn --host localhost --port 8000 pa_app.main:app --reload
```

## TCP connection test

To test TCP connection follow steps listed below:  
1. Connect to nihilia server through this command:  
```ssh -L 42069:0.0.0.0:42069 passat@nihilia.xyz ```
2. Start server reciver:  
 ``` python3.10 server.py```
3. Use Basic Instalation steps to set up an app and send the message via text box.  
**DISCLAIMER**: Currently sending messages does not work if app is runned via docker.

## Web Application

Website application is working under link: [PassApp](https://passat.nihilia.xyz/)

If its not working that means the docker container is down.  
Head to server: ```passat@nihilia.xyz```  
Go to: ```/home/passat/passapp/passat-high```  
Run: ```docker compose up --build -d```
