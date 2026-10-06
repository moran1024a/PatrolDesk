import csv
from datetime import datetime


FIELDS = (
    "record_id", "robot_id", "started_at", "area", "status",
    "duration_s", "distance_m", "note",
)
STATUSES = {"success", "failed", "cancelled"}


def _integer(value, field, where):
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{where}：{field} 必须为整数") from exc
    if number < 0:
        raise ValueError(f"{where}：{field} 不能为负数")
    return number


def _parse(row, robots, where):
    if None in row or any(value is None for value in row.values()):
        raise ValueError(f"{where}：字段数量与表头不一致")
    row = {key: value.strip() for key, value in row.items()}
    for key in FIELDS:
        if key != "note" and not row[key]:
            raise ValueError(f"{where}：{key} 不能为空")
    if row["robot_id"] not in robots:
        raise ValueError(f"{where}：未知设备 {row['robot_id']}")
    if row["status"] not in STATUSES:
        raise ValueError(f"{where}：未知状态 {row['status']}")
    try:
        started = datetime.strptime(row["started_at"], "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise ValueError(f"{where}：时间格式应为 YYYY-MM-DD HH:MM:SS") from exc

    duration = _integer(row["duration_s"], "duration_s", where)
    distance = _integer(row["distance_m"], "distance_m", where)
    return {
        "record_id": row["record_id"],
        "robot_id": row["robot_id"],
        "started_at": started.strftime("%Y-%m-%d %H:%M:%S"),
        "day": started.date().isoformat(),
        "area": row["area"],
        "status": row["status"],
        "duration_s": row["duration_s"],
        "distance_m": distance,
        "note": row["note"],
    }


def load_records(config):
    files = sorted(config["input_dir"].glob("*.csv"))
    if not files:
        raise ValueError("数据目录中没有 CSV 文件")
    unique = {}
    sources = []
    for path in files:
        raw_count = 0
        duplicate_count = 0
        # Excel 导出的 UTF-8 文件有时带 BOM。
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)) or set(headers) != set(FIELDS):
                raise ValueError(f"{path.name}：CSV 表头与约定不一致")
            for row in reader:
                if all(value is not None and value == "" for value in row.values()):
                    continue
                raw_count += 1
                record = _parse(row, config["robots"], f"{path.name}:{reader.line_num}")
                record_id = record["record_id"]
                if record_id in unique:
                    if unique[record_id] != record:
                        raise ValueError(f"{path.name}：记录 {record_id} 重复且内容不一致")
                    duplicate_count += 1
                else:
                    unique[record_id] = record
        sources.append({
            "file": path.name,
            "raw_rows": raw_count,
            "duplicate_rows": duplicate_count,
        })
        print(f"  {path.name}：读取 {raw_count} 条，重复 {duplicate_count} 条")

    if not unique:
        raise ValueError("没有可供统计的巡检记录")
    records = sorted(unique.values(), key=lambda item: (item["started_at"], item["record_id"]))
    return records, sources

