#!/usr/bin/env python3
# Copyright 2021 Guillaume
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.pebble import Layer

logger = logging.getLogger(__name__)


class PrometheusEdgeHubOperatorCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self._service_name = "prometheus-edge-hub"
        self.framework.observe(
            self.on.prometheus_edge_hub_pebble_ready,
            self._on_prometheus_edge_hub_pebble_ready
        )

    def pebble_layer(self):
        return Layer(
            {
                "summary": f"{self._service_name} pebble layer",
                "services": {
                    self._service_name: {
                        "override": "replace",
                        "startup": "enabled",
                        "command": "prometheus-edge-hub -limit=-1 -port=9091 -scrapeTimeout=10",
                    }
                },
            }
        )

    def _on_prometheus_edge_hub_pebble_ready(self, event):
        pass


if __name__ == "__main__":
    main(PrometheusEdgeHubOperatorCharm)
