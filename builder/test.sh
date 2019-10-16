#!/bin/bash -e


(
    cd test/submission
    rm submission.zip || true
    zip -r submission.zip ./*
)

python main.py test/submission/submission.zip

#docker build -t rl-arena-builder .

#docker run --rm -p 8000:8000 rl-arena-builder