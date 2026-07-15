#!/bin/sh
set -e

MODEL_FILE="models/gym_crowd_model_${MODEL_VERSION}.joblib"

if [ ! -f "$MODEL_FILE" ]; then
  echo "Assuming role for temporary S3 credentials..."

  CREDS=$(aws sts assume-role \
    --role-arn "$AWS_ROLE_ARN" \
    --role-session-name "render-deploy-$(date +%s)" \
    --duration-seconds 900 \
    --output json)

  export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | python -c "import sys,json; print(json.load(sys.stdin)['Credentials']['AccessKeyId'])")
  export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | python -c "import sys,json; print(json.load(sys.stdin)['Credentials']['SecretAccessKey'])")
  export AWS_SESSION_TOKEN=$(echo "$CREDS" | python -c "import sys,json; print(json.load(sys.stdin)['Credentials']['SessionToken'])")

  echo "Downloading model ${MODEL_VERSION} from S3..."
  mkdir -p models
  aws s3 cp \
    "s3://${AWS_S3_BUCKET}/models/gym_crowd_model_${MODEL_VERSION}.joblib" \
    "$MODEL_FILE"

  unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
  echo "Model downloaded. Temporary credentials discarded."
else
  echo "Model already present, skipping download."
fi

exec "$@"
