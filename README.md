# image-search-lance


## docker-compose

```bash
docker compose build
```

```bash
export DATABASE_ASYNC_URL=postgresql+asyncpg://postgres:postgres@0.0.0.0:5432/mydb
uv run alembic revision --autogenerate -m "Create a Search table"
```


## Load Test
hey -n 1000 -c 30 -m POST -H "Content-Type: application/json" -d '{"query": "cat"}' http://localhost:8000/search

hey -n 1000 -c 30 -m POST -H "Content-Type: application/json" -d '{"input": "cat"}' http://localhost:8005/embed/text