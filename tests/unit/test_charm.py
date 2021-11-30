# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import typing
import unittest
from unittest.mock import patch

from ops.testing import Harness

import charm
from charm import PrometheusEdgeHubCharm

MINIMAL_CONFIG: typing.Mapping = {}
GRPC_PORT = charm.PROMETHEUS_EDGE_HUB_GRPC_PORT


class TestCharm(unittest.TestCase):
    @patch("charm.KubernetesServicePatch", lambda x, y: None)
    def setUp(self):
        self.harness = Harness(PrometheusEdgeHubCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_given_initial_status_when_get_pebble_plan_then_content_is_empty(self):
        initial_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")

    def test_given_pebble_ready_when_get_pebble_plan_then_plan_is_filled_with_service_content(
        self,
    ):
        expected_plan = {
            "services": {
                "prometheus-edge-hub": {
                    "override": "replace",
                    "summary": "prometheus-edge-hub",
                    "startup": "enabled",
                    "command": f"prometheus-edge-hub -grpc-port={GRPC_PORT}",
                },
            },
        }
        self.harness.update_config(MINIMAL_CONFIG)
        container = self.harness.model.unit.get_container("prometheus-edge-hub")
        self.harness.charm.on.prometheus_edge_hub_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.assertEqual(expected_plan, updated_plan)

    def test_given_configs_provided_when_get_pebble_plan_then_plan_is_filled_with_service_content(
        self,
    ):
        config: typing.Mapping = {"metrics_count_limit": 200}
        expected_plan = {
            "services": {
                "prometheus-edge-hub": {
                    "override": "replace",
                    "summary": "prometheus-edge-hub",
                    "startup": "enabled",
                    "command": f"prometheus-edge-hub "
                    f"-grpc-port={GRPC_PORT} "
                    f"-limit={config['metrics_count_limit']}",
                },
            },
        }
        self.harness.update_config(config)
        container = self.harness.model.unit.get_container("prometheus-edge-hub")
        self.harness.charm.on.prometheus_edge_hub_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.assertEqual(expected_plan, updated_plan)

    def test_given_default_configs_provided_when_get_pebble_plan_then_plan_is_filled_with_service_content(  # noqa: E501
        self,
    ):
        config: typing.Mapping = {"metrics_count_limit": -1}
        expected_plan = {
            "services": {
                "prometheus-edge-hub": {
                    "override": "replace",
                    "summary": "prometheus-edge-hub",
                    "startup": "enabled",
                    "command": f"prometheus-edge-hub -grpc-port={GRPC_PORT}",
                },
            },
        }
        self.harness.update_config(config)
        container = self.harness.model.unit.get_container("prometheus-edge-hub")
        self.harness.charm.on.prometheus_edge_hub_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.assertEqual(expected_plan, updated_plan)

    def test_given_default_configs_provided_when_defaults_config_sent_again_then_plan_is_not_changed(  # noqa: E501
        self,
    ):
        config: typing.Mapping = {"metrics_count_limit": -1}
        expected_plan = {
            "services": {
                "prometheus-edge-hub": {
                    "override": "replace",
                    "summary": "prometheus-edge-hub",
                    "startup": "enabled",
                    "command": f"prometheus-edge-hub -grpc-port={GRPC_PORT}",
                },
            },
        }

        container = self.harness.model.unit.get_container("prometheus-edge-hub")
        self.harness.charm.on.prometheus_edge_hub_pebble_ready.emit(container)
        initial_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.harness.update_config(config)
        updated_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.assertEqual(initial_plan, updated_plan)
        self.assertEqual(updated_plan, expected_plan)

    def test_given_default_configs_provided_when_config_change_then_plan_is_changed(self):
        config: typing.Mapping = {"metrics_count_limit": 25}
        expected_initial_plan = {
            "services": {
                "prometheus-edge-hub": {
                    "override": "replace",
                    "summary": "prometheus-edge-hub",
                    "startup": "enabled",
                    "command": f"prometheus-edge-hub -grpc-port={GRPC_PORT}",
                },
            },
        }
        expected_final_plan = {
            "services": {
                "prometheus-edge-hub": {
                    "override": "replace",
                    "summary": "prometheus-edge-hub",
                    "startup": "enabled",
                    "command": f"prometheus-edge-hub -grpc-port={GRPC_PORT}"
                    f" -limit={config['metrics_count_limit']}",
                },
            },
        }

        container = self.harness.model.unit.get_container("prometheus-edge-hub")
        self.harness.charm.on.prometheus_edge_hub_pebble_ready.emit(container)
        initial_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.harness.update_config(config)
        updated_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.assertEqual(initial_plan, expected_initial_plan)
        self.assertEqual(updated_plan, expected_final_plan)
