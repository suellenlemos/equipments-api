# Equipments API

## Description

This project involves developing a REST API.

## Main Stacks

- Python;
- Flask;
- SQLAlchemy;
- PostgreSQL
- Nginx

## Prerequisites

- Docker
- Docker-compose

## Getting Started

- Clone the repository:

```code
git clone https://github.com/suellenlemos/equipments-api.git
```

- Go to the project folder

## Environment Variables

Create a `.env` file in the root of the project and add the environment variables from the `.env.example`

Set a password and a database name of your choice and place them respectively in the `POSTGRES_PASSWORD`and `POSTGRES_DB` environment variables

## Building and running the containers locally

In this project there are a couple of containers:

- `co-equipments-backend`: backend API to handle business rule and data;
- `co-equipments-backend-nginx`: when Flask is up we can build Nginx container, it will be our web-server, exposing the port and mapping the application routes;
- `co-equipments-postgres`: PostgreSQL image for database purposes;

To start the application, open your terminal, go to the project folder and execute this command:

```code
docker-compose -f docker-compose.yml -f docker-compose.local.yml build && docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

It will take a few minutes to create the containers and build the images.

After that, run `docker ps`. You should be able to see the three containers listed above running.

## Testing the app with Postman or Insomnia

Now the application is ready to use. You can make requests on this address: [http://localhost:5002/](http://localhost:5002/)

To help you, I have provided a postman collection and environment inside the folder called `postman`. You can import them into postman and test the app.

In case you need logs from a container, use the command: `docker logs <container_name>`

### Creating a new user

- First of all, you need to create a user with a POST request to `http://localhost:5002/register`. In the request's body, send the user email, password and fullname. Example:

```text
{
    "email": "teste@teste.com",
    "password": "Teste*123",
    "fullname": "Suellen Lemos"
}
```

### Log in the user

- After that, you will need to log in this user sending a POST request to `http://localhost:5002/login`. In the request's body, send the user email and password. Example:

```text
{
    "email": "teste@teste.com",
    "password": "Teste*123"
}
```

You'll be able to see the token in the response body.

### Adding the token inside the Postman Environment

- Copy the token and go to the Postman Equipments Environment. Paste it inside the "Current value" in the Variable called token and save it. Example:

| Variable | Type    | Initial value | Current value |
| -------- | ------- | ------------- | ------------- |
| token    | default | Bearer token  | Bearer token  |

### Uploading the csv file to add data inside equipment's table

- Download the csv file from the API repository: [equipments.csv](https://github.com/suellenlemos/equipments-api/blob/0f9fa07107ea8f68d1ec1972de67addbf86b7b0f/src/temporary/equipment.csv)

- To download it, click on the download icon (Download raw file) or press `Command`+`Shift`+`s` (Mac) or `Ctrl`+`Shift`+`s` (Windows/Linux)

- If you wish, you can add new data in the csv file or create a new one. Just follow this format:

| equipmentId | timestamp                     | value |
| ----------- | ----------------------------- | ----- |
| EQ-5        | 2024-08-29T01:30:00.000-05:00 | 78.81 |

- To upload the file, you need to send a POST request to `http://localhost:5002/equipment/upload`. In the request's body, go to the "form-data" and select the csv file. Example:

| Key       | Value         |
| --------- | ------------- |
| file File | equipment.csv |

### Getting equipments data

- Send a GET request to `http://localhost:5002/equipment?column_name=equipmentId`. You should be able to see the request body. Example:

```text
{
  "equipments": [
    {
      "label": "EQ-1",
      "last_24": null,
      "last_48": null,
      "last_month": 52.5,
      "last_week": 48.58,
      "value": "EQ-1"
    },
    {
      "label": "EQ-2",
      "last_24": null,
      "last_48": null,
      "last_month": 55.23,
      "last_week": 47.13,
      "value": "EQ-2"
    }
  ],
  "total": 2
}
```

## Testing the app with the front-end application

If you wish, you can test it using the front-end, which can be found in the [equipments-frontend repository](https://github.com/suellenlemos/equipments-frontend)

Just follow the instructions described in the `README.md` file.

## Running The Application Locally

Instead of running the Flask app through containers, you can start the application locally.

Prerequisites:

- Python v3.12.5

Follow the steps below:

- Go to your terminal and run:

```code
docker ps
```

- Stop the backend and Nginx containers running:

```code
docker stop co-equipments-backend equipments-backend-nginx
```

- Run `docker ps`again: you should be able to see only the Postgres container running (don't stop it or remove it)

- Go to your `.env` file and change the POSTGRES_HOST environment variable to `POSTGRES_HOST=localhost`

- In the `main.py` file change the port 5010 to `5002`

- In the application folder execute the commands below:

### Unix/macOS

```code
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r src/requirements.txt
export FLASK_APP=main.py
python -m flask run
```

### Windows

```code
py -m venv .venv
.venv\Scripts\activate
pip3 install -r src/requirements.txt
export FLASK_APP=main.py
python -m flask run
```
