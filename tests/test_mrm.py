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

import rddlgym
from rddl2tf.compiler import Compiler

from tfmdp.train.policy import DeepReactivePolicy
from tfmdp.train.mrm import MRMCell, MarkovRecurrentModel, ReparameterizationType

import numpy as np
import tensorflow as tf

import unittest


class TestMRMCell(unittest.TestCase):

    def setUp(self):
        self.rddl1 = rddlgym.make('Navigation-v2', mode=rddlgym.AST)
        self.compiler1 = Compiler(self.rddl1, batch_mode=True)

        self.layers = [64, 32, 16]
        self.policy1 = DeepReactivePolicy(self.compiler1, self.layers, tf.nn.elu, input_layer_norm=True)

        self.batch_size1 = 100
        self.cell1 = MRMCell(self.compiler1, self.policy1, self.batch_size1)

    def test_state_size(self):
        expected1 = ((2,),)
        actual1 = self.cell1.state_size
        self.assertTupleEqual(actual1, expected1)

    def test_output_size(self):
        expected1 = (((2,),), ((2,),), ((2,), (2,)), 1, 1)
        actual1 = self.cell1.output_size
        self.assertTupleEqual(actual1, expected1)

    def test_initial_state(self):
        cells = [self.cell1]
        batch_sizes = [self.batch_size1]
        for cell, batch_size in zip(cells, batch_sizes):
            initial_state = cell.initial_state()
            self.assertIsInstance(initial_state, tuple)
            self.assertEqual(len(initial_state), len(cell.state_size))
            for t, shape in zip(initial_state, cell.state_size):
                self.assertIsInstance(t, tf.Tensor)
                expected_shape = [batch_size] + list(shape)
                if len(expected_shape) == 1:
                    expected_shape += [1]
                self.assertListEqual(t.shape.as_list(), expected_shape)

    def test_output_simulation_step(self):
        horizon = 40
        cells = [self.cell1]
        batch_sizes = [self.batch_size1]
        for cell, batch_size in zip(cells, batch_sizes):
            with cell.graph.as_default():
                # initial_state
                initial_state = cell.initial_state()

                # timestep
                timestep = tf.constant(horizon, dtype=tf.float32)
                timestep = tf.expand_dims(timestep, -1)
                timestep = tf.stack([timestep] * batch_size)

                # stop_flag
                stop_flag = tf.constant(0.0, shape=(batch_size,1), dtype=tf.float32)

                input = tf.concat([timestep, stop_flag], axis=1)

                # simulation step
                output, _ = cell(input, initial_state)
                self.assertIsInstance(output, tuple)
                self.assertEqual(len(output), 5)

    def test_next_state_output(self):
        horizon = 40
        cells = [self.cell1]
        batch_sizes = [self.batch_size1]
        for cell, batch_size in zip(cells, batch_sizes):
            with cell.graph.as_default():
                # initial_state
                initial_state = cell.initial_state()

                # timestep
                timestep = tf.constant(horizon, dtype=tf.float32)
                timestep = tf.expand_dims(timestep, -1)
                timestep = tf.stack([timestep] * batch_size)

                # stop_flag
                stop_flag = tf.constant(0.0, shape=(batch_size,1), dtype=tf.float32)

                input = tf.concat([timestep, stop_flag], axis=1)

                # simulation step
                output, _ = cell(input, initial_state)
                next_state, _, _, _, _ = output
                next_state_size, _, _, _, _ = cell.output_size

                self.assertIsInstance(next_state, tuple)
                self.assertEqual(len(next_state), len(next_state_size))
                for s, sz in zip(next_state, next_state_size):
                    self.assertIsInstance(s, tf.Tensor)
                    self.assertEqual(s.dtype, tf.float32)
                    self.assertListEqual(s.shape.as_list(), [batch_size] + list(sz))

    def test_action_output(self):
        horizon = 40
        cells = [self.cell1]
        batch_sizes = [self.batch_size1]
        for cell, batch_size in zip(cells, batch_sizes):
            with cell.graph.as_default():
                # initial_state
                initial_state = cell.initial_state()

                # timestep
                timestep = tf.constant(horizon, dtype=tf.float32)
                timestep = tf.expand_dims(timestep, -1)
                timestep = tf.stack([timestep] * batch_size)

                # stop_flag
                stop_flag = tf.constant(0.0, shape=(batch_size,1), dtype=tf.float32)

                input = tf.concat([timestep, stop_flag], axis=1)

                # simulation step
                output, _ = cell(input, initial_state)
                _, action, _, _, _ = output
                _, action_size, _, _, _ = cell.output_size

                self.assertIsInstance(action, tuple)
                self.assertEqual(len(action), len(action_size))
                for a, sz in zip(action, action_size):
                    self.assertIsInstance(a, tf.Tensor)
                    self.assertEqual(a.dtype, tf.float32)
                    self.assertListEqual(a.shape.as_list(), [batch_size] + list(sz))

    def test_reward_output(self):
        horizon = 40
        cells = [self.cell1]
        batch_sizes = [self.batch_size1]
        for cell, batch_size in zip(cells, batch_sizes):
            with cell.graph.as_default():
                # initial_state
                initial_state = cell.initial_state()

                # timestep
                timestep = tf.constant(horizon, dtype=tf.float32)
                timestep = tf.expand_dims(timestep, -1)
                timestep = tf.stack([timestep] * batch_size)

                # stop_flag
                stop_flag = tf.constant(0.0, shape=(batch_size,1), dtype=tf.float32)

                input = tf.concat([timestep, stop_flag], axis=1)

                # simulation step
                output, _ = cell(input, initial_state)
                _, _, _, reward, _ = output
                _, _, _, reward_size, _ = cell.output_size

                self.assertIsInstance(reward, tf.Tensor)
                self.assertListEqual(reward.shape.as_list(), [batch_size, reward_size])

    def test_log_prob_output(self):
        horizon = 40
        cells = [self.cell1]
        batch_sizes = [self.batch_size1]
        for cell, batch_size in zip(cells, batch_sizes):
            with cell.graph.as_default():
                # initial_state
                initial_state = cell.initial_state()

                # timestep
                timestep = tf.constant(horizon, dtype=tf.float32)
                timestep = tf.expand_dims(timestep, -1)
                timestep = tf.stack([timestep] * batch_size)

                # stop_flag
                stop_flag = tf.constant(0.0, shape=(batch_size,1), dtype=tf.float32)

                input = tf.concat([timestep, stop_flag], axis=1)

                # simulation step
                output, _ = cell(input, initial_state)
                _, _, _, _, log_prob = output
                _, _, _, _, log_prob_size = cell.output_size

                self.assertIsInstance(log_prob, tf.Tensor)
                self.assertListEqual(log_prob.shape.as_list(), [batch_size, log_prob_size])


class TestMarkovRecurrentModel(unittest.TestCase):

    def setUp(self):
        self.rddl1 = rddlgym.make('Navigation-v2', mode=rddlgym.AST)
        self.compiler1 = Compiler(self.rddl1, batch_mode=True)

        self.layers = [64, 32, 16]
        self.policy1 = DeepReactivePolicy(self.compiler1, self.layers, tf.nn.elu, input_layer_norm=True)

        self.batch_size1 = 100
        self.mrm1 = MarkovRecurrentModel(self.compiler1, self.policy1, self.batch_size1)

    def test_timesteps(self):
        horizon = 40
        simulators = [self.mrm1]
        batch_sizes = [self.batch_size1]

        for mrm, batch_size in zip(simulators, batch_sizes):

            with mrm.graph.as_default():
                timesteps = mrm.timesteps(horizon)

            self.assertIsInstance(timesteps, tf.Tensor)
            self.assertListEqual(timesteps.shape.as_list(), [batch_size, horizon, 1])

            with tf.Session(graph=mrm.graph) as sess:
                timesteps = sess.run(timesteps)

                for t in timesteps:
                    self.assertListEqual(list(t), list(np.arange(horizon-1, -1, -1)))

    def test_stop_flags(self):
        horizon = 40
        simulators = [self.mrm1]
        batch_sizes = [self.batch_size1]

        for mrm, batch_size in zip(simulators, batch_sizes):

            with mrm.graph.as_default():

                stop_flags1 = mrm.stop_flags(horizon, ReparameterizationType.FULLY_REPARAMETERIZED)
                self.assertIsInstance(stop_flags1, tf.Tensor)
                self.assertListEqual(stop_flags1.shape.as_list(), [batch_size, horizon, 1])

                stop_flags2 = mrm.stop_flags(horizon, ReparameterizationType.NOT_REPARAMETERIZED)
                self.assertIsInstance(stop_flags2, tf.Tensor)
                self.assertListEqual(stop_flags2.shape.as_list(), [batch_size, horizon, 1])

                with tf.Session(graph=mrm.graph) as sess:
                    stop_flags1, stop_flags2 = sess.run([stop_flags1, stop_flags2])
                    self.assertTrue(np.all(stop_flags1 == np.zeros((batch_size, horizon, 1))))
                    self.assertTrue(np.all(stop_flags2 == np.ones((batch_size, horizon, 1))))

    def test_inputs(self):
        horizon = 40
        simulators = [self.mrm1]
        batch_sizes = [self.batch_size1]

        for mrm, batch_size in zip(simulators, batch_sizes):

            with mrm.graph.as_default():

                timesteps = mrm.timesteps(horizon)

                flags1 = mrm.stop_flags(horizon, ReparameterizationType.FULLY_REPARAMETERIZED)
                inputs1 = mrm.inputs(timesteps, flags1)
                self.assertIsInstance(inputs1, tf.Tensor)
                self.assertListEqual(inputs1.shape.as_list(), [batch_size, horizon, 2])

                flags2 = mrm.stop_flags(horizon, ReparameterizationType.NOT_REPARAMETERIZED)
                inputs2 = mrm.inputs(timesteps, flags2)
                self.assertIsInstance(inputs2, tf.Tensor)
                self.assertListEqual(inputs2.shape.as_list(), [batch_size, horizon, 2])

                with tf.Session(graph=mrm.graph) as sess:
                    inputs1, inputs2 = sess.run([inputs1, inputs2])

                    for t in inputs1:
                        self.assertListEqual(list(t[:,0]), list(np.arange(horizon-1, -1, -1)))

                    for t in inputs2:
                        self.assertListEqual(list(t[:,0]), list(np.arange(horizon-1, -1, -1)))

                    self.assertTrue(np.all(inputs1[:,:,1] == np.zeros((batch_size, horizon))))
                    self.assertTrue(np.all(inputs2[:,:,1] == np.ones((batch_size, horizon))))

    def test_trajectory_fully_reparameterized(self):
        self._test_trajectory(ReparameterizationType.FULLY_REPARAMETERIZED)

    def test_trajectory_not_reparameterized(self):
        self._test_trajectory(ReparameterizationType.NOT_REPARAMETERIZED)

    def _test_trajectory(self, reparam_type):
        horizon = 40
        compilers = [self.compiler1]
        simulators = [self.mrm1]
        batch_sizes = [self.batch_size1]

        for compiler, mrm, batch_size in zip(compilers, simulators, batch_sizes):

            with mrm.graph.as_default():
                initial_state = mrm._cell.initial_state()

                timesteps = mrm.timesteps(horizon)
                flags = mrm.stop_flags(horizon, reparam_type)
                inputs = mrm.inputs(timesteps, flags)

                trajectory = mrm.trajectory(initial_state, inputs)

            self.assertIsInstance(trajectory, tuple)
            self.assertEqual(len(trajectory), 6)

            # sizes
            state_size, action_size, interm_size, reward_size, log_prob_size = mrm.output_size

            # states
            self.assertIsInstance(trajectory.states, tuple)
            self.assertEqual(len(trajectory[1]), len(state_size))
            for s, sz in zip(trajectory[1], state_size):
                self.assertIsInstance(s, tf.Tensor)
                self.assertListEqual(s.shape.as_list(), [batch_size, horizon] + list(sz), '{}'.format(s))

            # interms
            self.assertIsInstance(trajectory.interms, tuple)
            self.assertEqual(len(trajectory.interms), len(interm_size))
            for s, sz in zip(trajectory.interms, interm_size):
                self.assertIsInstance(s, tf.Tensor)
                self.assertListEqual(s.shape.as_list(), [batch_size, horizon] + list(sz), '{}'.format(s))

            # actions
            self.assertIsInstance(trajectory.actions, tuple)
            self.assertEqual(len(trajectory.actions), len(action_size))
            for a, sz in zip(trajectory.actions, action_size):
                self.assertIsInstance(a, tf.Tensor)
                self.assertListEqual(a.shape.as_list(), [batch_size, horizon] + list(sz))

            # rewards
            self.assertIsInstance(trajectory.rewards, tf.Tensor)
            self.assertListEqual(trajectory.rewards.shape.as_list(), [batch_size, horizon, reward_size])

            # log_probs
            self.assertIsInstance(trajectory.log_probs, tf.Tensor)
            self.assertListEqual(trajectory.log_probs.shape.as_list(), [batch_size, horizon, log_prob_size])

    def test_reward_to_go(self):
        horizon = 40
        compilers = [self.compiler1]
        simulators = [self.mrm1]
        batch_sizes = [self.batch_size1]

        for compiler, mrm, batch_size in zip(compilers, simulators, batch_sizes):

            with mrm.graph.as_default():
                initial_state = mrm._cell.initial_state()

                timesteps = mrm.timesteps(horizon)
                flags = mrm.stop_flags(horizon, ReparameterizationType.NOT_REPARAMETERIZED)
                inputs = mrm.inputs(timesteps, flags)

                trajectory = mrm.trajectory(initial_state, inputs)
                q = mrm.reward_to_go(trajectory.rewards)

            self.assertIsInstance(q, tf.Tensor)
            self.assertEqual(q.dtype, tf.float32)
            self.assertEqual(q.shape, trajectory.rewards.shape)
