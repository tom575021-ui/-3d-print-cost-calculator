from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.calculator import (
    DEFAULT_BATCH_COLUMNS,
    PrintJobInput,
    calculate_batch_quotes,
    calculate_single_quote,
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    normalize_order_dataframe,
)


st.set_page_config(
    page_title="3D Print Cost Calculator",
    page_icon="🧮",
    layout="wide",
)


st.markdown(
    """
    <style>
    .block-container { padding-top: 1.8rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.7rem 0.8rem;
        background: #ffffff;
    }
    div[data-testid="stMetricValue"] { font-size: 1.45rem; }
    .small-note { color: #6b7280; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value: float, symbol: str) -> str:
    return f"{symbol}{value:,.2f}"


def percent(value: float) -> str:
    return f"{value:.2%}"


def float_input(
    label: str,
    value: float,
    min_value: float = 0.0,
    max_value: float | None = None,
    step: float = 1.0,
    help_text: str | None = None,
) -> float:
    return float(
        st.number_input(
            label,
            min_value=float(min_value),
            max_value=None if max_value is None else float(max_value),
            value=float(value),
            step=float(step),
            format="%.2f",
            help=help_text,
        )
    )


def int_input(
    label: str,
    value: int,
    min_value: int = 0,
    max_value: int | None = None,
    step: int = 1,
    help_text: str | None = None,
) -> int:
    return int(
        st.number_input(
            label,
            min_value=int(min_value),
            max_value=None if max_value is None else int(max_value),
            value=int(value),
            step=int(step),
            format="%d",
            help=help_text,
        )
    )


def build_input_from_widgets() -> PrintJobInput:
    st.sidebar.header("通用设置")
    st.session_state["currency_symbol"] = st.sidebar.selectbox(
        "货币符号", ["¥", "$", "€"], index=0
    )

    with st.sidebar.expander("默认报价参数", expanded=True):
        default_material_price = float_input("材料价格 / kg", 80.0, step=1.0)
        default_electricity_price = float_input("电价 / kWh", 0.8, step=0.1)
        default_machine_price = float_input("设备购置成本", 2500.0, step=1.0)
        default_machine_lifetime = float_input(
            "设备折旧寿命（小时）", 2500.0, min_value=1.0, step=1.0
        )
        default_maintenance = float_input("维护与耗材损耗 / 小时", 0.5, step=0.1)
        default_labor_rate = float_input("人工单价 / 小时", 35.0, step=1.0)

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        st.subheader("模型与材料")
        order_name = st.text_input("订单 / 模型名称", value="样品零件")
        quantity = int_input(
            "订单数量",
            min_value=1,
            value=1,
            step=1,
            help_text="本次报价的订单数量",
        )
        material_price_per_kg = float_input("材料价格 / kg", default_material_price, step=1.0)
        model_weight_g = float_input("模型重量（g）", 85.0, step=1.0)
        material_waste_rate = float_input(
            "支撑 / 损耗率（%）",
            8.0,
            min_value=0.0,
            max_value=95.0,
            step=0.1,
        ) / 100

    with col_b:
        st.subheader("打印与设备")
        print_hours = float_input("打印时间（小时）", 6.5, min_value=0.1, step=0.1)
        printer_power_w = float_input("打印机平均功率（W）", 120.0, step=1.0)
        electricity_price_per_kwh = float_input("电价 / kWh", default_electricity_price, step=0.1)
        machine_purchase_price = float_input("设备购置成本", default_machine_price, step=1.0)
        machine_lifetime_hours = float_input(
            "设备折旧寿命（小时）", default_machine_lifetime, min_value=1.0, step=1.0
        )
        maintenance_cost_per_hour = float_input(
            "维护与喷嘴等损耗 / 小时", default_maintenance, step=0.1
        )

    with col_c:
        st.subheader("人工与杂费")
        labor_hours = float_input("人工时间（小时）", 0.6, step=0.1)
        labor_rate_per_hour = float_input("人工单价 / 小时", default_labor_rate, step=1.0)
        packaging_cost = float_input("包装成本 / 单", 3.0, step=0.1)
        other_fixed_cost = float_input("其他固定成本 / 单", 2.0, step=0.1)

    with col_d:
        st.subheader("风险与报价")
        failure_rate = float_input(
            "失败率（%）",
            8.0,
            min_value=0.0,
            max_value=95.0,
            step=0.1,
        ) / 100
        platform_fee_rate = float_input(
            "平台佣金 / 手续费（%）",
            6.0,
            min_value=0.0,
            max_value=80.0,
            step=0.1,
        ) / 100
        target_profit_margin = float_input(
            "目标利润率（%）",
            30.0,
            min_value=0.0,
            max_value=90.0,
            step=0.1,
        ) / 100
        override_unit_price = float_input(
            "手动售价 / 件（填 0 使用建议售价）",
            0.0,
            step=1.0,
            help_text="用于对比已有店铺售价；为 0 时按目标利润率自动反推建议售价。",
        )

    return PrintJobInput(
        order_name=order_name,
        quantity=quantity,
        material_price_per_kg=material_price_per_kg,
        model_weight_g=model_weight_g,
        material_waste_rate=material_waste_rate,
        print_hours=print_hours,
        printer_power_w=printer_power_w,
        electricity_price_per_kwh=electricity_price_per_kwh,
        machine_purchase_price=machine_purchase_price,
        machine_lifetime_hours=machine_lifetime_hours,
        maintenance_cost_per_hour=maintenance_cost_per_hour,
        labor_hours=labor_hours,
        labor_rate_per_hour=labor_rate_per_hour,
        packaging_cost=packaging_cost,
        other_fixed_cost=other_fixed_cost,
        failure_rate=failure_rate,
        platform_fee_rate=platform_fee_rate,
        target_profit_margin=target_profit_margin,
        override_unit_price=override_unit_price or None,
    )


def render_single_result(job: PrintJobInput, symbol: str) -> None:
    result = calculate_single_quote(job)
    breakdown = result.to_display_dict()

    st.markdown("### 单件报价结果")
    metric_cols = st.columns(5)
    metric_cols[0].metric("建议售价 / 件", money(result.suggested_unit_price, symbol))
    metric_cols[1].metric("总成本 / 件", money(result.unit_total_cost, symbol))
    metric_cols[2].metric("每单净利润", money(result.order_profit, symbol))
    metric_cols[3].metric("利润率", percent(result.actual_profit_margin))
    metric_cols[4].metric("每小时收益", money(result.profit_per_print_hour, symbol))

    st.markdown(
        '<p class="small-note">平台手续费按售价计算；建议售价会同时覆盖成本、失败率摊销、平台佣金和目标利润率。</p>',
        unsafe_allow_html=True,
    )

    cost_df = pd.DataFrame(
        [
            {"项目": "材料成本", "金额": result.material_cost},
            {"项目": "电费成本", "金额": result.electricity_cost},
            {"项目": "机器折旧成本", "金额": result.machine_cost},
            {"项目": "人工成本", "金额": result.labor_cost},
            {"项目": "包装成本", "金额": result.packaging_cost},
            {"项目": "其他固定成本", "金额": result.other_fixed_cost},
            {"项目": "失败率摊销成本", "金额": result.failure_allowance},
            {"项目": "平台手续费", "金额": result.platform_fee},
        ]
    )

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### 成本拆分")
        st.dataframe(
            cost_df.assign(金额=cost_df["金额"].map(lambda value: money(value, symbol))),
            use_container_width=True,
            hide_index=True,
        )
    with right:
        st.markdown("#### 成本图表")
        st.bar_chart(cost_df.set_index("项目"))

    detail_df = pd.DataFrame([breakdown])
    st.markdown("#### 完整明细")
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    download_cols = st.columns(2)
    download_cols[0].download_button(
        "下载单件报价 Excel",
        data=dataframe_to_excel_bytes(detail_df, sheet_name="Single Quote"),
        file_name="single_3d_print_quote.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    download_cols[1].download_button(
        "下载单件报价 CSV",
        data=dataframe_to_csv_bytes(detail_df),
        file_name="single_3d_print_quote.csv",
        mime="text/csv",
    )


def sample_file_bytes() -> bytes:
    sample_path = Path(__file__).parent / "examples" / "sample_orders.xlsx"
    if sample_path.exists():
        return sample_path.read_bytes()

    fallback = pd.DataFrame(
        [
            {
                "order_name": "PLA 收纳夹",
                "quantity": 10,
                "material_price_per_kg": 80,
                "model_weight_g": 45,
                "material_waste_rate": 0.08,
                "print_hours": 2.2,
                "printer_power_w": 120,
                "electricity_price_per_kwh": 0.8,
                "machine_purchase_price": 2500,
                "machine_lifetime_hours": 2500,
                "maintenance_cost_per_hour": 0.5,
                "labor_hours": 0.25,
                "labor_rate_per_hour": 35,
                "packaging_cost": 2,
                "other_fixed_cost": 1,
                "failure_rate": 0.06,
                "platform_fee_rate": 0.06,
                "target_profit_margin": 0.3,
                "override_unit_price": 0,
            }
        ]
    )
    return dataframe_to_excel_bytes(fallback, sheet_name="Orders")


def render_batch_tab(default_job: PrintJobInput, symbol: str) -> None:
    st.markdown("### 批量订单报价")
    st.write("上传 Excel 或 CSV 后，应用会逐行计算每个订单的建议售价、总成本和利润。")

    template_cols = st.columns([1, 2])
    template_cols[0].download_button(
        "下载示例订单表",
        data=sample_file_bytes(),
        file_name="sample_orders.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    template_cols[1].caption(
        "字段名请使用英文列名；示例表已包含全部支持字段。缺失字段会用当前页面的默认单件参数补齐。"
    )

    uploaded_file = st.file_uploader(
        "上传订单表",
        type=["xlsx", "csv"],
        accept_multiple_files=False,
    )

    if uploaded_file is None:
        st.markdown("#### 支持字段")
        st.dataframe(pd.DataFrame({"column": DEFAULT_BATCH_COLUMNS}), hide_index=True)
        return

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)

        normalized_df = normalize_order_dataframe(raw_df, default_job)
        results_df = calculate_batch_quotes(normalized_df)
    except Exception as exc:  # noqa: BLE001
        st.error(f"无法处理上传文件：{exc}")
        return

    total_cost = float(results_df["order_total_cost"].sum())
    total_revenue = float(results_df["order_revenue"].sum())
    total_profit = float(results_df["order_profit"].sum())
    avg_margin = total_profit / total_revenue if total_revenue else 0.0

    cols = st.columns(4)
    cols[0].metric("批量总成本", money(total_cost, symbol))
    cols[1].metric("批量销售额", money(total_revenue, symbol))
    cols[2].metric("批量总利润", money(total_profit, symbol))
    cols[3].metric("平均利润率", percent(avg_margin))

    st.dataframe(results_df, use_container_width=True, hide_index=True)

    download_cols = st.columns(2)
    download_cols[0].download_button(
        "下载批量结果 Excel",
        data=dataframe_to_excel_bytes(results_df, sheet_name="Batch Quotes"),
        file_name="batch_3d_print_quotes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    download_cols[1].download_button(
        "下载批量结果 CSV",
        data=dataframe_to_csv_bytes(results_df),
        file_name="batch_3d_print_quotes.csv",
        mime="text/csv",
    )


def render_formula_notes() -> None:
    st.markdown("### 主要公式")
    st.markdown(
        """
        - 材料成本 = 材料单价 / 1000 × 模型重量 × (1 + 支撑 / 损耗率)
        - 电费成本 = 打印机功率 / 1000 × 打印小时 × 电价
        - 机器折旧成本 = (设备购置成本 / 折旧寿命 + 维护损耗 / 小时) × 打印小时
        - 失败率摊销成本 = 基础成本 / (1 - 失败率) - 基础成本
        - 建议售价 = 失败率摊销后成本 / (1 - 平台佣金率 - 目标利润率)
        - 平台手续费 = 售价 × 平台佣金率
        - 利润 = 售价 - 失败率摊销后成本 - 平台手续费
        """
    )
    st.info("当平台佣金率 + 目标利润率过高时，建议售价会无法反推，应用会提示降低其中一个比例。")


def main() -> None:
    st.title("3D Print Cost Calculator")
    st.caption("面向 3D 打印小卖家、工作室和定制配件卖家的成本与报价计算器")

    job = build_input_from_widgets()
    symbol = st.session_state.get("currency_symbol", "¥")

    tab_single, tab_batch, tab_formula = st.tabs(["单件报价", "批量订单", "公式说明"])
    with tab_single:
        try:
            render_single_result(job, symbol)
        except ValueError as exc:
            st.error(str(exc))

    with tab_batch:
        render_batch_tab(job, symbol)

    with tab_formula:
        render_formula_notes()


if __name__ == "__main__":
    main()
