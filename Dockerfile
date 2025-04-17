FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PGTZ=UTC \
    # For system-wide poetry installation. Allows pip to remove system python packages
    PIP_BREAK_SYSTEM_PACKAGES=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      iputils-ping \
      telnet \
      curl \
      wget \
      python3.12 \
      python3.12-dev \
      python3-pip \
      libxml2-dev \
      libxslt-dev \
      libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install and allow poetry to install packages system-wide
RUN pip3 --no-cache-dir install poetry --break-system-packages
# RUN curl -sSL https://install.python-poetry.org | python3 -
# ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    antiword

RUN mkdir -p                    /opt/catsearch/cat-spider

COPY ./pyproject.toml           /opt/catsearch/cat-spider
COPY ./poetry.lock              /opt/catsearch/cat-spider
COPY ./alembic.ini              /opt/catsearch/cat-spider

WORKDIR                         /opt/catsearch/cat-spider

# Install packages system-wide
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi --compile --only main

#ENV PYTHONPATH="${PYTHONPATH}:/opt/catsearch/cat-spider"
ENV PYTHONPATH=/opt/catsearch/cat-spider

COPY ./entrypoint.sh            /opt/catsearch/cat-spider/entrypoint.sh
RUN chmod +x                    /opt/catsearch/cat-spider/entrypoint.sh
ENTRYPOINT ["/opt/catsearch/cat-spider/entrypoint.sh"]

COPY ./src/                     /opt/catsearch/cat-spider/src
