docker run -d --name CA-db -e POSTGRES_DB=CA_db -e POSTGRES_USER=CA_user -e POSTGRES_PASSWORD=CA123 -p 5434:5432 postgis/postgis
