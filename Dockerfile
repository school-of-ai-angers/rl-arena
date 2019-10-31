FROM continuumio/miniconda3:4.7.10

# Install docker inside the image (it's used by the builder app)
# Instructions from https://docs.docker.com/install/linux/docker-ce/debian/
RUN apt-get -q update && \
    apt-get -q install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get -q update && \
    apt-get -q install -y docker-ce docker-ce-cli containerd.io

# Save the public key for GitHub
RUN mkdir ~/.ssh && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

# Install gcloud
COPY keys/gcp.json keys/gcp.json
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get -q update && \
    apt-get -q install -y google-cloud-sdk && \
    gcloud auth activate-service-account --key-file keys/gcp.json && \
    gcloud auth configure-docker


WORKDIR /app

# Conda dependencies
COPY environment.yml .
RUN conda env create
RUN echo "conda activate rl-arena" >> ~/.bashrc
ENV PATH=/opt/conda/envs/rl-arena/bin:$PATH

# Main app
COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "/opt/conda/envs/rl-arena/bin/python" ]

