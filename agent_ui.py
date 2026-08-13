"""全站悬浮 Agent、对话状态与 PDF 导出。"""

from datetime import datetime

import streamlit as st

from pdf_reports import build_conversation_pdf


def _ask_agent(question, history):
    history.append({"role": "user", "content": question})
    try:
        from agent import ask_agent

        with st.spinner("Agent 正在读取宏观、新闻与历史信号……"):
            answer = ask_agent(question)
    except Exception as exc:
        answer = f"Agent 暂时无法完成回答：{exc}"
    history.append({"role": "assistant", "content": answer})


@st.dialog("Macro Intelligence Agent", width="large")
def _agent_dialog():
    history = st.session_state.setdefault("agent_messages", [])
    st.markdown(
        f"""
        <section class="fin-agent-panel-head">
          <div class="fin-agent-panel-mark" aria-hidden="true"><span>Agent</span></div>
          <div>
            <div class="fin-agent-kicker"><i></i> DEEPSEEK CONNECTED</div>
            <h2>把分散信号，变成一个判断</h2>
            <p>同时读取宏观周期、个人风险、历史回测、AI 泡沫与每日情报。</p>
          </div>
          <div class="fin-agent-count">{len(history)} 条记录</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.container(height=430, border=False):
        if history:
            for item in history:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])
        else:
            st.markdown(
                """
                <div class="fin-agent-empty">
                  <span>START A DECISION</span>
                  <strong>今天想先判断什么？</strong>
                  <p>你可以直接提问，也可以从下面四个常用问题开始。</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            prompt_options = (
                "结合当前环境，我的资产应该怎么配？",
                "AI 泡沫现在走到哪个阶段？",
                "用历史回测检验当前建议",
                "今天的新闻改变了哪些资产判断？",
            )
            for row in (prompt_options[:2], prompt_options[2:]):
                columns = st.columns(2)
                for column, prompt in zip(columns, row):
                    if column.button(prompt, key=f"agent_prompt_{prompt}", width="stretch"):
                        _ask_agent(prompt, history)
                        st.rerun()

    question = st.chat_input("例如：为什么当前要降低股票风险？")
    if question:
        _ask_agent(question, history)
        st.rerun()

    st.markdown(
        '<div class="fin-agent-export-note">PDF 会完整保留本次对话，并在报告结尾附上 Macro Portal 推荐与访问地址。</div>',
        unsafe_allow_html=True,
    )
    action1, action2, action3 = st.columns([1.7, 1, 1])
    if history:
        action1.download_button(
            "导出完整对话 PDF",
            data=build_conversation_pdf(history),
            file_name=f"macro-portal-agent-{datetime.now():%Y-%m-%d}.pdf",
            mime="application/pdf",
            width="stretch",
            type="primary",
        )
        if action2.button("清空对话", width="stretch"):
            st.session_state["agent_messages"] = []
            st.rerun()
    else:
        action1.button("对话后可导出 PDF", disabled=True, width="stretch")
    if action3.button("关闭", width="stretch"):
        st.session_state["agent_dialog_open"] = False
        st.rerun()


def render_agent_experience():
    if st.query_params.get("view") == "agent":
        st.session_state["agent_dialog_open"] = True
        del st.query_params["view"]
    if st.session_state.get("agent_dialog_open"):
        _agent_dialog()
