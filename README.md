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
3. Copy `example.env` as `.env` and edit it
4. Run `./prepare_dev.sh`

## Prepare publish repo

1. `mkdir -p data/publish_keys`
2. `ssh-keygen -f data/publish_keys/id_rsa`

## Environments

An environment is an implementation of a two-player game. This repo contains implementations for:

- Tic-tac-toe
- Quarto
- Connect Four

Each implementation resides inside its own directory in `environments`, providing:

- `environment.py`: a Python implementation of the game rules and its HTML renderization
- `info.yml`: data used to set-up the Environment model in the database
- `static`: static files served on the website under the URL `/static/environment-&lt;environment>/`

## Duel runner

This is a pure-Python script that executes a duel between two players. For that, it  takes the Docker-image name of each player and the name of the environment.

It will output a JSON document with the results of the duel with the format:

```json
{
    "result": "one of: ERROR, PLAYER_1_WIN, PLAYER_2_WIN, DRAW",
    "error_msg": "",
    "num_matches": 17,
    "player_1_errors": 17,
    "player_2_errors": 17,
    "other_errors": 17,
    "player_1_wins": 17,
    "player_2_wins": 17,
    "draws": 17,
    "player_1_score": 1.7,
    "player_2_score": 1.7,
    "matches": [{
        "result": "one of: PLAYER_1_ERROR, PLAYER_2_ERROR, OTHER_ERROR, PLAYER_1_WIN, PLAYER_2_WIN, DRAW",
        "error_msg": "",
        "player_1_score": 1.7,
        "player_2_score": 1.7,
        "first_player": "one of: PLAYER_1, PLAYER_2",
        "states": ["result of BaseEnvironment.to_jsonable()"]
    }]
}
```

## Deployment

* secrets.tfvars
* `cd terraform; terraform apply -var-file=secrets.tfvars`

```sh
# Build source
git clone https://github.com/school-of-ai-angers/rl-arena.git
cd rl-arena
docker build -t rl-arena .

# Configure env
cp example.env .env
nano .env

# Prepare publisher repo
mkdir -p data/publish_keys
ssh-keygen -f data/publish_keys/id_rsa
cat data/publish_keys/id_rsa.pub

# Prepare database
docker-compose up -d db
wait 30
docker-compose run --rm -T migrate

# Prepare static files
docker-compose run --rm collectstatic

# Start other services
docker-compose up -d web builder publisher smoke_tester tournament_manager duel_runner nginx
```