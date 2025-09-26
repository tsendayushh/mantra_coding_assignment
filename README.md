# Assignment Template

## Initial Setup

- uv is recommended for managing virtual environments.

```
uv sync --all-groups

# uv run manage.py migrate
```

### Run tests

```
docker compose exec web uv run poe test
```

### Run server

```
# uv run manage.py runserver
docker compose up -d --build
```

### To load the mock data
```
docker compose exec web uv run manage.py init_data
```


### Lint and format code

```
uv run poe lint
uv run poe format
```
