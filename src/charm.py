#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging

from charms.observability_libs.v0.kubernetes_service_patch import (  # type: ignore
    KubernetesServicePatch,
)
from charms.prometheus_k8s.v0.prometheus_scrape import (  # type: ignore
    MetricsEndpointProvider,
)
from ops.charm import CharmBase
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import Layer

logger = logging.getLogger(__name__)

PROMETHEUS_EDGE_HUB_PORT = 9091
PROMETHEUS_EDGE_HUB_GRPC_PORT = 9092
CHARM_NAME = "prometheus-edge-hub"


class PrometheusEdgeHubCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self._container_name = self._service_name = CHARM_NAME
        self._container = self.unit.get_container(CHARM_NAME)
        self.framework.observe(self.on.prometheus_edge_hub_pebble_ready, self._configure)
        self.framework.observe(self.on.config_changed, self._configure)
        self._service_patcher = KubernetesServicePatch(
            self,
            [
                (CHARM_NAME, PROMETHEUS_EDGE_HUB_PORT, PROMETHEUS_EDGE_HUB_PORT),
                (
                    f"{CHARM_NAME}-grpc",
                    PROMETHEUS_EDGE_HUB_GRPC_PORT,
                    PROMETHEUS_EDGE_HUB_GRPC_PORT,
                ),
            ],
        )
        self.metrics_endpoint_provider = MetricsEndpointProvider(
            self,
            jobs=[
                {
                    "static_configs": [
                        {"targets": [f"{self.app.name}:{PROMETHEUS_EDGE_HUB_PORT}"]}
                    ],
                }
            ],
        )

    def _command(self) -> str:
        """
        Returns the startup command based on configs provided by the user (or the default one if
        none is provided).
        """
        config = self.model.config
        args = [f"-grpc-port={PROMETHEUS_EDGE_HUB_GRPC_PORT}"]
        if config["metrics_count_limit"] != -1:
            args.append(f"-limit={config['metrics_count_limit']}")
        if config["scrape_timeout"] != 10:
            args.append(f"-scrapeTimeout={config['scrape_timeout']}")
        command = ["prometheus-edge-hub"] + args
        return " ".join(command)

    @property
    def _pebble_layer(self) -> Layer:
        """
        Returns the pebble layer
        """
        return Layer(
            {
                "summary": f"{CHARM_NAME} pebble layer",
                "services": {
                    CHARM_NAME: {
                        "summary": CHARM_NAME,
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
        if self._container.can_connect():
            self.unit.status = MaintenanceStatus("Configuring pod")
            plan = self._container.get_plan()
            layer = self._pebble_layer
            if plan.services != layer.services:
                self._container.add_layer(CHARM_NAME, layer, combine=True)
                self._container.restart(CHARM_NAME)
                logger.info(f"Restarted container {CHARM_NAME}")
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for container to be ready...")
            event.defer()


if __name__ == "__main__":
    main(PrometheusEdgeHubCharm)
