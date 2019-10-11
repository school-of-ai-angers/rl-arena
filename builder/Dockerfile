FROM continuumio/miniconda3:4.7.10

WORKDIR /app

# Conda dependencies
COPY environment.yml .
RUN conda env create
RUN echo "source activate $(head -1 /app/environment.yml | cut -d' ' -f2)" > ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /app/environment.yml | cut -d' ' -f2)/bin:$PATH

# Main app
COPY . .
