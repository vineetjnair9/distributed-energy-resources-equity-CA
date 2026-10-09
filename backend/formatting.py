"""Display formatting shared by the offline builder and the API (no pandas)."""


def _trimmed_decimal(value, places):
    formatted = f"{float(value):,.{places}f}".rstrip("0").rstrip(".")
    return "0" if formatted == "-0" else formatted


def format_metric_value(metric_value, metric_unit):
    """Format a stored metric for people rather than exposing database precision."""
    value = float(metric_value)
    if metric_unit == "share":
        return f"{value:.1%}"
    if metric_unit == "dollars":
        return f"${value:,.0f}"
    if metric_unit in {"chargers", "turbines"}:
        label = metric_unit[:-1] if round(value) == 1 else metric_unit
        return f"{value:,.0f} {label}"
    if metric_unit in {"people", "kWh"}:
        return f"{value:,.0f} {metric_unit}"
    if metric_unit == "degree_days":
        return f"{value:,.0f} degree days"
    if metric_unit == "index":
        return f"{value:,.1f} index points"
    if metric_unit == "MW":
        return f"{_trimmed_decimal(value, 3)} MW"
    if metric_unit == "kWh/m2/day":
        return f"{_trimmed_decimal(value, 2)} kWh/m²/day"
    if metric_unit == "m/s":
        return f"{_trimmed_decimal(value, 2)} m/s"
    return f"{_trimmed_decimal(metric_value, 3)} {metric_unit}".strip()
