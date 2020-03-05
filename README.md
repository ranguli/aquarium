## Building

```
docker build . -t ranguli/urlhaus_dl
```

## Running

```
docker run -it --name urlhaus_dl -v /path/to/project:/urlhaus_db ranguli/urlhaus_dl
```


## When updating the dependencies for the Dockerfile, run:

```bash
poetry run pip freeze > requirements.txt
```
