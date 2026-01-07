# Reinforcement Learning Implementations with Mesa

This repository demonstrates various applications of reinforcement learning (RL) using the Mesa agent-based modeling framework.

<p align="center">
<img src="wolf_sheep/resources/wolf_sheep.gif" width="500" height="400">
</p>

## Getting Started

### Installation

*Given the number of dependencies required, we recommend starting by creating a Conda environment or a Python virtual environment.*
1. **Install Mesa Models**
   Begin by installing the Mesa models:

#TODO: Update this -- do release?

   ```bash
   pip install -U -e git+https://github.com/mesa/mesa-examples@mesa-2.x#egg=mesa-models
   ```

3. **Install RLlib for Multi-Agent Training**
   Next, install RLlib along with TensorFlow and PyTorch to support multi-agent training algorithms:

   ```bash
   pip install "ray[rllib]" tensorflow torch
   ```
#TODO Update requirements to mesa[rec] >3.0

4. **Install Additional Dependencies**
   Finally, install any remaining dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. **Download Pre-Trained Weights**
   Download pre-trained weights from hugging face:

   ```bash
   git clone https://huggingface.co/projectmesa/rl_models/
   ```

### Running the Examples

To test the code, simply execute `example.py`:

```bash
python example.py
```

*Note: Pre-trained models might not work in some cases because of difference in versions of libraries used to train and test.*

To learn about individual implementations, please refer to the README files of specific environments.


## Tutorials

For detailed tutorials on how to use these implementations and guidance on starting your own projects, please refer to [Tutorials.md](./Tutorials.md).

Here's a refined version of your contribution guide:


## Contribution Guide

We welcome contributions to our project! A great way to get started is by implementing the remaining examples listed in the [Mesa-Examples](https://github.com/mesa/mesa-examples) repository with reinforcement learning (RL).

Additionally, if you have your own Mesa environments that you think would benefit from RL integration, we encourage you to share them with us. Simply start an issue on our GitHub repository with your suggestion, and we can collaborate on bringing it to life!