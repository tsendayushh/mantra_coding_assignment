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

### Improvement points


#### DB level improvements:
#### 1. by creating a replica db to separate the db to read and write purpose

```
# in the settings file
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'db-primary',  # Writes go here
    },
    'read_replica': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'db-replica',  # Reads go here
    }
}

# and change the reading queries to
queryset = LearningLog.objects.using('read_replica').filter(...)

```
#### Cons of separating the db:
##### there will be a delay to the sync of the 2 dbs the entries that committed might be not shown right after.


#### 2. To improve the performance of the user summary API, we can use cache, redis to store the user summaries per user query key, or could use cache_page decorator
