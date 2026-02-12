FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    postgresql-client \
    python3-dev \
    libgmp3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

RUN mkdir -p /app/staticfiles 

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "funding_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
