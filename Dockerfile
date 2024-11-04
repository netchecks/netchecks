FROM python:3.11.10-slim
LABEL org.opencontainers.image.source=https://github.com/hardbyte/netchecks

# Configure Poetry
ENV USERNAME=netchecks \
    USER_UID=1000 \
    USER_GID=1000 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME=/home/netchecks/bin/poetry \
    POETRY_VENV=/home/netchecks/bin/poetry-venv \
    POETRY_CACHE_DIR=/home/netchecks/bin/.cache \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME}

USER ${USERNAME}

# Install poetry separated from system interpreter
RUN python3 -m venv ${POETRY_VENV} \
    && ${POETRY_VENV}/bin/pip install -U pip setuptools --no-cache-dir \
    && ${POETRY_VENV}/bin/pip install poetry==${POETRY_VERSION} --no-cache-dir

# Add `poetry` to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Install dependencies
COPY --chown=${USERNAME}:${USER_GID} poetry.lock* pyproject.toml README.md ./
RUN poetry install --no-root --no-cache

COPY --chown=${USERNAME}:${USER_GID} ./netcheck/ /app/netcheck/
RUN poetry install --no-cache
ENTRYPOINT ["poetry", "run", "netcheck"]
CMD ["http", "-v"]
