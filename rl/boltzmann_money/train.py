import argparse

from model import NUM_AGENTS, BoltzmannWealthModelRL
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback


def rl_model(args):
    # Create the environment
    env = BoltzmannWealthModelRL(N=NUM_AGENTS, width=NUM_AGENTS, height=NUM_AGENTS)
    eval_env = BoltzmannWealthModelRL(N=NUM_AGENTS, width=NUM_AGENTS, height=NUM_AGENTS)
    eval_callback = EvalCallback(
        eval_env, best_model_save_path="./logs/", log_path="./logs/", eval_freq=5000
    )
    # Define the PPO model
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./logs/")

    # Train the model
    model.learn(total_timesteps=args.stop_timesteps, callback=[eval_callback])

    # Save the model
    model.save("ppo_money_model")


if __name__ == "__main__":
    # Define the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stop-timesteps",
        type=int,
        default=NUM_AGENTS * 100,
        help="Number of timesteps to train.",
    )
    args = parser.parse_args()
    rl_model(args)
