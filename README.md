# Service Ticket Classifier

A small full-stack project that classifies IT support tickets, suggests related troubleshooting steps, stores reviewed tickets, and supports retraining the model with corrected labels.

I built this project mainly to learn how the different parts of an ML application fit together once it leaves a notebook. The final version includes a React frontend, FastAPI backend, PostgreSQL with pgvector, separate training and retraining jobs, Docker images, Kubernetes manifests, Terraform infrastructure, and GitHub Actions workflows running on self-hosted runners.

This project's CI/CD runs entirely on a self-hosted Actions Runner Controller platform built as a separate project ([Secure Self-Hosted CI Platform]). Instead of relying on GitHub-hosted runners, each workflow spins up an ephemeral runner inside my own AWS environment, uses IAM permissions directly, and is deleted once the job finishes. Connecting the two projects allowed me to use one as the delivery platform for the other while avoiding long-lived AWS credentials in GitHub Secrets.

> This is a personal project and proof of concept. It is not connected to a live help desk and is not intended to be presented as a production-ready support system.

---

## Demo

https://github.com/user-attachments/assets/89210ecc-8706-4577-8c9a-e68dc37c3dff

Screenshots for AWS resources that were provisioned and k8s resources can be seen at: [Resource Images](./Project3_images)

---

## What the Project Does

A user submits an IT support ticket through the frontend. The application then:

1. Sends the ticket to the FastAPI backend.
2. Predicts one of five categories:
   - Hardware
   - Software
   - Access
   - Network
   - Security
3. Returns a confidence score for the prediction.
4. Searches a troubleshooting knowledge base for relevant guidance.
5. Stores the ticket and prediction in PostgreSQL.
6. Lets the user confirm or correct the predicted category.
7. Saves reviewed tickets for later retraining.

Once enough reviewed tickets are available, a separate retraining job can update the dataset, train a new model, upload it to S3, and restart the API so the new model is loaded.

---

## Why I Built It

The idea came from working with IT service tickets and seeing how much repetitive work goes into categorizing issues and looking up troubleshooting steps.

I wanted to build something that went further than training a classifier locally. The main goal was to understand the full workflow around the model:

- preparing and validating data
- training and saving the model
- exposing predictions through an API
- building a frontend around the API
- storing tickets and corrections
- using vector search for troubleshooting documents
- containerizing each part
- deploying everything to Kubernetes
- provisioning AWS infrastructure with Terraform
- automating builds and deployments through GitHub Actions

The model itself is intentionally simple. Most of the work in this project was around connecting the different systems and getting the application deployed end to end.

---

## Architecture

```text
User
  |
  v
React / Vite Frontend
  |
  |  /api
  v
AWS Application Load Balancer
  |
  +-- /      -> Frontend Service -> Nginx Pod
  |
  +-- /api   -> API Service -> FastAPI Pod
                                  |
                                  +-- Loads model from Amazon S3
                                  +-- Predicts ticket category
                                  +-- Searches pgvector knowledge base
                                  +-- Stores tickets in Amazon RDS
```

### Model flow

```text
Public dataset + synthetic dataset
                |
                v
       Kubernetes training job
                |
                v
        Model uploaded to S3
                |
                v
        API downloads model
```

### Review and retraining flow

```text
Prediction
    |
    v
User confirms or corrects category
    |
    v
Reviewed ticket stored in PostgreSQL
    |
    v
Retraining job selects unused reviewed tickets
    |
    v
Dataset updated and model retrained
    |
    v
New model uploaded to S3
    |
    v
API deployment restarted
```

### Troubleshooting retrieval flow

```text
Markdown troubleshooting files
               |
               v
          Amazon S3
               |
               v
       Knowledge-base insert job
               |
               v
      Chunking and embeddings
               |
               v
     PostgreSQL with pgvector
               |
               v
 Similar troubleshooting sections returned
```

---

## Main Features

### Ticket classification

The backend uses a scikit-learn pipeline made up of:

- `TfidfVectorizer`
- `LogisticRegression`

The model uses the ticket subcategory and description as its input and returns a predicted category and confidence score.

```python
X = Subcategory + Description
y = Category
```

The fitted vectorizer and classifier are saved together with `joblib`.

### Troubleshooting suggestions

The project includes a small Markdown knowledge base with common IT troubleshooting documents.

The documents are split into sections such as:

- Symptoms
- Likely Causes
- Troubleshooting Steps

Each section is embedded with `sentence-transformers/all-MiniLM-L6-v2` and stored in PostgreSQL using pgvector.

When a ticket is submitted, the system embeds the ticket text, runs a similarity search, and returns the most relevant troubleshooting sections.

This is retrieval only. It does not use an LLM to generate new troubleshooting instructions.

### Ticket history

Submitted tickets are stored in PostgreSQL and can be viewed through the frontend.

Stored information includes:

- ticket description
- predicted category
- prediction confidence
- confirmed category
- whether the ticket has already been used for retraining

### Human review

The user can accept the model prediction or replace it with the correct category.

The database keeps both:

```text
predicted_category
confirmed_category
```

Keeping both values makes it possible to compare the original prediction with the reviewed result.

### Retraining

A ticket becomes eligible for retraining when it has a confirmed category and has not already been used:

```sql
confirmed_category IS NOT NULL
AND used_for_training IS FALSE
```

The current threshold is five reviewed tickets.

The retraining job:

1. Reads eligible tickets from PostgreSQL.
2. Adds them to the synthetic dataset.
3. Validates the updated data.
4. Combines the public and synthetic datasets.
5. Retrains the classifier.
6. Uploads a versioned model to S3.
7. Updates the production model in S3.
8. Marks the tickets as used.
9. Restarts the API deployment.

The API is restarted because it loads the model when the container starts.

---

## Tech Stack

### Application

- Python
- FastAPI
- Pydantic
- React
- Vite
- JavaScript
- Nginx

### Machine learning and retrieval

- scikit-learn
- pandas
- TF-IDF
- logistic regression
- joblib
- sentence-transformers
- pgvector

### Database and storage

- PostgreSQL
- Amazon RDS
- Amazon S3

### Deployment

- Docker
- Docker Compose
- Kubernetes
- Kustomize
- Amazon EKS Auto Mode
- Amazon ECR
- AWS Application Load Balancer

### Infrastructure and CI/CD

- Terraform
- GitHub Actions
- Actions Runner Controller
- self-hosted ephemeral runners
- AWS CLI
- kubectl
- Helm

---

## Repository Structure

```text
Project3/
├── .github/
│   └── workflows/
│       ├── build-push-image.yaml
│       ├── deploy-api-frontend.yaml
│       ├── deploy-application.yaml
│       ├── insert-s3.yaml
│       ├── retrain-model.yaml
│       └── verify-runner.yaml
│
├── app/
│   ├── Dockerfile
│   ├── get_tickets.py
│   ├── insert_user_data.py
│   ├── main.py
│   ├── predict.py
│   ├── requirements.txt
│   ├── schemas.py
│   └── update_ticket.py
│
├── data/
│   ├── combine_data.sh
│   ├── combined_ticket.csv
│   ├── public_it_tickets.csv
│   ├── synthetic_tickets.csv
│   └── validation_output.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
│
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── output.tf
│   │   ├── terraform.tf
│   │   └── variables.tf
│   └── s3_storage.py
│
├── knowledge_base/
│   └── *.md
│
├── kubernetes/
│   ├── api/
│   ├── frontend/
│   ├── jobs/
│   ├── ingress-class.yaml
│   ├── ingress.yaml
│   ├── kustomization.yaml
│   └── namespace.yaml
│
├── ml/
│   ├── combine_train.sh
│   ├── Dockerfile
│   ├── download_files.py
│   ├── requirements.txt
│   ├── test_train.py
│   ├── train.py
│   └── upload_files.py
│
├── models/
│
├── rag/
│   ├── Dockerfile
│   ├── build_chunks.py
│   ├── init.py
│   ├── requirements.txt
│   └── retrieve.py
│
├── retrain/
│   ├── Dockerfile
│   ├── retrain.py
│   ├── retrain.sh
│   ├── upload_files.py
│   └── validate.py
│
├── .dockerignore
├── .gitignore
└── docker-compose.yaml
```

`ml/`, `rag/`, `retrain/`, and `kubernetes/` are separate root-level directories. The Kubernetes directory only contains deployment manifests.

---

## Backend

The backend is a FastAPI application in `app/`.

Main responsibilities:

- load the production model from S3
- validate incoming requests
- classify tickets
- calculate prediction confidence
- retrieve troubleshooting suggestions
- insert tickets into PostgreSQL
- return ticket history
- save reviewed categories

The main routes include:

```text
GET  /api/
POST /api/analyze-ticket/
POST /api/ticket
GET  /api/tickets
GET  /api/ticket/{id}
POST /api/ticket/{id}/review
```

The exact routes and HTTP methods are defined in `app/main.py`.

### Important files

| File | Purpose |
|---|---|
| `main.py` | FastAPI application and routes |
| `predict.py` | Model loading and predictions |
| `insert_user_data.py` | Inserts submitted tickets |
| `get_tickets.py` | Reads ticket history |
| `update_ticket.py` | Saves reviewed categories |
| `schemas.py` | Pydantic request and response models |
| `Dockerfile` | Builds the API image |

The API listens on port `8000`.

---

## Frontend

The frontend is built with React and Vite.

It provides pages for:

- submitting a ticket
- viewing the prediction and confidence
- viewing troubleshooting suggestions
- viewing previous tickets
- reviewing or correcting a category

The production image uses a multi-stage Docker build:

1. Node builds the frontend.
2. Nginx serves the static files.

The frontend calls the backend through:

```text
/api
```

This allows the frontend and API to use the same ALB hostname without hard-coding a separate backend URL.

---

## Data and Model Training

The dataset contains fields similar to:

```text
Ticket ID
Category
Subcategory
Priority
Description
Source
```

The project started with:

- a public IT ticket dataset
- approximately 45 manually written synthetic tickets
- reviewed tickets created through the application

The public dataset contained roughly 200,000 records.

### Training pipeline

The initial training code is in `ml/`.

| File | Purpose |
|---|---|
| `download_files.py` | Downloads datasets from S3 |
| `train.py` | Trains and evaluates the model |
| `upload_files.py` | Uploads the model and reports |
| `combine_train.sh` | Runs the training steps in order |
| `Dockerfile` | Builds the training image |

Training is run as a Kubernetes Job rather than inside the API container.

### Data validation

The validation code checks for:

- missing columns
- missing values
- duplicate records
- invalid categories
- invalid priorities
- possible email addresses
- possible phone numbers

The validation is intended as a basic check before training. It is not a complete PII detection system.

### Model results

Two tests were run during development:

- Training on the public dataset and testing on the small synthetic dataset produced about **64.44% accuracy**.
- A split within the full public dataset produced about **99.996% accuracy**.

The second result is likely inflated by repeated or very similar records in the public dataset. I would not treat it as a realistic measure of production performance.

The model is included to support the larger application workflow rather than to make a claim about state-of-the-art classification accuracy.

---

## Knowledge Base and Vector Search

The retrieval code is in `rag/`.

| File | Purpose |
|---|---|
| `build_chunks.py` | Splits Markdown documents into sections and creates embeddings |
| `retrieve.py` | Searches pgvector for similar sections |
| `init.py` | Starts or coordinates the ingestion logic |
| `Dockerfile` | Builds the image used by the insert job |

The knowledge-base documents are stored locally in `knowledge_base/` and uploaded to S3 for the deployed version.

The insert job:

1. Downloads the Markdown files.
2. Builds chunks and metadata.
3. Generates embeddings.
4. Enables pgvector if required.
5. Creates the required table.
6. Inserts the chunks and vectors.

---

## AWS Infrastructure

Terraform code is stored in `infrastructure/terraform/`.

The deployed environment included:

- a VPC
- public and private subnets
- route tables
- an internet gateway
- a NAT gateway
- security groups
- an EKS Auto Mode cluster
- an RDS PostgreSQL instance
- an S3 bucket
- ECR repositories
- IAM roles and policies
- EKS Pod Identity associations

The project was deployed in `us-east-1`.

The EKS cluster was named:

```text
service-ticket-cluster
```

### S3 structure

```text
datasets/
├── raw/
│   ├── public-it-tickets.csv
│   └── synthetic-tickets.csv
├── processed/
│   └── combined-tickets.csv
└── versions/

knowledge-base/
└── Markdown files

models/
├── production/
│   └── ticket-classifier.joblib
└── versions/
    └── timestamped models

reports/
└── validation/
```

The API downloads:

```text
models/production/ticket-classifier.joblib
```

when it starts.

### PostgreSQL and pgvector

Amazon RDS stores:

- tickets
- predictions
- confirmed categories
- retraining status
- knowledge-base chunks
- embeddings

The RDS instance is private and the deployed application uses SSL for database connections.

---

## Kubernetes Deployment

All workloads run in the `service-ticket` namespace.

### API

The API is deployed with:

- two replicas
- port `8000`
- rolling updates
- readiness and liveness probes
- resource requests and limits
- a non-root container user
- a dedicated ServiceAccount
- ConfigMap and Secret configuration

### Frontend

The frontend is deployed with:

- two replicas
- Nginx on port `80`
- readiness and liveness probes
- rolling updates
- resource requests and limits

### Jobs

The project uses separate Kubernetes Jobs for:

- initial model training
- knowledge-base insertion
- model retraining

This keeps training workloads separate from the API that serves requests.

### Kustomize

`kubernetes/kustomization.yaml` combines the application manifests and generates ConfigMaps.

The deployment workflow renders and applies the manifests using:

```bash
kubectl kustomize
kubectl apply -k
```

A standalone `kustomize` binary is not required.

### ALB routing

The Application Load Balancer routes:

```text
/api  -> service-ticket-api:8000
/     -> service-ticket-frontend:80
```

The project uses an `IngressClass` and `IngressClassParams` for EKS Auto Mode.

---

## GitHub Actions

The workflows are stored in `.github/workflows/`.

### `verify-runner.yaml`

Checks that the self-hosted runner has the required tools and access.

### `build-push-image.yaml`

Builds and pushes the API, frontend, training, insertion, and retraining images to ECR.

Image tags follow a format similar to:

```text
<short-git-sha>-<run-number>
```

### `insert-s3.yaml`

Initializes a fresh environment by:

- applying required Kubernetes resources
- running the initial training job
- verifying the production model
- running the knowledge-base insertion job

This workflow is not intended to run after every normal application change.

### `deploy-application.yaml`

Deploys the API and frontend using Kustomize.

It:

- accepts an image tag
- configures access to EKS
- creates or updates the database Secret
- replaces image-tag placeholders
- renders and verifies the manifests
- applies the Kustomization
- waits for both deployments to roll out
- prints logs and Kubernetes events if something fails

The workflow is safe to run whether the application already exists or is being deployed for the first time.

### `retrain-model.yaml`

Runs the retraining Kubernetes Job.

It:

- injects the selected image tag
- creates the job
- checks for both success and failure
- prints the job logs
- verifies the new production model in S3
- restarts the API
- waits for the new API pods to become ready

### `deploy-api-frontend.yaml`

This was an earlier deployment workflow. The final Kustomize-based deployment is handled by `deploy-application.yaml`.

---

## Self-Hosted GitHub Actions Runners

The workflows run on a separate self-hosted runner setup using Actions Runner Controller.

The runner scale set is:

```text
arc-runner-set
```

Each workflow job gets its own temporary runner pod.

```text
Workflow queued
    |
    v
ARC listener receives job
    |
    v
Runner scale set changes from 0 to 1
    |
    v
Ephemeral runner pod is created
    |
    v
Workflow runs
    |
    v
Runner pod is deleted
    |
    v
Scale set returns to 0
```

The custom runner image includes tools such as:

- Docker CLI
- AWS CLI
- Terraform
- kubectl
- Helm
- Git
- Python
- jq

The runner platform is separate from the EKS cluster hosting this application.

---

## Deployment Order

For a new environment, the deployment order is:

1. Run Terraform.
2. Confirm that the self-hosted runners are available.
3. Run the runner verification workflow.
4. Upload the datasets and knowledge-base files to S3.
5. Build and push the Docker images.
6. Run the initial training and insert workflow.
7. Deploy the API and frontend.
8. Test the application through the ALB.
9. Run retraining later after enough tickets have been reviewed.

```text
Terraform
    ->
Verify runner
    ->
Build and push images
    ->
Initial training and knowledge-base insert
    ->
Deploy API and frontend
    ->
Review tickets
    ->
Run retraining when needed
```

For normal application changes:

```text
Code change
    ->
Build new images
    ->
Push to ECR
    ->
Deploy new image tags
```

The initial training and insert jobs do not need to run after every code change.

---

## Local Development

The project can also run locally with Docker Compose.

Typical ports:

```text
Frontend: 3000
API:      8000
Database: 5432
```

The local setup was used to test the API, frontend, PostgreSQL, model, and vector retrieval before deploying to AWS.

The exact services and environment variables are defined in:

```text
docker-compose.yaml
```

---

## Configuration

Non-secret configuration is supplied through Kubernetes ConfigMaps.

Examples:

```text
AWS_REGION
DB_HOST
DB_PORT
DB_NAME
DB_SSLMODE
S3_BUCKET_NAME
MODEL_S3_BUCKET
MODEL_S3_KEY
MODEL_LOCAL_PATH
PUBLIC_DATASET_KEY
SYNTHETIC_DATASET_KEY
COMBINED_DATASET_KEY
KNOWLEDGE_BASE_PREFIX
MODEL_PRODUCTION_KEY
MODEL_VERSIONS_PREFIX
RETRAIN_MIN_RECORDS
```

Database credentials are stored in:

```text
service-ticket-db-secret
```

The values are passed from GitHub repository secrets and are not committed to the repository.

---

## Security Choices

This project is not a security-focused application, but I still tried to avoid a few obvious bad practices:

- RDS was deployed privately.
- PostgreSQL connections used SSL.
- Database credentials were stored in a Kubernetes Secret.
- AWS access for pods used EKS Pod Identity instead of hard-coded access keys.
- The API ran as a non-root user.
- Kubernetes workloads had resource requests and limits.
- The API and frontend used readiness and liveness probes.
- The application was exposed through the ALB rather than by exposing pods directly.
- Deployments used generated image tags instead of depending only on `latest`.

These choices reduce some basic risks, but they should not be interpreted as a full security review.

---

## Problems I Ran Into

A large part of this project was debugging the gaps between components.

Some of the main issues were:

- Docker images missing shared Python modules because of the build context
- the API failing Kubernetes `runAsNonRoot`
- readiness and liveness probes pointing to the wrong endpoint
- incorrect S3 key and prefix handling
- pgvector not being initialized before insertion
- Kustomize image names not matching the full ECR repository paths
- the runner not having the standalone `kustomize` binary
- the ALB not being created because the IngressClass was missing
- waiting for ALB DNS propagation
- Kubernetes Jobs failing while `kubectl wait` continued waiting for completion
- the retraining image missing an expected Python module
- understanding why ARC runner pods disappear after each workflow
- cleaning Docker resources too broadly on a shared runner host

These issues were useful because they forced me to understand what each layer was actually doing rather than only following a working example.

---

## Limitations

- The classifier has not been tested on real production ticket traffic.
- The public dataset appears to contain repeated patterns that inflate its train/test score.
- The application is not connected to Request Tracker or another live ticketing system.
- Retraining is triggered manually.
- The API only loads the model during startup.
- There is no authentication system.
- The demo used the generated ALB hostname over HTTP.
- There is no dedicated monitoring or logging stack.
- Database changes are not managed through a migration tool.
- Secrets are passed from GitHub Actions rather than read directly from AWS Secrets Manager.

---

## Possible Next Steps

Some reasonable improvements would be:

- connect the application to a real ticket source
- add authentication
- use HTTPS and a custom domain
- add monitoring and centralized logs
- add database migrations
- move database credentials to AWS Secrets Manager
- add a model approval step before replacing the production model
- trigger retraining automatically once enough reviewed tickets are available
- remove the older `deploy-api-frontend.yaml` workflow
- improve the dataset and evaluation process

---

## Infrastructure Cleanup

The AWS infrastructure was destroyed after testing and screenshots were completed to avoid leaving paid resources running.

```bash
terraform destroy
```

The project can be deployed again by following the deployment order above and reseeding the required S3 objects.

---

## What I Learned

This project helped me understand how much work sits around a machine-learning model once it becomes part of an application.

The main takeaways were:

- how to separate API, frontend, training, insertion, and retraining workloads
- how to store and version model artifacts outside the application image
- how to use PostgreSQL for both relational data and vector search
- how to deploy a multi-service application to Kubernetes
- how to provision AWS resources with Terraform
- how to use Pod Identity instead of static AWS credentials
- how to build deployment workflows that report failures properly
- how ephemeral self-hosted GitHub Actions runners behave
- how to debug issues across Docker, Kubernetes, AWS, and CI/CD

The finished classifier is fairly simple, but building the full system around it was the main purpose of the project.
