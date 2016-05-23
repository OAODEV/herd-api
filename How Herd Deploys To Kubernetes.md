# New Build

On kubernetes, herd maintains a few object types for the head of each branch.
It will update everything that needs to be changed when a new iteration is built.

# A service

Named `myservice-mybranch` selecting pods labeled `service: myservice, branch: mybranch`

# A Secret

Based on a guess for the most relevant config
TODO: update this with the new config guess strategy when it's updated.

# A ReplicationController

Named `mybranch-myservice-<commit hash>-<config id>` with labeles `service: myservice, branch: mybranch`


# Deleted Branch (future work)

The objects for the deleted branch will also be deleted in kubernetes.
