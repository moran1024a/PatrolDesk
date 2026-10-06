import argparse

from rich.console import Console
from rich.table import Table

from records import load_records
from reporting import write_reports
from settings import DEFAULT_CONFIG, load_settings
from summary import build_summary


def main():
    parser = argparse.ArgumentParser(description="PatrolDesk 巡检报告生成器")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="指定 TOML 配置文件")
    args = parser.parse_args()

    console = Console(markup=False, highlight=False)
    console.rule("PatrolDesk / 巡检记录汇总", style="cyan")
    console.print("读取配置...", style="dim")
    config = load_settings(args.config)
    console.print(f"批次：{config['batch_id']}  场地：{config['site_name']}")
    console.print("导入巡检记录...", style="dim")
    records, sources = load_records(config)
    console.print(f"合并后共 {len(records)} 条，开始汇总...", style="dim")
    payload = build_summary(records, sources, config)
    console.print("生成报告...", style="dim")
    paths = write_reports(payload, config)
    for path in paths:
        console.print(f"  已保存：{path}")

    table = Table(title="设备概况", header_style="bold cyan")
    table.add_column("设备")
    table.add_column("任务数", justify="right")
    table.add_column("失败 / 取消", justify="right")
    table.add_column("成功率", justify="right")
    for row in payload["by_robot"]:
        table.add_row(
            row["robot_name"], str(row["task_count"]),
            f"{row['failed_count']} / {row['cancelled_count']}",
            row["success_rate_pct"] + "%",
        )
    console.print(table)
    totals = payload["totals"]
    console.print(f"完成：{totals['task_count']} 次巡检，成功率 {totals['success_rate_pct']}%", style="green")
    console.print(f"校验码：{payload['verification_code']}", style="bold")


if __name__ == "__main__":
    main()
