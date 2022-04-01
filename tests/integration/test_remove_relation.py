#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
# See LICENSE file for licensing details.


import asyncio
import logging
from pathlib import Path

import pytest
import requests  # type: ignore
import yaml
from pytest_operator.plugin import OpsTest


logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
app_name = METADATA["name"]
APPLICATION_NAME = "prometheus-edge-hub"
PROMETHEUS_APPLICATION_NAME = "prometheus-k8s"

@pytest.mark.abort_on_fail
async def test_deploy(ops_test,charm_under_test):
    """Deploy the charm-under-test."""
    logger.debug("deploy local charm")
    await ops_test.model.deploy(charm_under_test, application_name=app_name)

    await ops_test.model.add_relation(relation1="prometheus-k8s", relation2=APPLICATION_NAME)

    await asyncio.gather(
        ops_test.model.wait_for_idle(
            apps=[APPLICATION_NAME, "prometheus-k8s"], status="active", timeout=1000
        ),
        ops_test.model.wait_for_idle(
            apps=[PROMETHEUS_APPLICATION_NAME], status="active", timeout=1000
        ),
    )


@pytest.mark.abort_on_fail
async def test_remove_relation(ops_test: OpsTest):
    await ops_test.model.applications[app_name].remove_relation(PROMETHEUS_APPLICATION_NAME, APPLICATION_NAME)
    assert await ops_test.model.wait_for_idle(apps=[app_name], status="blocked", timeout=1000)