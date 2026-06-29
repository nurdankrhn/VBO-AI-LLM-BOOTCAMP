```bash
docker run --name pg16-weather-container \
  -e POSTGRES_USER=weather_admin \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=weather_db \
  -p 5432:5432 \
  -d postgres:16

```