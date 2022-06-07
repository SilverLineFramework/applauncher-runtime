# Custom containers

We use these containers with our docker launcher to start modules.

## Build containers

Run the 'build_push_containers.sh' to build the containers and push to dockerhub.

The script accepts the following optional arguments:
```
  -b            Build only, do not push to dockerhub
```

The file '.secrets.env' **must** define the variables DOCKER_USER and DOCKER_PASSWD. Here is an example .secrets.env:
```
# save to .secrets.env
DOCKER_USER=someuser
DOCKER_PASSWD=somepassword
```

**Then, you can use these containers in the launcher config (`.appsettings.yaml`)**.
