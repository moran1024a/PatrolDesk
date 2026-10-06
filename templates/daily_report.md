# {site_name}巡检简报

批次：`{batch_id}`  
统计日期：{period_start} 至 {period_end}

## 本批概况

- 巡检任务：{task_count} 次
- 成功：{success_count} 次；失败：{failed_count} 次；取消：{cancelled_count} 次
- 成功率：{success_rate}%
- 累计耗时：{total_duration_s} 秒，平均每次 {average_duration_s} 秒
- 累计里程：{total_distance_m} 米

## 设备汇总

{device_table}

## 每日汇总

{daily_table}

## 待关注记录

{exception_table}

## 数据来源

共读取 {raw_rows} 条记录，合并 {duplicate_rows} 条重复记录。

{source_list}

校验码：`{verification_code}`

