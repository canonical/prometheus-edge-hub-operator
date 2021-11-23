#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

from ops.charm import CharmBase
from ops.main import main
from ops.model import MaintenanceStatus, ActiveStatus
from ops.pebble import Layer

from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch

logger = logging.getLogger(__name__)


class PrometheusEdgeHubOperatorCharm(CharmBase):

    def __init__(self, *args):
        super().__init__(*args)
        self._container_name = self._service_name = "prometheus-edge-hub"
        self._container = self.unit.get_container(self._container_name)
        self.framework.observe(
            self.on.prometheus_edge_hub_pebble_ready,
            self._on_prometheus_edge_hub_pebble_ready
        )
        self._service_patcher = KubernetesServicePatch(self, [("prometheus-edge-hub", 9091, 9091)])

    @property
    def _pebble_layer(self) -> Layer:
        return Layer(
            {
                "summary": f"{self._service_name} pebble layer",
                "services": {
                    self._service_name: {
                        "override": "replace",
                        "startup": "enabled",
                        "command": "prometheus-edge-hub -limit=-1 -port=9091 -scrapeTimeout=10",
                    },
                },
            }
        )

    def _on_prometheus_edge_hub_pebble_ready(self, event):
        self.unit.status = MaintenanceStatus("Configuring pod")
        plan = self._container.get_plan()
        layer = self._pebble_layer
        if plan.services != layer.services:
            self._container.add_layer(self._container_name, layer, combine=True)
            self._container.restart(self._service_name)
            logger.info(f"Restarted container {self._service_name}")
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(PrometheusEdgeHubOperatorCharm)
