# herd-service
A web api exposing herd functionality.

# settings
#### required

    kubernetes_master_host
    kubernetes_admin_password
    
# Kubernetes deployment

To deploy to kubernetes the pod should include a kubectl container that reverse proxies to the cluster master.

    - name: kubectl
      image: gcr.io/google_containers/kubectl:v0.18.0-120-gaeb4ac55ad12b1-dirty
      imagePullPolicy: Always
      args: ['proxy', '-p', '8001']

The herd service pod needs the cluster credentials mounted in as a secret.
Navigate to the cluster information in the GCE dev console
