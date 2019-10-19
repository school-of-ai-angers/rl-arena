# Reinforced Learning Arena

## Project structure

```
data
    +- db
    +- media
        +- submissions
        +- submission_image_logs
        +- submission_test_logs
        +- duel_logs
```

## Dev

1. Clone this repo
2. Install Docker and docker-compose
3. Run `./prepare_dev.sh`
4. Run in another terminal `docker-compose run --rm web 'python manage.py createsuperuser'` to create your root account