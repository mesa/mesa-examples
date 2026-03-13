from math import factorial


def analytical_mmc(arrival_rate, service_rate, c):
    """Compute analytical M/M/c steady-state metrics using the Erlang C formula.

    Returns:
        dict with analytical metrics, or None if system is unstable (rho >= 1).
    """
    rho = arrival_rate / (c * service_rate)
    if rho >= 1.0:
        return None

    a = arrival_rate / service_rate  # offered load

    sum_terms = sum(a**k / factorial(k) for k in range(c))
    last_term = (a**c / factorial(c)) * (1 / (1 - rho))
    p0 = 1.0 / (sum_terms + last_term)

    erlang_c = (a**c / factorial(c)) * (1 / (1 - rho)) * p0

    return {
        "utilization": rho,
        "avg_wait_time": erlang_c / (c * service_rate * (1 - rho)),
        "avg_system_time": erlang_c / (c * service_rate * (1 - rho))
        + 1.0 / service_rate,
        "avg_queue_length": erlang_c * rho / (1 - rho),
        "prob_queuing": erlang_c,
    }
