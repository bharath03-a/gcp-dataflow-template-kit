# Dataflow Starter Kit

A simple Apache Beam pipeline template for Google Cloud Dataflow.

## Installation

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

## Running Locally

```bash
# Using DirectRunner
python -m dataflow_starter_kit.main --input=1 --runner=DirectRunner

# With multiple iterations
python -m dataflow_starter_kit.main --input=5 --runner=DirectRunner
```

## Docker Build and Test

### Build the Docker image

```bash
docker build -t dataflow-template:latest .
```

### Test the Docker image locally

The Docker image is designed for Dataflow Flex Templates. To test locally:

```bash
# Option 1: Run without Docker (recommended for local testing)
python -m dataflow_starter_kit.main --input=1 --runner=DirectRunner

# Option 2: Run inside Docker container
docker run --rm --entrypoint /bin/bash dataflow-template:latest \
  -c "python -m dataflow_starter_kit.main --input=1 --runner=DirectRunner"

# Option 3: Interactive shell for debugging
docker run --rm -it --entrypoint /bin/bash dataflow-template:latest
```

## Deployment to Google Cloud Dataflow

### Build and push to Artifact Registry

```bash
# Set your project and location
export PROJECT_ID=your-project-id
export REGION=us-east4  # or us-central1
export REPO_NAME=cloud-run-ai  # your Artifact Registry repo
export IMAGE_NAME=dataflow-template

# Build and push to Artifact Registry
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest
```

### Create Flex Template

```bash
# Create staging bucket if it doesn't exist
gsutil mb -l ${REGION} gs://dataflow-staging-${REGION}-${PROJECT_ID}

# Build Flex template (without metadata for simplicity)
gcloud dataflow flex-template build \
  gs://dataflow-staging-${REGION}-${PROJECT_ID}/templates/${IMAGE_NAME}.json \
  --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
  --sdk-language PYTHON

# Or with metadata file (optional)
# gcloud dataflow flex-template build \
#   gs://dataflow-staging-${REGION}-${PROJECT_ID}/templates/${IMAGE_NAME}.json \
#   --image ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest \
#   --sdk-language PYTHON \
#   --metadata-file flex-template-metadata.json
```

### Run Flex Template on Dataflow

```bash
# Enable Dataflow API if not already enabled
gcloud services enable dataflow.googleapis.com

# Run the Flex template
gcloud dataflow flex-template run dataflow-template-$(date +%Y%m%d-%H%M%S) \
  --template-file-gcs-location gs://dataflow-staging-${REGION}-${PROJECT_ID}/templates/${IMAGE_NAME}.json \
  --region ${REGION} \
  --parameters input=1

# Check job status
gcloud dataflow jobs list --region ${REGION} --limit 5
```

### Alternative: Run directly with DataflowRunner

```bash
python -m dataflow_starter_kit.main \
  --input=1 \
  --runner=DataflowRunner \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --temp_location=gs://dataflow-staging-${REGION}-${PROJECT_ID}/temp \
  --flex_container_image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:latest
```

## Pipeline Description

This pipeline:

1. Creates input data (F1 lap times by driver)
2. Processes each element to extract lap times
3. Aggregates total lap time using sum

### Example Input

```
Hamilton - 83.456
Verstappen - 82.789
Leclerc - 81.234
Sainz - 80.567
```

### Example Output

```
Total time: 328.046s
```

## Project Structure

```
dataflow_starter_kit/
├── main.py                 # Pipeline entry point
├── transforms/
│   └── transform.py        # ProcessElement transform
├── options/
│   └── starter_kit_options.py  # Custom pipeline options
└── utils/
    └── config.py           # Configuration constants
```
