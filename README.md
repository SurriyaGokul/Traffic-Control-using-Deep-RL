![image](https://github.com/user-attachments/assets/6d93db8a-2779-4570-80a4-5a21619a2b2b)

# Traffic Control Using PPO Algorithm

This repository contains a project for a traffic control system using the Proximal Policy Optimization (PPO) algorithm. The custom environment simulates traffic signals and vehicles at an intersection, aiming to optimize traffic flow and minimize waiting time.

## Table of Contents

- [Usage](#usage)
- [Project Structure](#project-structure)
- [Custom Environment](#custom-environment)
- [Results](#results)

## Usage
 * Step I: Clone the Repository
```sh
      $ git clone [https://github.com/Feraless/Traffic-Control-using-Deep-RL/tree/main]
```
  * Step II: Install the required packages
```sh
      $ cd traffic-control-ppo
      $ pip install pygame
```
* Step III: Run the training script of the model
```sh
      $ RL.ipynb
```
## Project Structure

-[Traffic.py: Custom traffic control environment]

-[models/: Saved models]

-[RL.ipynb: Training and simulation scripts]

## Custom Environment

The custom environment is designed to simulate a traffic intersection with the following features:

* Four traffic signals
* Each signal has a timer of 10 seconds
* The action taken by the agent adjusts the signal timing
* The observation includes the number of cars passed from each signal and the number of cars waiting at each signal
* The episode ends when all 4 signals have become green
* The reward is -1 multiplied by the total number of cars waiting at the end of the episode plus the total number of cars passed 

## Training the Model

The model is trained using the PPO algorithm from Stable Baselines 3. The training script is located in the RL.ipynb directory.

## Results

After training the model this is the development found to effectively manage traffic.



