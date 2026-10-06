from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config" / "settings.toml"


def _text(section, key):
    value = section.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"配置项 {key} 必须是非空文本")
    return value.strip()


def _resolve(base, value):
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def load_settings(path):
    path = Path(path).resolve()
    with path.open("rb") as stream:
        data = tomllib.load(stream)
    for name in ("report", "paths", "robots"):
        if not isinstance(data.get(name), dict):
            raise ValueError(f"配置缺少 [{name}] 段")

    report = data["report"]
    paths = data["paths"]
    robots = data["robots"]
    if not robots:
        raise ValueError("至少需要配置一台设备")
    for robot_id, name in robots.items():
        if not robot_id.strip() or not isinstance(name, str) or not name.strip():
            raise ValueError("设备编号和名称不能为空")

    # 配置里的相对路径以配置文件所在目录为准。
    base = path.parent
    config = {
        "site_name": _text(report, "site_name"),
        "batch_id": _text(report, "batch_id"),
        "input_dir": _resolve(base, _text(paths, "input_dir")),
        "output_dir": _resolve(base, _text(paths, "output_dir")),
        "template": _resolve(base, _text(paths, "template")),
        "robots": {key: value.strip() for key, value in robots.items()},
    }
    if not config["input_dir"].is_dir():
        raise FileNotFoundError(f"巡检数据目录不存在：{config['input_dir']}")
    if not config["template"].is_file():
        raise FileNotFoundError(f"报告模板不存在：{config['template']}")
    if config["output_dir"] == config["input_dir"]:
        raise ValueError("输出目录不能与输入目录相同")
    return config

