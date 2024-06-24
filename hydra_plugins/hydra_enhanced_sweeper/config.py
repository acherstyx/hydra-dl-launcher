# -*- coding: utf-8 -*-
# @Time    : 2024/3/28
# @Author  : Yaojie Shen
# @Project : hydra-dl-launcher
# @File    : config.py

from dataclasses import dataclass
from hydra.core.config_store import ConfigStore
from typing import Optional, Dict


@dataclass
class EnhancedSweeperConf:
    _target_: str = "hydra_plugins.hydra_enhanced_sweeper.enhanced_sweeper.EnhancedSweeper"
    max_batch_size: Optional[int] = 1
    params: Optional[Dict[str, str]] = None


ConfigStore.instance().store(
    group="hydra/sweeper", name="enhanced", node=EnhancedSweeperConf, provider="custom"
)
