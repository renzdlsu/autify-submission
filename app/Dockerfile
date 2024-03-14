FROM python:3.12-slim-bullseye as builder

WORKDIR /app

RUN pip install --no-cache-dir pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv requirements  > requirements.txt

FROM python:3.12-slim-bullseye

ARG HF_API_URL
ARG HF_MODEL_NAME
ARG HF_TOKEN

ENV HF_API_URL=${HF_API_URL}
ENV HF_MODEL_NAME=${HF_MODEL_NAME}
ENV HF_TOKEN=${HF_TOKEN}

WORKDIR /app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
