# This file is part of tf-mdp.

# tf-mdp is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# tf-mdp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with tf-mdp. If not, see <http://www.gnu.org/licenses/>.


from rddl2tf.compiler import Compiler
from rddl2tf.fluent import TensorFluent
from tfmdp.train.policy import DeepReactivePolicy

import tensorflow as tf

from typing import Iterable, Sequence, Optional, Tuple, Union

Shape = Sequence[int]
FluentTriple = Tuple[str, TensorFluent, TensorFluent]

NonFluentsTensor = Sequence[tf.Tensor]
StateTensor = Sequence[tf.Tensor]
StatesTensor = Sequence[tf.Tensor]
ActionsTensor = Sequence[tf.Tensor]
IntermsTensor = Sequence[tf.Tensor]

CellOutput = Tuple[StatesTensor, ActionsTensor, IntermsTensor, tf.Tensor]
CellState = Sequence[tf.Tensor]

class MRMCell(tf.nn.rnn_cell.RNNCell):

    def __init__(self, compiler: Compiler, policy: DeepReactivePolicy, batch_size: int) -> None:
        self._compiler = compiler
        self._policy = policy
        self._batch_size = batch_size

    @property
    def graph(self) -> tf.Graph:
        '''Returns the computation graph.'''
        return self._compiler.graph

    @property
    def state_size(self) -> Sequence[Shape]:
        '''Returns the MDP state size.'''
        return self._compiler.state_size

    @property
    def action_size(self) -> Sequence[Shape]:
        '''Returns the MDP action size.'''
        return self._compiler.action_size

    @property
    def interm_size(self) -> Sequence[Shape]:
        '''Returns the MDP intermediate state size.'''
        return self._compiler.interm_size

    @property
    def output_size(self) -> Tuple[Sequence[Shape], Sequence[Shape], Sequence[Shape], int, int]:
        '''Returns the simulation cell output size.'''
        return (self.state_size, self.action_size, self.interm_size, 1, 1)

    def initial_state(self) -> StateTensor:
        '''Returns the initial state tensor.'''
        return self._compiler.compile_initial_state(self._batch_size)

    def __call__(self,
            input: tf.Tensor,
            state: Sequence[tf.Tensor],
            scope: Optional[str] = None) -> Tuple[CellOutput, CellState]:

        timestep, stop_flag = tf.split(input, [1, 1], axis=1)

        # action
        action = self._policy(state, input)

        # next state
        transition_scope = self._compiler.transition_scope(state, action)
        interm_fluents, next_state_fluents = self._compiler.compile_probabilistic_cpfs(transition_scope, self._batch_size)

        # log_probs
        log_prob = self._log_prob(interm_fluents, next_state_fluents)

        # reward
        transition_scope.update({name: fluent for name, fluent, _ in next_state_fluents})
        reward = self._compiler.compile_reward(transition_scope)
        reward = reward.tensor

        # outputs
        interm_state = self._output(interm_fluents)
        next_state = self._output(next_state_fluents)
        output = (next_state, action, interm_state, reward, log_prob)

        return (output, next_state)

    def _log_prob(self, interm_fluents, next_state_fluents):

        with self.graph.as_default():

            interm_log_probs = [log_prob.tensor for _, _, log_prob in interm_fluents]
            interm_log_prob = tf.reduce_sum(
                tf.concat(interm_log_probs, axis=1, name='interm_log_probs'),
                axis=1,
                name='interm_log_prob')

            next_state_log_probs = [log_prob.tensor for _, _, log_prob in next_state_fluents]
            next_state_log_prob = tf.reduce_sum(
                tf.concat(next_state_log_probs, axis=1, name='next_state_log_probs'),
                axis=1,
                name='next_state_log_prob')

            log_prob = tf.expand_dims(interm_log_prob + next_state_log_prob, -1, name='log_prob')
            return log_prob

    @classmethod
    def _tensors(cls, fluents: Sequence[FluentTriple]) -> Iterable[tf.Tensor]:
        '''Yields the `fluents`' tensors.'''
        for _, fluent, _ in fluents:
            yield fluent.tensor

    @classmethod
    def _dtype(cls, tensor: tf.Tensor) -> tf.Tensor:
        '''Converts `tensor` to tf.float32 datatype if needed.'''
        if tensor.dtype != tf.float32:
            tensor = tf.cast(tensor, tf.float32)
        return tensor

    @classmethod
    def _output(cls, fluents: Sequence[FluentTriple]) -> Sequence[tf.Tensor]:
        '''Returns output tensors for `fluents`.'''
        return tuple(cls._dtype(t) for t in cls._tensors(fluents))
