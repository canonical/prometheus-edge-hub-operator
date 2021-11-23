# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import patch

from ops.testing import Harness

from charm import PrometheusEdgeHubCharm


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
                    "command": "prometheus-edge-hub -limit=-1 -port=9091 -scrapeTimeout=10",
                },
            },
        }
        container = self.harness.model.unit.get_container("prometheus-edge-hub")
        self.harness.charm.on.prometheus_edge_hub_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("prometheus-edge-hub").to_dict()
        self.assertEqual(expected_plan, updated_plan)
