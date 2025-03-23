FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    alembic==1.12.0 \
    psycopg2-binary==2.9.9 \
    sqlalchemy==2.0.20 \
    geoalchemy2==0.14.0

ENTRYPOINT ["alembic"]
CMD ["--help"]
