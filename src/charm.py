#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

from charms.observability_libs.v0.kubernetes_service_patch import KubernetesServicePatch
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)

PROMETHEUS_EDGE_HUB_PORT = 9091
PROMETHEUS_EDGE_HUB_GRPC_PORT = 9092


class PrometheusEdgeHubCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self._container_name = self._service_name = "prometheus-edge-hub"
        self._container = self.unit.get_container(self._container_name)
        self.framework.observe(self.on.prometheus_edge_hub_pebble_ready, self._configure)
        self.framework.observe(self.on.config_changed, self._configure)
        self._service_patcher = KubernetesServicePatch(
            self,
            [
                (self._service_name, PROMETHEUS_EDGE_HUB_PORT, PROMETHEUS_EDGE_HUB_PORT),
                (
                    f"{self._service_name}-grpc",
                    PROMETHEUS_EDGE_HUB_GRPC_PORT,
                    PROMETHEUS_EDGE_HUB_GRPC_PORT,
                ),
            ],
        )

    def _command(self) -> str:
        """
        Returns the startup command based on configs provided by the user (or the default one if
        none is provided).
        """
        config = self.model.config
        args = [
            f"-grpc-port={PROMETHEUS_EDGE_HUB_GRPC_PORT}",
        ]
        if config["limit"] != -1:
            args.append(f"-limit={config['limit']}")
        if config["scrape-timeout"] != 10:
            args.append(f"-scrapeTimeout={config['scrape-timeout']}")
        command = ["prometheus-edge-hub"] + args
        return " ".join(command)

    @property
    def _pebble_layer(self) -> Layer:
        """
        Returns the pebble layer
        """
        return Layer(
            {
                "summary": f"{self._service_name} pebble layer",
                "services": {
                    self._service_name: {
                        "summary": self._service_name,
                        "override": "replace",
                        "startup": "enabled",
                        "command": self._command(),
                    },
                },
            }
        )

    def _configure(self, event):
        """
        Configures the pebble layer and patches the Kubernetes services if there's a change to
        be made
        """
        self.unit.status = MaintenanceStatus("Configuring pod")
        plan = self._container.get_plan()
        layer = self._pebble_layer
        if plan.services != layer.services:
            self._container.add_layer(self._container_name, layer, combine=True)
            self._container.restart(self._service_name)
            logger.info(f"Restarted container {self._service_name}")
        self.unit.status = ActiveStatus()


if __name__ == "__main__":
    main(PrometheusEdgeHubCharm)
