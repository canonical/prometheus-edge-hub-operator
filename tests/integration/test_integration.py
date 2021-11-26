#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import time
from pathlib import Path

import pytest
import requests
import yaml
from pytest_operator.plugin import OpsTest  # type: ignore

logger = logging.getLogger(__name__)
METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())

APPLICATION_NAME = "prometheus-edge-hub"
PROMETHEUS_APPLICATION_NAME = "prometheus-k8s"


def get_scrape_targets(prometheus_address: str):
    url = f"http://{prometheus_address}:9090/api/v1/targets"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def validate_scrape_targets(scrape_targets: dict, edge_hub_address: str):
    active_targets = scrape_targets["data"]["activeTargets"]
    scrape_urls = [active_target["scrapeUrl"] for active_target in active_targets]
    edge_hub_metrics_endpoint = f"http://{edge_hub_address}:9091/metrics"
    assert edge_hub_metrics_endpoint in scrape_urls


def validate_scrape_target_is_added_to_prometheus(prometheus_address: str, edge_hub_address: str):
    start_time = time.time()
    timeout = 120
    while time.time() - start_time < timeout:
        try:
            scrape_targets = get_scrape_targets(prometheus_address)
            return validate_scrape_targets(scrape_targets, edge_hub_address)
        except Exception as e:
            logger.info(e)
            logger.info("Failed retrieving scrape target, will retry in 5 seconds")
        time.sleep(5)
    raise TimeoutError(f"Timeout retrieving scrape target after {timeout} seconds")


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest):
    charm = await ops_test.build_charm(".")
    resources = {
        f"{APPLICATION_NAME}-image": METADATA["resources"][f"{APPLICATION_NAME}-image"][
            "upstream-source"
        ],
    }
    await ops_test.model.deploy(
        PROMETHEUS_APPLICATION_NAME, application_name=PROMETHEUS_APPLICATION_NAME, channel="edge"
    )
    await ops_test.model.deploy(
        charm, resources=resources, application_name=APPLICATION_NAME, trust=True
    )
    await ops_test.model.add_relation(relation1="prometheus-k8s", relation2=APPLICATION_NAME)
    await ops_test.model.wait_for_idle(
        apps=[APPLICATION_NAME, "prometheus-k8s"], status="active", timeout=1000
    )
    await ops_test.model.wait_for_idle(
        apps=[PROMETHEUS_APPLICATION_NAME], status="active", timeout=1000
    )
    prometheus_k8s_unit = ops_test.model.units[f"{PROMETHEUS_APPLICATION_NAME}/0"]
    prometheus_edge_hub_unit = ops_test.model.units[f"{APPLICATION_NAME}/0"]
    prometheus_k8s_private_address = prometheus_k8s_unit.data["private-address"]
    prometheus_edge_hub_private_address = prometheus_edge_hub_unit.data["private-address"]
    assert validate_scrape_target_is_added_to_prometheus(
        prometheus_k8s_private_address, prometheus_edge_hub_private_address
    )
