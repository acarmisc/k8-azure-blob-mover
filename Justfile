# Define variables
IMAGE_NAME := "azure-storage-mover"
TAG := "latest"

# Recipe to enable the Minikube registry addon
enable-registry:
  minikube addons enable registry

# Recipe to build the Docker image and tag it for the local registry
build:
  docker build -t {{IMAGE_NAME}}:{{TAG}} .

# Recipe to push the built Docker image to the local Minikube registry
push:
  docker push {{IMAGE_NAME}}:{{TAG}}

# Recipe to create or update the Kubernetes secret for the config file
create-config-secret:
  # Use kubectl apply with --dry-run=client to create/update idempotently
  kubectl create secret generic azure-storage-config --from-file=config.toml --dry-run=client -o yaml | kubectl apply -f -

# Recipe to update the deployed job
# This assumes your Kubernetes context is set to your minikube cluster
update-job:
  kubectl apply -f k8s-job.yaml

# Default recipe (optional, runs when you just type 'just')
# This will enable the registry, build the image, push it, create the secret, and update the job
all:
  #just enable-registry
  just build
  #just push
  just create-config-secret
  just update-job
