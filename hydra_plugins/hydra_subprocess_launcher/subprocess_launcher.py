# -*- coding: utf-8 -*-
# @Time    : 2024/3/31
# @Author  : Yaojie Shen
# @Project : hydra-dl-launcher
# @File    : subprocess_launcher.py
import copy
import logging
from pathlib import Path
from typing import List, Optional, Sequence

from .spawn import start_processes
import pickle
import cloudpickle

from omegaconf import DictConfig, open_dict

from hydra.core.utils import (
    JobReturn,
    configure_log,
    filter_overrides,
    run_job,
    setup_globals,
)
from hydra.core.singleton import Singleton
from hydra.core.hydra_config import HydraConfig
from hydra.plugins.launcher import Launcher
from hydra.types import HydraContext, TaskFunction

log = logging.getLogger(__name__)


class SubprocessLauncher(Launcher):
    def __init__(self, start_method: str) -> None:
        super().__init__()
        self.config: Optional[DictConfig] = None
        self.task_function: Optional[TaskFunction] = None
        self.hydra_context: Optional[HydraContext] = None
        self.start_method = start_method

    def setup(
            self,
            *,
            hydra_context: HydraContext,
            task_function: TaskFunction,
            config: DictConfig,
    ) -> None:
        self.config = config
        self.hydra_context = hydra_context
        self.task_function = task_function

    def launch(
            self, job_overrides: Sequence[Sequence[str]], initial_job_idx: int
    ) -> Sequence[JobReturn]:
        setup_globals()
        assert self.hydra_context is not None
        assert self.config is not None
        assert self.task_function is not None

        configure_log(self.config.hydra.hydra_logging, self.config.hydra.verbose)
        sweep_dir = self.config.hydra.sweep.dir
        Path(str(sweep_dir)).mkdir(parents=True, exist_ok=True)
        log.info(f"Launching {len(job_overrides)} jobs locally")
        runs: List[JobReturn] = []
        for idx, overrides in enumerate(job_overrides):
            idx = initial_job_idx + idx
            lst = " ".join(filter_overrides(overrides))
            log.info(f"\t#{idx} : {lst}")
            sweep_config = self.hydra_context.config_loader.load_sweep_config(
                self.config, list(overrides)
            )
            with open_dict(sweep_config):
                sweep_config.hydra.job.id = idx
                sweep_config.hydra.job.num = idx
            ret = run_job(
                hydra_context=self.hydra_context,
                task_function=run_in_subprocess(
                    self.task_function,
                    start_method=self.start_method,
                    task_config=self.config
                ),
                config=sweep_config,
                job_dir_key="hydra.sweep.dir",
                job_subdir_key="hydra.sweep.subdir",
                configure_logging=False
            )
            runs.append(ret)
            configure_log(self.config.hydra.hydra_logging, self.config.hydra.verbose)
        return runs


def run_in_subprocess(task_function, start_method: str, task_config: DictConfig):
    def wrapped_function(*args):
        log.info(f"Running task in subprocess...")
        start_processes(
            run_pickled_task_function,
            args=[
                cloudpickle.dumps(task_function),
                cloudpickle.dumps(args),
                cloudpickle.dumps(task_config),
                cloudpickle.dumps(Singleton.get_state())
            ],
            nprocs=1,
            join=True,
            daemon=False,
            start_method=start_method
        )

    return wrapped_function


def run_pickled_task_function(
        n_proc,
        dumped_task_function,
        dumped_args,
        dumped_task_config,
        dumped_singleton_state
):
    assert n_proc == 0
    task_function = pickle.loads(dumped_task_function)
    args = pickle.loads(dumped_args)
    task_config = pickle.loads(dumped_task_config)
    singleton_state = pickle.loads(dumped_singleton_state)

    # Add hydra config and task config together to fix interpolation
    Singleton.set_state(singleton_state)
    config = copy.deepcopy(task_config)
    config.hydra = HydraConfig.instance().cfg.hydra

    configure_log(config.hydra.job_logging, config.hydra.verbose)

    return task_function(*args)
