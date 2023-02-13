#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
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


def validate_scrape_target_is_added_to_prometheus(prometheus_address: str):
    scrape_targets = get_scrape_targets(prometheus_address)
    validate_scrape_targets(scrape_targets)


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    charm = await ops_test.build_charm(".")
    resources = {
        f"{APPLICATION_NAME}-image": METADATA["resources"][f"{APPLICATION_NAME}-image"][
            "upstream-source"
        ],
    }

    await asyncio.gather(
        ops_test.model.deploy(
            PROMETHEUS_APPLICATION_NAME,
            application_name=PROMETHEUS_APPLICATION_NAME,
            channel="edge",
        ),
        ops_test.model.deploy(
            charm, resources=resources, application_name=APPLICATION_NAME, trust=True
        ),
    )

    await ops_test.model.add_relation(relation1="prometheus-k8s", relation2=APPLICATION_NAME)

    await asyncio.gather(
        ops_test.model.wait_for_idle(
            apps=[APPLICATION_NAME, "prometheus-k8s"], status="active", timeout=1000
        ),
        ops_test.model.wait_for_idle(
            apps=[PROMETHEUS_APPLICATION_NAME], status="active", timeout=1000
        ),
    )
    prometheus_k8s_unit = ops_test.model.units[f"{PROMETHEUS_APPLICATION_NAME}/0"]
    prometheus_k8s_private_address = prometheus_k8s_unit.data["private-address"]
    validate_scrape_target_is_added_to_prometheus(prometheus_k8s_private_address)


async def test_remove_relation(ops_test: OpsTest):
    await ops_test.model.applications["prometheus-edge-hub"].remove_relation(
        "metrics-endpoint", "prometheus-k8s"
    )
    await ops_test.model.wait_for_idle(apps=["prometheus-edge-hub"], status="active", timeout=1000)
