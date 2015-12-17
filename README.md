# herd-service
A web api exposing herd functionality.

Navigate to the cluster information in the GCE dev console. Click "show credentials" to find the `k8spassword` for the required settings below.

# settings
#### required

    kubeproxy     # should be the host and port that the kubectl container below provides.
                    usually 127.0.0.1:8001
    k8spassword   # the password for the cluster found in the dev console.

#### optional

    default_infrastructure_backend  # if using Google Container Engine, this should be set to 'gce'
    
# Kubernetes deployment

To deploy to kubernetes the pod should include a kubectl container that reverse proxies to the cluster master.

    - name: kubectl
      image: gcr.io/google_containers/kubectl:v0.18.0-120-gaeb4ac55ad12b1-dirty
      imagePullPolicy: Always
      args: ['proxy', '-p', '8001']

The herd service pod needs the cluster credentials mounted in as a secret.
Navigate to the cluster information in the GCE dev console. Click "show credentials" and make `k8s.pem` out of the "Cluster CA Certificate".

Create a secret from that pem and add it to the RepCon.

    volumeMounts:
    - mountPath: /secret
      name: herd-secret-volume
      readOnly: True
    # ...
    - name: herd-secret-volume
      secret:
        secretName: herd    

