# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Optional, Tuple

from pytorch_lightning.loops import Loop
from pytorch_lightning.loops.utilities import (
    _build_training_step_kwargs,
    _check_training_step_output,
    _process_training_step_output,
)
from pytorch_lightning.trainer.connectors.logger_connector.result import ResultCollection


class ManualOptimization(Loop):
    """
    A special loop implementing what is known in Lightning as Manual Optimization where the optimization happens
    entirely in the :meth:`~pytorch_lightning.core.lightning.LightningModule.training_step` and therefore the user
    is responsible for back-propagating gradients and making calls to the optimizers.

    This loop is a trivial case because it performs only a single iteration (calling directly into the module's
    :meth:`~pytorch_lightning.core.lightning.LightningModule.training_step`) and passing through the output(s).
    """

    @property
    def done(self) -> bool:
        return False

    def reset(self) -> None:
        raise NotImplementedError

    def advance(self, *args: Any, **kwargs: Any) -> None:
        """Unimplemented for manual optimization as there is no effective progression of the loop."""
        raise NotImplementedError

    def run(
        self, batch: Any, batch_idx: int, hiddens: Optional[Any] = None
    ) -> Optional[Tuple[ResultCollection, Optional[Any]]]:
        """Performs the training step for manual optimization.

        Args:
            batch: the current tbptt split of the current batch
            batch_idx: the index of the current batch
            hiddens: the model's hidden state of the previous iteration

        Returns:
            post-processed outputs from the training step, or ``None`` if training step returned nothing
        """
        ligtning_module = self.trainer.lightning_module

        with self.trainer.profiler.profile("model_forward"):

            # TODO: does not need optimizers or opt_idx
            step_kwargs = _build_training_step_kwargs(
                ligtning_module, self.trainer.optimizers, batch, batch_idx, opt_idx=None, hiddens=hiddens
            )

            # manually capture logged metrics
            ligtning_module._current_fx_name = "training_step"
            with self.trainer.profiler.profile("training_step"):
                training_step_output = self.trainer.accelerator.training_step(step_kwargs)
                self.trainer.accelerator.post_training_step()

            del step_kwargs

            training_step_output = self.trainer.call_hook("training_step_end", training_step_output)

            _check_training_step_output(ligtning_module, training_step_output)

            result_collection, hiddens = _process_training_step_output(self.trainer, training_step_output)
            if result_collection is None:
                return

        return result_collection, hiddens
