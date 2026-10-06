import csv
import io
import json

from tabulate import tabulate


METRIC_FIELDS = (
    "task_count", "success_count", "failed_count", "cancelled_count",
    "success_rate_pct", "total_duration_s", "average_duration_s", "total_distance_m",
)


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _table(headers, rows):
    return tabulate(
        [[_cell(cell) for cell in row] for row in rows],
        headers=headers,
        tablefmt="github",
        disable_numparse=True,
        colalign=("left",) * len(headers),
    )


def _markdown(payload, template):
    devices = []
    for row in payload["by_robot"]:
        devices.append((
            row["robot_name"], row["task_count"], row["success_count"],
            row["failed_count"], row["cancelled_count"], row["success_rate_pct"] + "%",
            row["total_duration_s"], row["total_distance_m"],
        ))
    daily = []
    for row in payload["by_day"]:
        daily.append((
            row["day"], row["task_count"], row["success_count"],
            row["failed_count"], row["cancelled_count"], row["success_rate_pct"] + "%",
        ))
    statuses = {"failed": "失败", "cancelled": "取消"}
    exceptions = [
        (row["record_id"], row["robot_id"], row["started_at"], row["area"],
         statuses[row["status"]], row["note"] or "—")
        for row in payload["exceptions"]
    ]
    source_lines = [
        f"- `{row['file']}`：读取 {row['raw_rows']} 条，重复 {row['duplicate_rows']} 条。"
        for row in payload["sources"]
    ]
    context = {
        **payload["totals"],
        "site_name": payload["site_name"],
        "batch_id": payload["batch_id"],
        "period_start": payload["period_start"],
        "period_end": payload["period_end"],
        "raw_rows": payload["raw_rows"],
        "duplicate_rows": payload["duplicate_rows"],
        "verification_code": payload["verification_code"],
        "source_list": "\n".join(source_lines),
        "device_table": _table(
            ("设备", "任务数", "成功", "失败", "取消", "成功率", "耗时/s", "里程/m"), devices
        ),
        "daily_table": _table(("日期", "任务数", "成功", "失败", "取消", "成功率"), daily),
        "exception_table": _table(
            ("任务编号", "设备", "开始时间", "区域", "状态", "备注"), exceptions
        ) if exceptions else "本批次没有失败或取消的任务。",
    }
    return template.format_map(context)


def _csv_text(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row[key] for key in fields})
    return stream.getvalue()


def write_reports(payload, config):
    template = config["template"].read_text(encoding="utf-8")
    report = _markdown(payload, template)
    contents = {
        "report.md": report,
        "summary.json": json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        "devices.csv": _csv_text(("robot_id", "robot_name", *METRIC_FIELDS), payload["by_robot"]),
        "daily.csv": _csv_text(("day", *METRIC_FIELDS), payload["by_day"]),
    }
    output = config["output_dir"]
    output.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in contents.items():
        target = output / name
        # 每份文件先写完，再替换旧产物。
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        temporary.replace(target)
        written.append(target)
    return written
