# -*- coding: utf-8 -*-
# @Time    : 6/24/24
# @Author  : Yaojie Shen
# @Project : hydra-dl-launcher
# @File    : config.py
from dataclasses import dataclass
from hydra.core.config_store import ConfigStore


@dataclass
class SubprocessLauncherConf:
    _target_: str = "hydra_plugins.hydra_subprocess_launcher.subprocess_launcher.SubprocessLauncher"
    start_method: str = "spawn"


ConfigStore.instance().store(
    group="hydra/launcher", name="process", node=SubprocessLauncherConf, provider="hydra"
)
