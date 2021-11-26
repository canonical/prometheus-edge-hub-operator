# prometheus-edge-hub-operator

## Description

Prometheus Edge Hub is a replacement of the Prometheus Pushgateway which allows for the pushing of 
metrics to an endpoint for scraping by prometheus, rather than having Prometheus scrape the metric 
sources directly. This differs from the Prometheus Pushgateway in several ways, the most important 
of which being that it does not overwrite timestamps and that metrics do not persist until updated. 
When the hub is scraped, all metrics are drained.

This project is a Juju charm to deploy Prometheus Edge Hub on Kubernetes.


## Usage

For now, you have to build the charm yourself before deploying it. Please refer to CONTRIBUTING.md
for more information on the build itself. Once it is built, you can deploy the charm using 
`juju deploy`: 

```bash
juju deploy ./prometheus-edge-hub_ubuntu-20.04-amd64.charm \
 --config limit=500000 \
 --resource prometheus-edge-hub-image=facebookincubator/prometheus-edge-hub:1.1.0
```

### Relating to Prometheus

```bash
juju deploy prometheus-k8s --channel edge
juju relate prometheus-k8s prometheus-edge-hub
```

## OCI Images

Default image: facebookincubator/prometheus-edge-hub:1.1.0

## Contributing

Please see the `CONTRIBUTING.md` for developer guidance.
