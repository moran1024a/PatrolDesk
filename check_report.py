import argparse
import csv
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_csv(path, expected, identity):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        actual = list(reader)
        fields = reader.fieldnames
    require(len(actual) == len(expected), f"{path.name} 行数与 JSON 不一致")
    require(bool(expected) and set(fields or []) == set(expected[0]), f"{path.name} 表头不一致")
    require([row[identity] for row in actual] == [str(row[identity]) for row in expected],
            f"{path.name} 的分组或顺序不一致")
    for index, (row, reference) in enumerate(zip(actual, expected), 2):
        require(row == {key: str(value) for key, value in reference.items()},
                f"{path.name} 第 {index} 行与 JSON 不一致")


def check(output):
    payload = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    code = payload["verification_code"]
    content = {key: value for key, value in payload.items() if key != "verification_code"}
    encoded = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    expected_code = "PD-" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16].upper()
    require(code == expected_code, "JSON 校验码与内容不一致")
    require(payload["schema_version"] == 1, "不支持的报告版本")
    total = payload["totals"]
    require(total["task_count"] > 0, "报告没有巡检记录")
    count_fields = ("task_count", "success_count", "failed_count", "cancelled_count",
                    "total_duration_s", "total_distance_m")
    for group in ("by_robot", "by_day"):
        require(bool(payload[group]), f"{group} 不能为空")
        for field in count_fields:
            require(sum(row[field] for row in payload[group]) == total[field],
                    f"{group} 的 {field} 合计与总览不一致")
    require(total["success_count"] + total["failed_count"] + total["cancelled_count"]
            == total["task_count"], "状态数量合计不一致")
    require(payload["raw_rows"] - payload["duplicate_rows"] == total["task_count"],
            "去重前后记录数不一致")
    require(sum(row["raw_rows"] for row in payload["sources"]) == payload["raw_rows"],
            "来源记录数不一致")
    require(sum(row["duplicate_rows"] for row in payload["sources"]) == payload["duplicate_rows"],
            "来源重复数不一致")
    require(len(payload["exceptions"]) == total["failed_count"] + total["cancelled_count"],
            "异常任务清单数量不一致")
    check_csv(output / "devices.csv", payload["by_robot"], "robot_id")
    check_csv(output / "daily.csv", payload["by_day"], "day")
    report = (output / "report.md").read_text(encoding="utf-8")
    for value in (payload["site_name"], payload["batch_id"], code):
        require(value in report, "Markdown 报告缺少场地、批次或校验码")
    return code


def main():
    parser = argparse.ArgumentParser(description="检查 PatrolDesk 导出文件的一致性")
    parser.add_argument("output", nargs="?", default=str(Path(__file__).resolve().parent / "output"))
    args = parser.parse_args()
    try:
        code = check(Path(args.output))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"检查未通过：{exc}\n")
    print(f"检查通过：4 份文件一致，校验码 {code}")


if __name__ == "__main__":
    main()

