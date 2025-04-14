FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PGTZ=UTC
#    POETRY_HOME="/opt/poetry" \
#    PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update \
    && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    iputils-ping \
    telnet \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
# RUN python3 -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# Install Poetry
# TODO: resolve --break-system-packages later
RUN pip3 --no-cache-dir install poetry --break-system-packages
# RUN curl -sSL https://install.python-poetry.org | python3 -
# ENV PATH="/root/.local/bin:$PATH"

RUN mkdir -p                    /opt/catsearch/cat-spider

COPY ./pyproject.toml           /opt/catsearch/cat-spider
COPY ./poetry.lock              /opt/catsearch/cat-spider
COPY ./alembic.ini              /opt/catsearch/cat-spider

WORKDIR                         /opt/catsearch/cat-spider

# RUN pwd; ls -la; which python; which poetry; sleep 100

RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi --compile --only main

COPY ./entrypoint.sh            /opt/catsearch/cat-spider/entrypoint.sh
COPY ./src/                     /opt/catsearch/cat-spider/src

RUN chmod +x                    /opt/catsearch/cat-spider/entrypoint.sh

ENV PYTHONPATH "${PYTHONPATH}:/opt/catsearch/cat-spider"

ENTRYPOINT ["/opt/catsearch/cat-spider/entrypoint.sh"]
