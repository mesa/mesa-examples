"""
Entry point for CI (and for developers who want a quick sanity check).
Runs the model for a fixed number of steps and exits 0 on success.
"""

from model import Model


def main():
    model = Model(n_agents=10, width=10, height=10)
    for step in range(5):
        model.step()
    print(f"Completed {step + 1} steps — all good.")


if __name__ == "__main__":
    main()
