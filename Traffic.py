import gym
from gym import spaces
import numpy as np
import random
import pygame
import time
import threading
import sys

class TrafficEnv(gym.Env):

    def __init__(self):
        super(TrafficEnv, self).__init__()
        # Action Space
        self.action_space = spaces.Box(low=0, high=10, shape=(4,), dtype=np.int32)

        # Observation space
        self.observation_space = spaces.Box(low=0, high=100, shape=(8,), dtype=np.int32)

        self.signal_cycles_completed = [False] * 4
        self.signal_cycles_count = [0] * 4  # Count how many cycles each signal has completed
        self.total_cycles_needed = 1
        self.passed_vehicles = [0] * 4

    def reset(self):
        # Default values of signal timers
        self.defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}  # Default green signal time for each direction
        self.defaultRed = 150  # Default red signal time for all directions
        self.defaultYellow = 5  # Default yellow signal time for all directions
        self.signal_cycles_completed = [False] * 4
        self.signal_cycles_count = [0] * 4
        self.total_cycles_needed = 1

        self.signals = []  # List to hold traffic signal objects
        self.noOfSignals = 4  # Total number of signals
        self.currentGreen = 0  # Indicates which signal is green currently
        self.nextGreen = (self.currentGreen + 1) % self.noOfSignals  # Indicates which signal will turn green next
        self.currentYellow = 0  # Indicates whether yellow signal is on or off

        # Average speeds of different types of vehicles
        self.speeds = {'car': 2.25, 'bus': 1.8, 'truck': 1.8, 'bike': 2.5}

        # Coordinates of vehicles' start positions
        self.x = {
            'right': [0, 0, 0],
            'down': [755, 727, 697],
            'left': [1400, 1400, 1400],
            'up': [602, 627, 657]
        }
        self.y = {
            'right': [348, 370, 398],
            'down': [0, 0, 0],
            'left': [498, 466, 436],
            'up': [800, 800, 800]
        }

        # Vehicle data structure to hold vehicles in each direction
        self.vehicles = {
            'right': {0: [], 1: [], 2: [], 'crossed': 0},
            'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0},
            'up': {0: [], 1: [], 2: [], 'crossed': 0}
        }

        # Mapping of vehicle types
        self.vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
        # Mapping of direction numbers
        self.directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

        # Coordinates of signal images, timer, and vehicle count
        self.signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
        self.signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

        # Coordinates of stop lines
        self.stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
        self.defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

        # Gap between vehicles
        self.stoppingGap = 15  # Stopping gap
        self.movingGap = 15  # Moving gap

        # Initialize pygame
        pygame.init()
        self.simulation = pygame.sprite.Group()

        self.observation = np.zeros((8,),dtype= np.int32)
        self.info = {}
        return self.observation

    def step(self, action):
        self.action = action
        thread1 = threading.Thread(name="initialization", target=self.initialize, args=())  # initialization
        thread1.daemon = True
        thread1.start()

        # Colours
        black = (0, 0, 0)
        white = (255, 255, 255)

        # Screensize
        screenWidth = 1400
        screenHeight = 800
        screenSize = (screenWidth, screenHeight)

        # Setting background image i.e. image of intersection
        background = pygame.image.load('images/intersection.png')

        screen = pygame.display.set_mode(screenSize)
        pygame.display.set_caption("SIMULATION")

        # Loading signal images and font
        redSignal = pygame.image.load('images/signals/red.png')
        yellowSignal = pygame.image.load('images/signals/yellow.png')
        greenSignal = pygame.image.load('images/signals/green.png')
        font = pygame.font.Font(None, 30)

        thread2 = threading.Thread(name="generateVehicles", target=self.generateVehicles,
                                   args=())  # Generating vehicles
        thread2.daemon = True
        thread2.start()

        # Initialize the signal cycle tracking
        signal_cycles_completed = [False] * self.noOfSignals
        signal_cycles_start_time = [0] * self.noOfSignals
        done = False

        clock = pygame.time.Clock()  # Create a clock object to control frame rate

        # Variable to track total number of cars passed
        total_cars_passed = 0

        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            screen.blit(background, (0, 0))  # display background in simulation
            for i in range(
                    self.noOfSignals):  # display signal and set timer
                if i == self.currentGreen:
                    if self.currentYellow == 1:
                        self.signals[i].signalText = self.signals[i].yellow
                        screen.blit(yellowSignal, self.signalCoods[i])
                    else:
                        self.signals[i].signalText = self.signals[i].green
                        screen.blit(greenSignal, self.signalCoods[i])
                else:
                    if self.signals[i].red <= 10:
                        self.signals[i].signalText = self.signals[i].red
                    else:
                        self.signals[i].signalText = "---"
                    screen.blit(redSignal, self.signalCoods[i])
            signalTexts = ["", "", "", ""]

            # display signal timer
            for i in range(self.noOfSignals):
                signalTexts[i] = font.render(str(self.signals[i].signalText), True, white, black)
                screen.blit(signalTexts[i], self.signalTimerCoods[i])

            # display the vehicles
            for vehicle in self.simulation:
                screen.blit(vehicle.image, [vehicle.x, vehicle.y])
                vehicle.move(self)
            pygame.display.update()

            # Update signal cycle tracking
            for i in range(self.noOfSignals):
                if self.signals[i].green <= 0 and self.signals[i].red <= 0:
                    if not signal_cycles_completed[i]:
                        # Assume a signal cycle is complete if all 4 signals have completed
                        signal_cycles_completed[i] = True

            # Calculate waiting cars
            waiting_cars = [
                len(self.vehicles[self.directionNumbers[i]][0]) +
                len(self.vehicles[self.directionNumbers[i]][1]) +
                len(self.vehicles[self.directionNumbers[i]][2]) for i in range(self.noOfSignals)]

            # Get remaining time for each signal
            signal_times = [
                self.signals[i].green if i == self.currentGreen and self.currentYellow == 0
                else (self.signals[i].yellow if i == self.currentGreen and self.currentYellow == 1
                      else self.signals[i].red) for i in range(self.noOfSignals)]

            # Update the total number of cars passed
            total_cars_passed = sum([
                vehicle.crossed for vehicle in self.simulation
            ])

            # Construct the observation: [waiting_cars1, waiting_cars2, waiting_cars3, waiting_cars4, total_cars_passed]
            self.observation = np.array(waiting_cars + self.passed_vehicles,dtype=np.int32)

            # Check if all signals have completed their cycles
            if all(signal_cycles_completed):
                # Calculate total number of waiting cars
                total_waiting_cars = sum(waiting_cars)

                # Set the reward as -1 multiplied by the total number of waiting cars plus number of cars passed through
                self.reward = -1 * total_waiting_cars + total_cars_passed
                done = True  # End the episode
            else:
                self.reward = 0  # No reward until the episode ends

        self.info = {}
        return self.observation, self.reward, done, self.info

    def close(self):
        pygame.quit()

    def initialize(self):
        self.ts1 = TrafficSignal(self.defaultRed, self.defaultYellow, self.defaultGreen[0] - self.action[0])
        self.signals.append(self.ts1)
        self.ts2 = TrafficSignal(self.ts1.red + self.ts1.yellow + self.ts1.green, self.defaultYellow, self.defaultGreen[1] - self.action[1])
        self.signals.append(self.ts2)
        self.ts3 = TrafficSignal(self.defaultRed, self.defaultYellow, self.defaultGreen[2] - self.action[2])
        self.signals.append(self.ts3)
        self.ts4 = TrafficSignal(self.defaultRed, self.defaultYellow, self.defaultGreen[3] - self.action[3])
        self.signals.append(self.ts4)
        self.repeat()

    def repeat(self):
        # Loop until the current green signal timer reaches zero
        while self.signals[self.currentGreen].green > 0:  # while the timer of current green signal is not zero
            self.updateValues()
            time.sleep(1)

        self.currentYellow = 1  # set yellow signal on

        # reset stop coordinates of lanes and vehicles
        for i in range(0, 3):
            for vehicle in self.vehicles[self.directionNumbers[self.currentGreen]][i]:
                vehicle.stop = self.defaultStop[self.directionNumbers[self.currentGreen]]

        while self.signals[self.currentGreen].yellow > 0:  # while the timer of current yellow signal is not zero
            self.updateValues()
            time.sleep(1)

        self.currentYellow = 0  # set yellow signal off

        # Reset signal times for the next cycle
        self.signals[self.currentGreen].green = self.defaultGreen[self.currentGreen] - self.action[self.currentGreen]
        self.signals[self.currentGreen].yellow = self.defaultYellow
        self.signals[self.currentGreen].red = self.defaultRed

        # Move to the next signal
        self.currentGreen = self.nextGreen
        self.nextGreen = (self.currentGreen + 1) % self.noOfSignals

        # Set the red time of the next signal based on the green and yellow times of the current signal
        self.signals[self.nextGreen].red = self.signals[self.currentGreen].yellow + self.signals[
            self.currentGreen].green

        # Ensure the signal cycle tracking for the next signal is reset
        signal_cycles_completed = [False] * self.noOfSignals

        # Continue the cycle
        self.repeat()

    # Update values of the signal timers after every second
    def updateValues(self):
        for i in range(0, self.noOfSignals):
            if i == self.currentGreen:
                if self.currentYellow == 0:
                    self.signals[i].green -= 1
                else:
                    self.signals[i].yellow -= 1
            else:
                self.signals[i].red -= 1

    # Generating vehicles in the simulation
    def generateVehicles(self):
        while True:
            vehicle_type = random.randint(0, 3)
            lane_number = random.randint(0, 2)
            temp = random.randint(0, 99)
            direction_number = 0
            dist = [25, 50, 75, 100]
            if temp < dist[0]:
                direction_number = 0
            elif temp < dist[1]:
                direction_number = 1
            elif temp < dist[2]:
                direction_number = 2
            elif temp < dist[3]:
                direction_number = 3
            direction = self.directionNumbers[direction_number]

            print(
                f"Generating vehicle: Type {self.vehicleTypes[vehicle_type]}, Lane {lane_number}, Direction {direction}")

            Vehicle(lane_number, self.vehicleTypes[vehicle_type], direction_number, direction,self)
            time.sleep(1)


class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, traffic_env):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = traffic_env.speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.crossed = 0
        self.vehicles = traffic_env.vehicles
        self.vehicles[direction][lane].append(self)
        self.index = len(self.vehicles[direction][lane])
        path = "images/" + direction + "/" + vehicleClass + ".png"
        self.image = pygame.image.load(path)
        self.signals = traffic_env.signals
        self.currentGreen = traffic_env.currentGreen
        self.currentYellow = traffic_env.currentYellow
        self.stopLines = traffic_env.stopLines
        self.defaultStop = traffic_env.defaultStop
        self.stoppingGap = traffic_env.stoppingGap
        self.movingGap = traffic_env.movingGap
        self.x = traffic_env.x[direction][lane]
        self.y = traffic_env.y[direction][lane]
        if len(self.vehicles[direction][lane]) > 1 and self.vehicles[direction][lane][self.index - 1].crossed == 0:
            if direction == 'right':
                self.stop = self.vehicles[direction][lane][self.index - 1].stop - self.vehicles[direction][lane][self.index - 1].image.get_rect().width - self.stoppingGap
            elif direction == 'left':
                self.stop = self.vehicles[direction][lane][self.index - 1].stop + self.vehicles[direction][lane][self.index - 1].image.get_rect().width + self.stoppingGap
            elif direction == 'down':
                self.stop = self.vehicles[direction][lane][self.index - 1].stop - self.vehicles[direction][lane][self.index - 1].image.get_rect().height - self.stoppingGap
            elif direction == 'up':
                self.stop = self.vehicles[direction][lane][self.index - 1].stop + self.vehicles[direction][lane][self.index - 1].image.get_rect().height + self.stoppingGap
        else:
            self.stop = self.defaultStop[direction]

        if direction == 'right':
            temp = self.image.get_rect().width + self.stoppingGap
            self.x = traffic_env.x[direction][lane] - temp
        elif direction == 'left':
            temp = self.image.get_rect().width + self.stoppingGap
            self.x = traffic_env.x[direction][lane] + temp
        elif direction == 'down':
            temp = self.image.get_rect().height + self.stoppingGap
            self.y = traffic_env.y[direction][lane] - temp
        elif direction == 'up':
            temp = self.image.get_rect().height + self.stoppingGap
            self.y = traffic_env.y[direction][lane] + temp

        traffic_env.simulation.add(self)  # Add vehicle to simulation

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self, traffic_env):
        if (self.direction == 'right'):
            if (self.crossed == 0 and self.x + self.image.get_rect().width > traffic_env.stopLines[self.direction]):
                self.crossed = 1
                traffic_env.passed_vehicles[0] += 1  # Increment crossed count
            if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (
                    traffic_env.currentGreen == 0 and traffic_env.currentYellow == 0)) and (
                    self.index == 0 or self.x + self.image.get_rect().width < (
                    traffic_env.vehicles[self.direction][self.lane][self.index - 1].x - traffic_env.movingGap))):
                self.x += self.speed  # move the vehicle
        elif (self.direction == 'down'):
            if (self.crossed == 0 and self.y + self.image.get_rect().height > traffic_env.stopLines[self.direction]):
                self.crossed = 1
                traffic_env.passed_vehicles[1] += 1 # Increment crossed count
            if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or (
                    traffic_env.currentGreen == 1 and traffic_env.currentYellow == 0)) and (
                    self.index == 0 or self.y + self.image.get_rect().height < (
                    traffic_env.vehicles[self.direction][self.lane][self.index - 1].y - traffic_env.movingGap))):
                self.y += self.speed
        elif (self.direction == 'left'):
            if (self.crossed == 0 and self.x < traffic_env.stopLines[self.direction]):
                self.crossed = 1
                traffic_env.passed_vehicles[2] += 1  # Increment crossed count
            if ((self.x >= self.stop or self.crossed == 1 or (traffic_env.currentGreen == 2 and traffic_env.currentYellow == 0)) and (
                    self.index == 0 or self.x > (
                    traffic_env.vehicles[self.direction][self.lane][self.index - 1].x + traffic_env.vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().width + traffic_env.movingGap))):
                self.x -= self.speed
        elif (self.direction == 'up'):
            if (self.crossed == 0 and self.y < traffic_env.stopLines[self.direction]):
                self.crossed = 1
                traffic_env.passed_vehicles[3] += 1  # Increment crossed count
            if ((self.y >= self.stop or self.crossed == 1 or (traffic_env.currentGreen == 3 and traffic_env.currentYellow == 0)) and (
                    self.index == 0 or self.y > (
                    traffic_env.vehicles[self.direction][self.lane][self.index - 1].y + traffic_env.vehicles[self.direction][self.lane][
                self.index - 1].image.get_rect().height + traffic_env.movingGap))):
                self.y -= self.speed


class TrafficSignal:
    def __init__(self, red, yellow, green):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.signalText = ""
        self.count = 0
