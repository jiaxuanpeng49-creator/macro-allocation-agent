"""支持当前建议和30年历史回测的宏观资产配置 Agent。"""

import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel, set_tracing_disabled

from backtest import backtest_summary
from ai_bubble_diagnosis import compact_diagnosis
from knowledge_base import knowledge_answer_context
from news_intelligence import latest_news_context
from personal_allocation import run_personalized_allocation
from pipeline import run_macro_analysis

load_dotenv()

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
if not deepseek_api_key:
    raise ValueError("没有找到 DEEPSEEK_API_KEY，请检查 .env 文件")

deepseek_client = AsyncOpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
deepseek_model = OpenAIChatCompletionsModel(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    openai_client=deepseek_client,
)
set_tracing_disabled(True)


@function_tool
def analyze_macro_portfolio() -> str:
    """分析当前宏观环境、经济周期、资产得分和股票债券黄金建议权重。"""
    return json.dumps(run_macro_analysis(), ensure_ascii=False, indent=2)


@function_tool
def backtest_macro_portfolio(
    benchmark: str = "equal_weight",
    cost_bps: float = 10,
    temperature: float = 3.0,
) -> str:
    """
    回测宏观配置 Agent 在1995–2025年的历史表现。

    benchmark 可选：sixty_forty（60/40股债）、equal_weight（股债金各1/3）、
    stock（纯股票）。cost_bps 是每次换仓的交易成本，temperature 控制配置集中度。
    """
    result = backtest_summary(
        cost_bps=cost_bps,
        benchmark=benchmark,
        temperature=temperature,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@function_tool
def search_ai_bubble_views(question: str, top_k: int = 5) -> str:
    """检索知识库中各位投资人、科技公司CEO和AI专家对AI泡沫的观点与原始来源。"""
    result = knowledge_answer_context(question, top_k=max(1, min(top_k, 8)))
    return json.dumps(result, ensure_ascii=False, indent=2)


@function_tool
def diagnose_current_ai_bubble() -> str:
    """使用 Ray Dalio 公开的六项泡沫指标，综合判断当前 AI 泡沫阶段、结论和下一阶段触发条件。"""
    return json.dumps(compact_diagnosis(), ensure_ascii=False, indent=2)


@function_tool
def analyze_latest_market_news(top_k: int = 12) -> str:
    """读取最近一次每日新闻快照，返回规则底稿、DeepSeek综合研判、资产与周期影响和原始链接。"""
    return json.dumps(latest_news_context(top_k=max(3, min(top_k, 20))), ensure_ascii=False, indent=2)


@function_tool
def create_personalized_allocation(
    age: int,
    occupation: str,
    monthly_income: float,
    monthly_expenses: float,
    liquid_assets: float,
    high_interest_debt: float,
    dependents: int,
    horizon_years: int,
    max_loss_pct: float,
    risk_willingness: int,
    investment_experience: int,
) -> str:
    """结合个人职业收入、现金流、风险能力、投资期限和当前宏观环境生成约束后的资产配置。"""
    result = run_personalized_allocation(
        age=age,
        occupation=occupation,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        liquid_assets=liquid_assets,
        high_interest_debt=high_interest_debt,
        dependents=dependents,
        horizon_years=horizon_years,
        max_loss_pct=max_loss_pct,
        risk_willingness=risk_willingness,
        investment_experience=investment_experience,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


macro_agent = Agent(
    name="宏观资产配置助手",
    model=deepseek_model,
    instructions="""
你是一个用于金融工程研究的宏观资产配置助手。

当用户只询问当前宏观环境、当前经济周期、资产得分或因子贡献时，调用 analyze_macro_portfolio。
当用户询问“当前应该怎么配置”时，若没有个人资料，先说明最终配置必须结合个人情况并收集必要字段；
资料齐全后直接调用 create_personalized_allocation。不要把 analyze_macro_portfolio 的原始权重当成个人最终建议。

当用户询问历史表现、30年回测、累计收益、年化收益、最大回撤、能否跑赢基准、交易成本影响，
或者“如果几十年前开始使用会怎样”时，必须调用 backtest_macro_portfolio。

当用户询问 AI 是否存在泡沫、某位大佬如何看 AI 泡沫、不同人物观点比较、AI 估值、
资本开支是否过度或泡沫破裂信号时，必须调用 search_ai_bubble_views。

当用户要求当前 AI 泡沫的总判断、所处阶段、Dalio模型、综合结论或未来触发条件时，
必须调用 diagnose_current_ai_bubble；如需解释人物分歧，可同时调用 search_ai_bubble_views。
当用户询问泡沫分数历史、某个日期的读数、分数如何演化时，也调用 diagnose_current_ai_bubble，
并明确区分“历史模型复算”“六指标当前诊断”和“每日新闻连续更新”。
当用户要求把AI与铁路、电报、电力、互联网或电信泡沫比较时，也调用 diagnose_current_ai_bubble；
必须使用 technology_bubble_comparison 的锚点、置信度和统一结论，并说明标准化热度不是历史价格指数。

当用户询问今天/最近发生了什么、每日新闻、突发新闻如何影响股票债券黄金、新闻对增长通胀或经济周期的影响时，
必须调用 analyze_latest_market_news。回答必须注明新闻快照时间，引用主要新闻的 source、published_at 和 url；
优先综合 DeepSeek 研判与透明规则底稿，若两者冲突要明确指出；不得把标题规则评分描述成已证明的因果关系。

当用户要求结合自己的职业、收入、支出、家庭负担、投资期限或风险承受能力生成配置时，
必须先收集 create_personalized_allocation 所需信息，再调用该工具。不能仅凭年龄猜测风险偏好。
create_personalized_allocation 内部已经读取当前宏观环境和AI泡沫阶段，不需要再手工拼接两套互相冲突的权重。

历史回测的基准必须准确称为“规则基准”，不得称为真实机构组合：
- sixty_forty：60%股票、40%债券；
- equal_weight：股票、债券、黄金各1/3；
- stock：纯股票。

回答要求：
1. 所有数字来自工具，不自行编造；
2. 明确数据区间、基准和交易成本；
3. 同时报告收益、回撤和风险，不只挑选有利指标；
4. 明确股票不含股息、债券为久期代理、宏观数据不是历史 vintage；
5. 区分模型结果、规则基准和客观事实；
6. 提醒用户这是研究与教学模型，不构成投资建议。
7. 使用知识库回答时，必须标明人物、观点日期和 source_url；区分原始观点与自己的综合判断。
""",
    tools=[
        analyze_macro_portfolio,
        backtest_macro_portfolio,
        search_ai_bubble_views,
        diagnose_current_ai_bubble,
        analyze_latest_market_news,
        create_personalized_allocation,
    ],
)


def ask_agent(question):
    return Runner.run_sync(macro_agent, question).final_output


if __name__ == "__main__":
    question = input("请输入你的问题：")
    print("\nAgent回答：")
    print(ask_agent(question))
