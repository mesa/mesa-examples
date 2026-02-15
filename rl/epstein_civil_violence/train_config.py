import os

from model import EpsteinCivilViolenceRL
from ray.rllib.algorithms.ppo import PPOConfig
from ray.rllib.policy.policy import PolicySpec


# Configuration for the PPO algorithm
# You can change the configuration as per your requirements
def env_creator(_):
    return EpsteinCivilViolenceRL(
        width=20,
        height=20,
        citizen_density=0.5,
        cop_density=0.1,
        citizen_vision=4,
        cop_vision=4,
        legitimacy=0.82,
        max_jail_term=10,
    )


config = {
    "env_name": "WorldcopModel-v0",
    "env_creator": env_creator,
    "framework": "torch",
    "train_batch_size": 800,
    "policies": {
        "policy_cop": PolicySpec(config=PPOConfig.overrides(framework_str="torch")),
        "policy_citizen": PolicySpec(config=PPOConfig.overrides(framework_str="torch")),
    },
    "policy_mapping_fn": lambda agent_id, *args, **kwargs: "policy_cop"
    if agent_id[0:3] == "cop"
    else "policy_citizen",
    "policies_to_train": ["policy_cop", "policy_citizen"],
    "num_gpus": int(os.environ.get("RLLIB_NUM_GPUS", "1")),
    "num_learners": 50,
    "num_env_runners": 20,
    "num_envs_per_env_runner": 1,
    "batch_mode": "truncate_episodes",
    "rollout_fragment_length": 40,
}
