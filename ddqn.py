from collections import deque
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

import numpy as np
import random
import os


def to_array(arr):
    """ converts a python list object to a numpy array """
    return np.reshape(arr, newshape=(1, len(arr)))


def predict(network, state):
    """ predicts an action from a network for the current state """
    return network.predict(to_array(state))[0]


class Agent:
    def __init__(self):
        self.epsilon = 1
        self.epsilon_min = 0.001
        self.games = 500
        self.batch_size = 64
        self.iterations = self.games * self.batch_size
        self.epsilon_decay = (self.epsilon - self.epsilon_min) / self.iterations
        self.replay_memory_size = 500_000
        self.sync_target_steps = 10_000
        self.discount_rate = 0.99
        self.memory = deque(maxlen=self.replay_memory_size)
        self.q_network = self.create_network('weights.h5')
        self.t_network = self.create_network()

    def create_network(self, filename=''):
        network = Sequential()
        network.add(Dense(128, input_dim=200, activation='tanh'))
        network.add(Dense(25, activation='linear'))
        if os.path.isfile(filename):
            network.load_weights(filename)

        network.compile(loss='mse', optimizer=Adam(lr=0.00025))

    def predict(self, state, legal_actions):
        if self.epsilon > self.epsilon_min:
            self.epsilon -= self.epsilon_decay

        if np.random.uniform() <= self.epsilon:
            return random.choice(legal_actions)

        q_values = predict(self.q_network, state)
        actions = sorted(range(len(q_values)),
                         key=lambda i: q_values[i], reverse=True)

        for action in actions:
            if action in legal_actions:
                return action

    def learn(self):
        batch = random.sample(self.memory, self.batch_size)
        for state, action, reward, state_ in batch:
            future_reward = self.discount_rate * \
                np.amax(predict(self.t_network, state_))
            q_value = reward * (1 + future_reward)
            target = predict(self.q_network, state)
            target[action] = q_value
            self.q_network.fit(to_array(state), to_array(target),
                               epochs=1, verbose=0)
