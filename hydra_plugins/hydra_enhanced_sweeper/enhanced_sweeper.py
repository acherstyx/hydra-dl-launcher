# -*- coding: utf-8 -*-
# @Time    : 2024/3/29
# @Author  : Yaojie Shen
# @Project : hydra-dl-launcher
# @File    : enhanced_sweeper.py


from hydra._internal.core_plugins.basic_sweeper import *


class EnhancedSweeper(BasicSweeper):
    """
    Build launcher for each run.
    """

    def setup(
            self,
            *,
            hydra_context: HydraContext,
            task_function: TaskFunction,
            config: DictConfig,
    ) -> None:
        self.hydra_context = hydra_context
        self.config = config
        self.task_function = task_function

    def sweep(self, arguments: List[str]) -> Any:
        # Make sure batch size is equal to 1 in order to instantiate different launcher for each run
        assert self.max_batch_size == 1, "This sweeper only supports batch_size=1"

        assert self.config is not None
        assert self.hydra_context is not None

        params_conf = self._parse_config()
        params_conf.extend(arguments)

        parser = OverridesParser.create(config_loader=self.hydra_context.config_loader)
        overrides = parser.parse_overrides(params_conf)

        self.overrides = self.split_arguments(overrides, self.max_batch_size)
        returns: List[Sequence[JobReturn]] = []

        # Save sweep run config in top level sweep working directory
        sweep_dir = Path(self.config.hydra.sweep.dir)
        sweep_dir.mkdir(parents=True, exist_ok=True)
        OmegaConf.save(self.config, sweep_dir / "multirun.yaml")

        initial_job_idx = 0
        while not self.is_done():
            batch = self.get_job_batch()
            tic = time.perf_counter()
            # Validate that jobs can be safely composed. This catches composition errors early.
            # This can be a bit slow for large jobs. can potentially allow disabling from the config.
            self.validate_batch_is_legal(batch)
            elapsed = time.perf_counter() - tic
            log.debug(
                f"Validated configs of {len(batch)} jobs in {elapsed:0.2f} seconds, {len(batch) / elapsed:.2f} / second)"
            )

            # Build config and instantiate launcher
            from hydra.core.plugins import Plugins
            sweep_config = self.hydra_context.config_loader.load_sweep_config(self.config, list(list(batch)[0]))
            self.launcher = Plugins.instance().instantiate_launcher(hydra_context=self.hydra_context,
                                                                    task_function=self.task_function,
                                                                    config=sweep_config)
            assert self.launcher is not None

            results = self.launcher.launch(batch, initial_job_idx=initial_job_idx)

            for r in results:
                # access the result to trigger an exception in case the job failed.
                _ = r.return_value

            initial_job_idx += len(batch)
            returns.append(results)

        return returns
