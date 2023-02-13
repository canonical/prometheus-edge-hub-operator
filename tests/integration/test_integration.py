#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import time
from pathlib import Path

import pytest
import requests
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)
METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())

APPLICATION_NAME = "prometheus-edge-hub"
PROMETHEUS_APPLICATION_NAME = "prometheus-k8s"


class TestPrometheusEdgeHub:
    @pytest.fixture(scope="module")
    @pytest.mark.abort_on_fail
    async def setup(self, ops_test: OpsTest):
        await ops_test.model.set_config({"update-status-hook-interval": "2s"})  # type: ignore[union-attr]  # noqa: E501
        await self._deploy_prometheus_k8s(ops_test)

    @pytest.fixture(scope="module")
    @pytest.mark.abort_on_fail
    async def build_and_deploy(self, ops_test: OpsTest, setup):
        charm = await ops_test.build_charm(".")
        resources = {
            f"{APPLICATION_NAME}-image": METADATA["resources"][f"{APPLICATION_NAME}-image"][
                "upstream-source"
            ],
        }

        await ops_test.model.deploy(  # type: ignore[union-attr]
            charm, resources=resources, application_name=APPLICATION_NAME, trust=True
        )

    @pytest.mark.abort_on_fail
    async def test_wait_for_active_status(self, ops_test, build_and_deploy):
        await ops_test.model.wait_for_idle(apps=[APPLICATION_NAME], status="active", timeout=1000)

    @pytest.mark.abort_on_fail
    async def test_scrape_target_added_to_prometheus(self, ops_test, build_and_deploy):
        await ops_test.model.add_relation(relation1="prometheus-k8s", relation2=APPLICATION_NAME)
        await ops_test.model.wait_for_idle(
            apps=[APPLICATION_NAME, "prometheus-k8s"], status="active", timeout=1000
        )

        prometheus_k8s_unit = ops_test.model.units[f"{PROMETHEUS_APPLICATION_NAME}/0"]
        prometheus_k8s_private_address = prometheus_k8s_unit.data["private-address"]
        validate_scrape_target_is_added_to_prometheus(prometheus_k8s_private_address)

    async def test_remove_relation(self, ops_test, build_and_deploy):
        await ops_test.model.applications["prometheus-edge-hub"].remove_relation(
            "metrics-endpoint", "prometheus-k8s"
        )
        await ops_test.model.wait_for_idle(apps=[APPLICATION_NAME], status="active", timeout=1000)

    @staticmethod
    async def _deploy_prometheus_k8s(ops_test: OpsTest):
        await ops_test.model.deploy(  # type: ignore[union-attr]
            PROMETHEUS_APPLICATION_NAME, application_name=PROMETHEUS_APPLICATION_NAME
        )


def validate_scrape_target_is_added_to_prometheus(prometheus_address: str):
    scrape_targets = get_scrape_targets(prometheus_address)
    validate_scrape_targets(scrape_targets)


def get_scrape_targets(prometheus_address: str):
    url = f"http://{prometheus_address}:9090/api/v1/targets"
    start_time = time.time()
    timeout = 120
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.info(e)
            logger.info("Failed retrieving scrape target, will retry in 5 seconds")
        time.sleep(5)
    raise TimeoutError(f"Timeout retrieving scrape target after {timeout} seconds")


def validate_scrape_targets(scrape_targets: dict):
    active_targets = scrape_targets["data"]["activeTargets"]
    assert len(active_targets) == 2
    prometheus_edge_hub_target = active_targets[0]
    assert prometheus_edge_hub_target["scrapePool"].endswith(
        "prometheus-edge-hub_prometheus_scrape"
    )
    assert prometheus_edge_hub_target["scrapeUrl"].endswith(":9091/metrics")
