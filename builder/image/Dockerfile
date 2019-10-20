FROM continuumio/miniconda3:4.7.10

WORKDIR /app

# Conda dependencies
COPY environment.yml .
RUN conda env create
RUN echo "conda activate $(head -1 /app/environment.yml | cut -d' ' -f2)" >> ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /app/environment.yml | cut -d' ' -f2)/bin:$PATH

# Extra dependencies
# Run inside a login bash to use the conda environment
RUN bash -l -c 'pip install gunicorn==19.9.0 flask==1.1.1'

# Main app
COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "bash", "-l", "-c" ]

CMD [ "gunicorn -b 0.0.0.0 _apify:app" ]