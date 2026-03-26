# viz.py
import matplotlib.pyplot as plt
import pandas as pd


def plot_queue_sizes(df: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["holding_queue_size"], label="Holding queue")
    plt.plot(df["time"], df["takeoff_queue_size"], label="Takeoff queue")
    plt.xlabel("Time")
    plt.ylabel("Queue size")
    plt.title("Airport queue sizes over time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_outcomes(df: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], df["landed"], label="Landed")
    plt.plot(df["time"], df["departed"], label="Departed")
    plt.plot(df["time"], df["diverted"], label="Diverted")
    plt.plot(df["time"], df["cancelled"], label="Cancelled")
    plt.xlabel("Time")
    plt.ylabel("Count")
    plt.title("Airport outcomes over time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_total_congestion(df: pd.DataFrame) -> None:
    total_queue = df["holding_queue_size"] + df["takeoff_queue_size"]

    plt.figure(figsize=(10, 5))
    plt.plot(df["time"], total_queue, label="Total waiting aircraft")
    plt.xlabel("Time")
    plt.ylabel("Aircraft waiting")
    plt.title("Total airport congestion over time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def print_runway_dashboard(model) -> None:
    print("\n=== RUNWAY DASHBOARD ===")
    for runway in model.runways:
        aircraft = runway.current_aircraft
        print(
            {
                "runway": runway.runway_id,
                "mode": runway.mode,
                "operation": runway.operation,
                "occupied": aircraft is not None,
                "aircraft": getattr(aircraft, "flight_id", None),
                "remaining_time": runway.remaining_service_time,
            }
        )


def print_queue_dashboard(model) -> None:
    print("\n=== QUEUE DASHBOARD ===")
    print(f"Holding queue size: {len(model.holding_queue)}")
    print(f"Takeoff queue size: {len(model.takeoff_queue)}")

    holding_snapshot = model.holding_queue.to_list() if hasattr(model.holding_queue, "to_list") else []
    takeoff_snapshot = model.takeoff_queue.to_list() if hasattr(model.takeoff_queue, "to_list") else []

    print("Holding queue aircraft:")
    for a in holding_snapshot[:10]:
        print(
            {
                "flight_id": getattr(a, "flight_id", None),
                "emergency": getattr(a, "emergency", None),
                "fuel_remaining": getattr(a, "fuel_remaining", None),
                "wait_time": getattr(a, "wait_time", None),
                "status": getattr(a, "status", None),
            }
        )

    print("Takeoff queue aircraft:")
    for a in takeoff_snapshot[:10]:
        print(
            {
                "flight_id": getattr(a, "flight_id", None),
                "wait_time": getattr(a, "wait_time", None),
                "status": getattr(a, "status", None),
            }
        )


def show_all_plots(model) -> None:
    df = model.datacollector.get_model_vars_dataframe()
    plot_queue_sizes(df)
    plot_outcomes(df)
    plot_total_congestion(df)
    print_runway_dashboard(model)
    print_queue_dashboard(model)