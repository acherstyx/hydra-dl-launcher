# -*- coding: utf-8 -*-
# @Time    : 6/24/24
# @Author  : Yaojie Shen
# @Project : hydra-dl-launcher
# @File    : test_hydra_enhanced_sweeper.py

from pytest import mark
from hydra.core.plugins import Plugins
from hydra.plugins.sweeper import Sweeper
from hydra.test_utils.launcher_common_tests import (
    IntegrationTestSuite
)

from hydra_plugins.hydra_enhanced_sweeper.enhanced_sweeper import EnhancedSweeper


def test_discovery() -> None:
    # Tests that this plugin can be discovered via the plugins subsystem when looking for Launchers
    assert EnhancedSweeper.__name__ in [
        x.__name__ for x in Plugins.instance().discover(Sweeper)
    ]


@mark.parametrize(
    "task_launcher_cfg, extra_flags",
    [
        (
                {},
                [
                    "-m",
                    "hydra/job_logging=hydra_debug",
                    "hydra/job_logging=disabled",
                    "hydra/sweeper=enhanced",
                ],
        )
    ],
)
class TestHydraEnhancedSweeperIntegration(IntegrationTestSuite):
    """
    Run this launcher through the integration test suite.
    """

    pass
