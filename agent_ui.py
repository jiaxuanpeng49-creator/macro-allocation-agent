"""全站悬浮 Agent、对话状态与 PDF 导出。"""

import streamlit as st

from pdf_reports import build_conversation_pdf


@st.dialog("Agent", width="large")
def _agent_dialog():
    history = st.session_state.setdefault("agent_messages", [])
    st.caption("DeepSeek × 宏观周期 × 个人风险 × 历史验证 × 每日情报")
    if history:
        for item in history:
            with st.chat_message(item["role"]):
                st.write(item["content"])
    else:
        st.info("可以询问当前配置、历史回测、每日新闻或 AI 泡沫阶段。")

    question = st.chat_input("例如：为什么当前要降低股票风险？")
    if question:
        history.append({"role": "user", "content": question})
        try:
            from agent import ask_agent
            with st.spinner("Agent 正在综合分析……"):
                answer = ask_agent(question)
        except Exception as exc:
            answer = f"Agent 暂时无法完成回答：{exc}"
        history.append({"role": "assistant", "content": answer})
        st.rerun()

    action1, action2 = st.columns(2)
    if history:
        action1.download_button(
            "导出本次对话 PDF",
            data=build_conversation_pdf(history),
            file_name="macro-portal-agent-conversation.pdf",
            mime="application/pdf",
            width="stretch",
        )
    if action2.button("关闭", width="stretch"):
        st.session_state["agent_dialog_open"] = False
        st.rerun()


def render_agent_experience():
    if st.query_params.get("view") == "agent":
        st.session_state["agent_dialog_open"] = True
        del st.query_params["view"]
    if st.session_state.get("agent_dialog_open"):
        _agent_dialog()
