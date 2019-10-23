FROM continuumio/miniconda3:4.7.10

# Install docker inside the image (it's used by the builder app)
# Instructions from https://docs.docker.com/install/linux/docker-ce/debian/
RUN apt-get -q update && \
    apt-get -q install -y apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - && \
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" && \
    apt-get -q update && \
    apt-get -q install -y docker-ce docker-ce-cli containerd.io

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

