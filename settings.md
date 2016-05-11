# settings
#### required

    kubeproxy     # should be the host and port that the kubectl container below provides.
                    usually 127.0.0.1:8001
    k8spassword   # the password for the cluster found in the dev console.

#### optional

    default_infrastructure_backend  # if using Google Container Engine, this should be set to 'gce'
