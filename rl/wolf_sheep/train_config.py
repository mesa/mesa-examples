import os

from model import WolfSheepRL
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.policy.policy import PolicySpec


# Configuration to train the model
# Feel free to adjust the configuration as necessary
def env_creator(_):
    return WolfSheepRL(
        width=20,
        height=20,
        initial_sheep=100,
        initial_wolves=25,
        sheep_reproduce=0.04,
        wolf_reproduce=0.05,
        wolf_gain_from_food=20,
        grass=True,
        grass_regrowth_time=30,
        sheep_gain_from_food=4,
    )


config = {
    "env_name": "WorldSheepModel-v0",
    "env_creator": env_creator,
    "framework": "torch",  # Assuming you want to use PyTorch
    "train_batch_size": 150,  # Assuming a default value, adjust as necessary
    "policies": {
        "policy_sheep": PolicySpec(config=PPOConfig.overrides(framework_str="torch")),
        "policy_wolf": PolicySpec(config=PPOConfig.overrides(framework_str="torch")),
    },
    "policy_mapping_fn": lambda agent_id, *args, **kwargs: "policy_sheep"
    if agent_id[0:5] == "sheep"
    else "policy_wolf",
    "policies_to_train": ["policy_sheep", "policy_wolf"],
    "num_gpus": int(os.environ.get("RLLIB_NUM_GPUS", "1")),
    "num_learners": 50,  # Assuming a default value, adjust as necessary
    "num_env_runners": 20,  # Assuming a default value, adjust as necessary
    "num_envs_per_env_runner": 1,  # Assuming a default value, adjust as necessary
    "batch_mode": "truncate_episodes",  # Assuming a default value, adjust as necessary
    "rollout_fragment_length": "auto",  # Assuming a default value, adjust as necessary
}
