FROM continuumio/miniconda3:4.7.10

WORKDIR /app

COPY . .
RUN find .

# Conda dependencies
COPY environment.yml .
RUN conda env create
RUN echo "conda activate $(head -1 /app/environment.yml | cut -d' ' -f2)" >> ~/.bashrc
ENV PATH /opt/conda/envs/$(head -1 /app/environment.yml | cut -d' ' -f2)/bin:$PATH

# Extra dependencies
RUN pip install gunicorn==19.9.0 flask==1.1.1

# Main app
COPY . .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "bash", "-l", "-c", "gunicorn -b 0.0.0.0 _apify:app" ]