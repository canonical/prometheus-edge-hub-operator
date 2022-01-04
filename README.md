# prometheus-edge-hub-operator

## Description

Prometheus Edge Hub is a replacement of the Prometheus Pushgateway which allows for the pushing of 
metrics to an endpoint for scraping by prometheus, rather than having Prometheus scrape the metric 
sources directly. Prometheus Edge Hub differs from the Prometheus Pushgateway in several ways, the most important
of which are:
1. Prometheus Edge Hub not overwrite timestamps
2. Metrics in Prometheus Edge Hub persist only until scraped

This project is a Juju charm to deploy Prometheus Edge Hub on Kubernetes.


## Usage

```bash
juju deploy prometheus-edge-hub --config metrics_count_limit=500000
```

### Relating to Prometheus

```bash
juju deploy prometheus-k8s --channel edge
juju relate prometheus-k8s prometheus-edge-hub
```

- References: https://juju.is/docs/lma2
