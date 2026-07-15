FROM amazon/aws-cli:latest AS model-fetcher

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_REGION
ARG AWS_ROLE_ARN
ARG AWS_S3_BUCKET
ARG MODEL_VERSION

RUN CREDS=$(aws sts assume-role \
      --role-arn "$AWS_ROLE_ARN" \
      --role-session-name "docker-build" \
      --duration-seconds 900 \
      --output json) && \
    export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['Credentials']['AccessKeyId'])") && \
    export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['Credentials']['SecretAccessKey'])") && \
    export AWS_SESSION_TOKEN=$(echo "$CREDS" | python3 -c "import sys,json; print(json.load(sys.stdin)['Credentials']['SessionToken'])") && \
    aws s3 cp \
      "s3://${AWS_S3_BUCKET}/models/gym_crowd_model_${MODEL_VERSION}.joblib" \
      /model.joblib

# --- Final image: no secrets here ---
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG MODEL_VERSION
COPY --from=model-fetcher /model.joblib models/gym_crowd_model_${MODEL_VERSION}.joblib

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
