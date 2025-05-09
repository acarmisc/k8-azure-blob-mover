# Azure Storage Mover Kubernetes Job

This project provides a Python script packaged as a Docker image and a Kubernetes Job definition to move blobs between Azure Storage containers and tag the source blobs.

## Prerequisites

*   Python 3.6 or higher
*   Docker
*   kubectl
*   Access to Azure Storage accounts with necessary permissions.
*   A `config.toml` file with your Azure Storage configuration (see `config.toml-dist` for an example).

## Local Usage

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd k8-azure-storage-mover
    ```
2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3.  Copy `config.toml-dist` to `config.toml` and update it with your Azure Storage connection strings and container names:
    ```bash
    cp config.toml-dist config.toml
    # Edit config.toml with your details
    ```
4.  Run the Python script:
    ```bash
    python main.py
    ```

## Kubernetes Deployment

The project includes a Dockerfile to containerize the Python script and a `k8s-job.yaml` file to define the Kubernetes Job.

### Build and Push Docker Image

Use the provided `Justfile` to build and push the Docker image to your Kubernetes cluster's registry (assuming you are using Minikube with the registry addon enabled).

1.  Enable the Minikube registry addon (if not already enabled):
    ```bash
    just enable-registry
    ```
2.  Build the Docker image:
    ```bash
    just build
    ```
3.  Push the Docker image to the registry:
    ```bash
    just push
    ```

Alternatively, you can manually build and push the image to any Docker registry:

```bash
docker build -t your_registry/azure-storage-mover:latest .
docker push your_registry/azure-storage-mover:latest
```

Make sure to update the `image:` field in `k8s-job.yaml` to point to your pushed image.

### Create Kubernetes Secret for Configuration

Your `config.toml` file contains sensitive information and should not be directly included in the Docker image. Instead, create a Kubernetes Secret from your `config.toml`.

Use the provided `Justfile`:

```bash
just create-config-secret
```

This will create or update a secret named `azure-storage-config` in your current namespace.

Alternatively, you can manually create the secret:

```bash
kubectl create secret generic azure-storage-config --from-file=config.toml
```

### Deploy the Kubernetes Job

The `k8s-job.yaml` file defines the Kubernetes Job that runs your containerized script. It mounts the `azure-storage-config` secret as a file at `/app/config.toml` inside the container.

Apply the Kubernetes Job definition:

Use the provided `Justfile`:

```bash
just update-job
```

Alternatively, you can manually apply the YAML file:

```bash
kubectl apply -f k8s-job.yaml
```

### Monitoring the Job

You can monitor the status of the Kubernetes Job:

```bash
kubectl get jobs
```

To view the logs of the Job's pod:

```bash
kubectl logs <pod_name>
```

Replace `<pod_name>` with the actual name of the pod created by the Job.
