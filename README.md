# 3D Print Cost Calculator

一个可以部署到 Streamlit Community Cloud 的 3D 打印成本与报价计算器，面向 3D 打印小卖家、打印工作室和定制配件卖家。

应用会根据材料价格、模型重量、打印时间、电费、机器折旧、失败率、人工费、包装费、平台佣金和目标利润率，自动计算材料成本、电费成本、机器折旧成本、人工成本、包装成本、平台手续费、失败率摊销成本、总成本、建议售价、利润、利润率、每小时收益、每单净利润，以及批量订单总成本和总利润。

## 功能

- 单件报价：输入一件模型的成本参数，实时得到建议售价和利润。
- 批量报价：上传 Excel 或 CSV 订单表，逐行计算报价结果。
- 示例订单表：`examples/sample_orders.xlsx` 可直接下载或作为上传模板。
- 内存导出：Excel 和 CSV 导出均通过 `BytesIO` 在内存中生成，不依赖本地输出目录。
- Streamlit Cloud 友好：根目录包含 `app.py` 和 `requirements.txt`。

## 项目结构

```text
3d-print-cost-calculator/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ src/
│  ├─ __init__.py
│  └─ calculator.py
└─ examples/
   └─ sample_orders.xlsx
```

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 部署

1. 将本项目文件推送到 GitHub 仓库。
2. 打开 Streamlit Community Cloud，新建 App。
3. Repository 选择 `3d-print-cost-calculator`。
4. Branch 选择要部署的分支。
5. Main file path 填写：

```text
app.py
```

## 批量订单字段

上传 Excel 或 CSV 时，建议使用以下字段名：

| 字段 | 说明 |
| --- | --- |
| `order_name` | 订单或模型名称 |
| `quantity` | 订单数量 |
| `material_price_per_kg` | 材料价格 / kg |
| `model_weight_g` | 模型重量 / g |
| `material_waste_rate` | 支撑和材料损耗率，例如 `0.08` |
| `print_hours` | 打印小时数 |
| `printer_power_w` | 打印机平均功率 / W |
| `electricity_price_per_kwh` | 电价 / kWh |
| `machine_purchase_price` | 设备购置成本 |
| `machine_lifetime_hours` | 设备折旧寿命 / 小时 |
| `maintenance_cost_per_hour` | 维护与耗材损耗 / 小时 |
| `labor_hours` | 人工小时数 |
| `labor_rate_per_hour` | 人工单价 / 小时 |
| `packaging_cost` | 包装成本 / 单 |
| `other_fixed_cost` | 其他固定成本 / 单 |
| `failure_rate` | 失败率，例如 `0.08` |
| `platform_fee_rate` | 平台佣金率，例如 `0.06` |
| `target_profit_margin` | 目标利润率，例如 `0.30` |
| `override_unit_price` | 手动售价；填 `0` 或留空则使用建议售价 |

缺失字段会使用当前页面中的默认单件报价参数补齐。

## 主要计算公式

```text
材料成本 = 材料单价 / 1000 × 模型重量 × (1 + 支撑 / 损耗率)
电费成本 = 打印机功率 / 1000 × 打印小时 × 电价
机器折旧成本 = (设备购置成本 / 折旧寿命 + 维护损耗 / 小时) × 打印小时
失败率摊销成本 = 基础成本 / (1 - 失败率) - 基础成本
建议售价 = 失败率摊销后成本 / (1 - 平台佣金率 - 目标利润率)
平台手续费 = 售价 × 平台佣金率
利润 = 售价 - 失败率摊销后成本 - 平台手续费
```

平台佣金按售价计算，所以建议售价会反推到同时覆盖成本、失败率摊销、平台手续费和目标利润率。

## 代码说明

- `app.py`：Streamlit 页面、用户输入、结果展示和下载按钮。
- `src/calculator.py`：核心计算逻辑、批量订单处理、内存导出工具。
- `examples/sample_orders.xlsx`：可上传测试的示例订单表。

## 不要提交的内容

不要将本地虚拟环境、Streamlit secrets、本地运行缓存、`work/`、`outputs/` 或手动导出的临时文件提交到 GitHub。
