# Contributing / Hacking

## Developing and testing

Testing for the charm is done using `tox`. If you don't have it already installed, please install it.
You can then use it like so: 
```shell
tox -e lint      # code style
tox -e static    # static analysis
tox -e unit      # unit tests
```

tox creates virtual environment for every tox environment defined in
[tox.ini](tox.ini). Create and activate a virtualenv with the development requirements:

```bash
source .tox/unit/bin/activate
```

## Integration tests
To run the integration tests suite, run the following commands:
```bash
tox -e integration
```

## OCI Images
Default image: facebookincubator/prometheus-edge-hub:1.1.0

- Reference: [dockerhub](https://hub.docker.com/r/facebookincubator/prometheus-edge-hub)

## Publish

- Pack the charm:
```bash
charmcraft pack
```

- Upload the charm to charmhub:
```bash
charmcraft upload prometheus-edge-hub_ubuntu-20.04-amd64.charm
```

- Upload the OCI image to charmhub:
```bash
charmcraft upload-resource prometheus-edge-hub prometheus-edge-hub-image --image=facebookincubator/prometheus-edge-hub:1.1.0
```

- Release the charm:
```bash
charmcraft release prometheus-edge-hub --revision=1 --channel=edge --resource=prometheus-edge-hub-image:1
```
