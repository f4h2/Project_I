# -*- coding: utf-8 -*-
"""project1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1LBRZAp-1zXSaF_YbIo4VtcrbkHtFSO0s
"""

!pip install pygame

pip install gym[classic_control]

import os
os.environ['SDL_VIDEODRIVER']="dummy"
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import random
import gym
import numpy as np
from collections import deque
from keras.models import Model, load_model
from keras.layers import Input, Dense
from keras.optimizers import Adam, RMSprop

def OurModel(input_shape, action_space):
    X_input = Input(input_shape)

    # 'Dense' là đơn vị cơ sở của lớp mạng nơ ron.
    # lớp ẩn với 512 nodes
    X = Dense(512, input_shape=input_shape, activation="relu", kernel_initializer='he_uniform')(X_input)

    # lớp ẩn với 256 nodes
    X = Dense(256, activation="relu", kernel_initializer='he_uniform')(X)

    # lớp ẩn với 64 nodes
    X = Dense(64, activation="relu", kernel_initializer='he_uniform')(X)

    # Lớp đầu ra
    X = Dense(action_space, activation="linear", kernel_initializer='he_uniform')(X)

    model = Model(inputs = X_input, outputs = X, name='CartPole_DQN_model')

    # Biên dịch mô hình:xác định optimizer để kiểm soát tốc độ học tập và hàm mất mát
    model.compile(loss="mse", optimizer=RMSprop(lr=0.00025, rho=0.95, epsilon=0.01), metrics=["accuracy"])

    model.summary()
    return model

class DQNAgent:
    def __init__(self):
        self.env = gym.make('CartPole-v1')

        self.state_size = self.env.observation_space.shape[0]
        self.action_size = self.env.action_space.n
        self.EPISODES = 1000
        self.memory = deque(maxlen=2000)

        self.gamma = 0.95    # Hệ số chiết khấu
        self.epsilon = 1.0   # Tỷ lệ thăm dò: Bao nhiêu để hành động ngẫu nhiên
        self.epsilon_min = 0.001 # Số lượng khám phá ngẫu nhiên tối thiểu được phép
        self.epsilon_decay = 0.999 # Giảm số lượng khám phá ngẫu nhiên khi hiệu suất của tác nhân cải thiện theo thời gian
        self.batch_size = 64    #Xác định dung lượng bộ nhớ mà DQN sẽ sử dụng để huấn luyện;
        self.train_start = 1000

        self.model = OurModel(input_shape=(self.state_size,), action_space = self.action_size)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        if len(self.memory) > self.train_start:
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay

    def act(self, state):
        if np.random.random() <= self.epsilon:    # Nếu hành động ngẫu nhiên, hãy thực hiện hành động ngẫu nhiên
            return random.randrange(self.action_size)
        else:                                     # Nếu không hành động ngẫu nhiên, hãy dự đoán giá trị phần thưởng dựa trên trạng thái hiện tại
            return np.argmax(self.model.predict(state)) #Chọn hành động sẽ cho phần thưởng cao nhất (tức là, đi bên trái hay phải )

    def replay(self):         #  đào tạo NN với những trải nghiệm được lấy mẫu từ bộ nhớ
        if len(self.memory) < self.train_start: #hàm kiểm tra xem số lượng kinh nghiệm trong bộ nhớ có đủ
                                                #  lớn để bắt đầu huấn luyện hay không. Nếu không đủ lớn thì hàm sẽ không thực hiện gì và kết thúc ngay lập tức.
            return
        # lấy mẫu ngẫu nhiên minibatch từ bộ nhớ
        minibatch = random.sample(self.memory, min(len(self.memory), self.batch_size))

        #state và next_state là hai ma trận kích thước (batch_size, state_size) được khởi tạo bằng một ma trận gồm toàn số 0
        state = np.zeros((self.batch_size, self.state_size))
        next_state = np.zeros((self.batch_size, self.state_size))
        action, reward, done = [], [], []

        for i in range(self.batch_size):
            state[i] = minibatch[i][0]
            action.append(minibatch[i][1])
            reward.append(minibatch[i][2])
            next_state[i] = minibatch[i][3]
            done.append(minibatch[i][4])

        #Thực hiện dự đoán giá trị Q cho các trạng thái trong state bằng cách sử dụng mô hình của chúng ta và lưu trữ vào biến target
        #Tương tự, giá trị Q cho các trạng thái tiếp theo trong next_state được dự đoán và lưu trữ vào biến target_next
        target = self.model.predict(state)
        target_next = self.model.predict(next_state)

        for i in range(self.batch_size):
            # hiệu chỉnh giá trị Q cho hành động được sử dụng
            if done[i]:
            #nếu trạng thái hiện tại là trạng thái kết thúc (done[i] == True), giá trị Q cho hành động được thực hiện trong trạng thái đó bằng (reward[i])
                target[i][action[i]] = reward[i]
            else:
            #Nếu không, giá trị Q cho hành động đó được cập nhật bằng tổng của phần thưởng hiện tại và giá trị Q tối đa của trạng thái tiếp theo
                target[i][action[i]] = reward[i] + self.gamma * (np.amax(target_next[i]))

        # Huấn luyện Neural Network với các lô
        self.model.fit(state, target, batch_size=self.batch_size, verbose=2)


    def load(self, name):
        self.model = load_model(name)

    def save(self, name):
        self.model.save(name)

    import matplotlib.pyplot as plt
    def run(self):
        a=[]
        for e in range(self.EPISODES):
            state = self.env.reset()
            state = np.reshape(state, [1, self.state_size])
            done = False
            i = 0
            while not done:
                self.env.render()
                action = self.act(state)   #hành động là 0 hoặc 1;
                next_state, reward, done, _ = self.env.step(action)    # Tác nhân tương tác với Env, nhận phản hồi.
                next_state = np.reshape(next_state, [1, self.state_size])
                if not done or i == self.env._max_episode_steps-1:
                    reward = reward
                else:
                    reward = -100
                self.remember(state, action, reward, next_state, done) # Ghi nhớ trạng thái, hành động, phần thưởng của Timestep trước đó.
                state = next_state
                i += 1
                a.append(i)

                import matplotlib.pyplot as plt

                if done:
                    print("episode: {}/{}, score: {}, e: {:.2}".format(e, self.EPISODES, i, self.epsilon))
                    print(a)
                    plt.plot(a)
                    plt.show()
                    if i == 500:
                        print("Saving trained model as cartpole-dqn.h5")
                        self.save("cartpole-dqn.h5")
                        return
                self.replay()

    def test(self):
        a=[]
        self.load("cartpole-dqn.h5")
        for e in range(self.EPISODES):
            state = self.env.reset()
            state = np.reshape(state, [1, self.state_size])
            done = False
            i = 0
            while not done:
                self.env.render()
                action = np.argmax(self.model.predict(state))
                next_state, reward, done, _ = self.env.step(action)
                state = np.reshape(next_state, [1, self.state_size])
                i += 1
                a.append(i)
                if done:
                    print("episode: {}/{}, score: {}".format(e, self.EPISODES, i))
                    import matplotlib.pyplot as plt
                    plt.plot(a)
                    plt.show()
                    break

if __name__ == "__main__":
    agent = DQNAgent()
    agent.run()
    #agent.test()