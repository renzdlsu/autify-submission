FROM python:3.12-slim-bullseye as builder

WORKDIR /app

RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv requirements  > requirements.txt

FROM python:3.12-slim-bullseye as model-cacher

WORKDIR /app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY download_model.py .
RUN python download_model.py


FROM python:3.12-slim-bullseye

WORKDIR /app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=model-cacher /root/.cache /root/.cache

COPY main.py .
CMD ["python", "main.py"]
