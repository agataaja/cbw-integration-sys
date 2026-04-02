FROM python:3.13

WORKDIR /app

# dependências do sistema
RUN apt-get update && apt-get install -y curl build-essential

# instalar poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# adicionar poetry ao PATH
ENV PATH="/root/.local/bin:$PATH"

COPY backend/pyproject.toml backend/poetry.lock* /app/

RUN poetry config virtualenvs.create false

RUN poetry lock

RUN poetry install --no-root --without ml

COPY backend/ /app/

# EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8080"]
