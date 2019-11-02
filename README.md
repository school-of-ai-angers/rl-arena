# Reinforced Learning Arena

A platform to confront in multiple two-player games agents trained with reinforcement learning.

This project is a joint venture between the School of AI [in Angers](https://www.meetup.com/Angers-School-of-AI/) and in [Le Mans](https://www.meetup.com/Le-Mans-School-of-AI/), France to explore Reinforcement Learning in an engaging and dynamic setup.
For that, we've decided to setup this arena where attendees can submit their own competitors and the system will make them battle against each other to decide who's the best!

## Environments

An environment is an implementation of a two-player game. This repo contains implementations for:

- Tic-tac-toe
- Quarto
- Connect Four

Each implementation resides inside its own directory in `environments`, providing:

- `environment.py`: a Python implementation of the game rules and its HTML renderization
- `info.yml`: data used to set-up the Environment model in the database
- `static`: static files served on the website under the URL `/static/environment-&lt;environment>/`

## Project Components

* builder: responsible for preparing a Docker image wrapping each submission
* core: main Django settings, database models and migrations
* data: contains all user data, its subdirectories are mounted inside the multiple containers
* duel_runner: launch and monitors the duels that are scheduled as part of the tournaments and also tests whether a given submission is valid by making it play against itself multiple times without any rule violation
* environments: implement the different games
* example_players: a collect of basic players, mostly used for testing
* nginx: Nginx webproxy configuration
* publisher: responsible for pushing public submissions to the repo [rl-arena-public-submissions](https://github.com/school-of-ai-angers/rl-arena-public-submissions)
* run_duel: given two Docker images and the environment name, runs multiple matches and collect the results
* terraform: controls the infrastructure deployment on DigitalOcean
* tournament_manager: launch and monitors running tournaments, aggregating results and calculating rankings
* web: main Django app with all the user-facing web platform

## Development

1. Clone this repo
2. Install Docker and docker-compose
3. Copy `example.env` as `.env` and edit it with values that fit you
4. Run `./prepare_dev.sh`

## Duel Runner

This is a Python script that executes a duel between two players. For that, it  takes the Docker-image name of each player and the name of the environment.

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

## Production Deployment

1. Install [Terraform](https://www.terraform.io/)
2. Create a `terraform/secrets.tfvars` file with the necessary tokens
3. `cd terraform; terraform apply -var-file=secrets.tfvars`
4. Inside the recently-created Droplet, execute the following instructions. Note: this script should be executed manually, as there are some interactive steps!

    ```sh

    # Build source
    git clone https://github.com/school-of-ai-angers/rl-arena.git
    cd rl-arena

    # Prepare service account keys
    nano keys/gcp.json # Paste JSON key
    
    docker build -t rl-arena .
    docker build -t rl-arena-nginx nginx

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

    # Start other services in master node
    docker-compose up -d web builder publisher tournament_manager auto_scaler

    # Generate certificate
    docker-compose up -d nginx
    docker-compose exec nginx bash
    # Run it inside:
    certbot --nginx --register-unsafely-without-email
    # Get out

    # Rerun nginx
    docker-compose stop nginx
    docker-compose up -d nginx

    # Setup firewal
    ufw allow 80
    ufw allow 443
    ufw allow in on eth1 to any port 5432 proto tcp

    # Turn off and then create snapshot for worker
    docker-compose down
    poweroff

    ```