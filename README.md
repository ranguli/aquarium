## Building
```
docker build . -t ranguli/urlhaus_dl
```

## When updating the dependencies for the Dockerfile, run:

```bash
poetry run pip freeze > requirements.txt
```
