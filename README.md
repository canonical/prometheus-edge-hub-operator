# prometheus-edge-hub-operator

## Description

Prometheus Edge Hub is a replacement of the Prometheus Pushgateway which allows for the pushing of 
metrics to an endpoint for scraping by prometheus, rather than having Prometheus scrape the metric 
sources directly. This differs from the Prometheus Pushgateway in several ways, the most important 
of which being that it does not overwrite timestamps and that metrics do not persist until updated. 
When the hub is scraped, all metrics are drained.


## Usage

TODO: Provide high-level usage, such as required config or relations


## Relations

TODO: Provide any relations which are provided or required by your charm

## OCI Images

TODO: Include a link to the default image your charm uses

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines 
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
