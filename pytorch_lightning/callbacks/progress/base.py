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
from pytorch_lightning.callbacks import Callback


class ProgressBarBase(Callback):
    r"""
    The base class for progress bars in Lightning. It is a :class:`~pytorch_lightning.callbacks.Callback`
    that keeps track of the batch progress in the :class:`~pytorch_lightning.trainer.trainer.Trainer`.
    You should implement your highly custom progress bars with this as the base class.

    Example::

        class LitProgressBar(ProgressBarBase):

            def __init__(self):
                super().__init__()  # don't forget this :)
                self.enable = True

            def disable(self):
                self.enable = False

            def on_train_batch_end(self, trainer, pl_module, outputs):
                super().on_train_batch_end(trainer, pl_module, outputs)  # don't forget this :)
                percent = (self.train_batch_idx / self.total_train_batches) * 100
                sys.stdout.flush()
                sys.stdout.write(f'{percent:.01f} percent complete \r')

        bar = LitProgressBar()
        trainer = Trainer(callbacks=[bar])

    """

    def __init__(self):

        self._trainer = None
        self._train_batch_idx = 0
        self._val_batch_idx = 0
        self._test_batch_idx = 0
        self._predict_batch_idx = 0

    @property
    def trainer(self):
        return self._trainer

    @property
    def train_batch_idx(self) -> int:
        """
        The current batch index being processed during training.
        Use this to update your progress bar.
        """
        return self._train_batch_idx

    @property
    def val_batch_idx(self) -> int:
        """
        The current batch index being processed during validation.
        Use this to update your progress bar.
        """
        return self._val_batch_idx

    @property
    def test_batch_idx(self) -> int:
        """
        The current batch index being processed during testing.
        Use this to update your progress bar.
        """
        return self._test_batch_idx

    @property
    def predict_batch_idx(self) -> int:
        """
        The current batch index being processed during predicting.
        Use this to update your progress bar.
        """
        return self._predict_batch_idx

    @property
    def total_train_batches(self) -> int:
        """
        The total number of training batches during training, which may change from epoch to epoch.
        Use this to set the total number of iterations in the progress bar. Can return ``inf`` if the
        training dataloader is of infinite size.
        """
        return self.trainer.num_training_batches

    @property
    def total_val_batches(self) -> int:
        """
        The total number of validation batches during validation, which may change from epoch to epoch.
        Use this to set the total number of iterations in the progress bar. Can return ``inf`` if the
        validation dataloader is of infinite size.
        """
        total_val_batches = 0
        if self.trainer.enable_validation:
            is_val_epoch = (self.trainer.current_epoch + 1) % self.trainer.check_val_every_n_epoch == 0
            total_val_batches = sum(self.trainer.num_val_batches) if is_val_epoch else 0

        return total_val_batches

    @property
    def total_test_batches(self) -> int:
        """
        The total number of testing batches during testing, which may change from epoch to epoch.
        Use this to set the total number of iterations in the progress bar. Can return ``inf`` if the
        test dataloader is of infinite size.
        """
        return sum(self.trainer.num_test_batches)

    @property
    def total_predict_batches(self) -> int:
        """
        The total number of predicting batches during testing, which may change from epoch to epoch.
        Use this to set the total number of iterations in the progress bar. Can return ``inf`` if the
        predict dataloader is of infinite size.
        """
        return sum(self.trainer.num_predict_batches)

    def disable(self):
        """
        You should provide a way to disable the progress bar.
        The :class:`~pytorch_lightning.trainer.trainer.Trainer` will call this to disable the
        output on processes that have a rank different from 0, e.g., in multi-node training.
        """
        raise NotImplementedError

    def enable(self):
        """
        You should provide a way to enable the progress bar.
        The :class:`~pytorch_lightning.trainer.trainer.Trainer` will call this in e.g. pre-training
        routines like the :ref:`learning rate finder <advanced/lr_finder:Learning Rate Finder>`
        to temporarily enable and disable the main progress bar.
        """
        raise NotImplementedError

    def print(self, *args, **kwargs):
        """
        You should provide a way to print without breaking the progress bar.
        """
        print(*args, **kwargs)

    def on_init_end(self, trainer):
        self._trainer = trainer

    def on_train_start(self, trainer, pl_module):
        self._train_batch_idx = trainer.fit_loop.batch_idx

    def on_train_epoch_start(self, trainer, pl_module):
        self._train_batch_idx = 0

    def on_train_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        self._train_batch_idx += 1

    def on_validation_start(self, trainer, pl_module):
        self._val_batch_idx = 0

    def on_validation_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        self._val_batch_idx += 1

    def on_test_start(self, trainer, pl_module):
        self._test_batch_idx = 0

    def on_test_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        self._test_batch_idx += 1

    def on_predict_epoch_start(self, trainer, pl_module):
        self._predict_batch_idx = 0

    def on_predict_batch_end(self, trainer, pl_module, outputs, batch, batch_idx, dataloader_idx):
        self._predict_batch_idx += 1
