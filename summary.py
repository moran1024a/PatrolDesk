from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json


def _ratio(numerator, denominator, scale=1):
    if denominator == 0:
        return "0.00"
    value = Decimal(numerator) * scale / Decimal(denominator)
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def metrics(records):
    counts = Counter(row["status"] for row in records)
    duration = sum(row["duration_s"] for row in records)
    distance = sum(row["distance_m"] for row in records)
    count = len(records)
    return {
        "task_count": count,
        "success_count": counts["success"],
        "failed_count": counts["failed"],
        "cancelled_count": counts["cancelled"],
        "success_rate_pct": _ratio(counts["success"], count, 100),
        "total_duration_s": duration,
        "average_duration_s": _ratio(duration, count),
        "total_distance_m": distance,
    }


def verification_code(payload):
    content = {key: value for key, value in payload.items() if key != "verification_code"}
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "PD-" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16].upper()


def build_summary(records, sources, config):
    by_robot = defaultdict(list)
    by_day = defaultdict(list)
    for row in records:
        by_robot[row["robot_id"]].append(row)
        by_day[row["day"]].append(row)

    totals = metrics(records)
    devices = []
    for robot_id in sorted(config["robots"]):
        devices.append({
            "robot_id": robot_id,
            "robot_name": config["robots"][robot_id],
            **metrics(by_robot[robot_id]),
        })
    days = [{"day": day, **metrics(by_day[day])} for day in sorted(by_day)]
    exceptions = [dict(row) for row in records if row["status"] != "success"]
    payload = {
        "schema_version": 1,
        "site_name": config["site_name"],
        "batch_id": config["batch_id"],
        "period_start": records[0]["day"],
        "period_end": records[-1]["day"],
        "sources": sources,
        "raw_rows": sum(item["raw_rows"] for item in sources),
        "duplicate_rows": sum(item["duplicate_rows"] for item in sources),
        "totals": totals,
        "by_robot": devices,
        "by_day": days,
        "exceptions": exceptions,
    }
    payload["verification_code"] = verification_code(payload)
    return payload

