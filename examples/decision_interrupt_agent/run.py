from .model import DecisionModel


def main():
    model = DecisionModel(n_agents=5)
    for _ in range(20):
        model.step()


if __name__ == "__main__":
    main()
