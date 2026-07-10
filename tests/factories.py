"""
测试数据工厂 — 生成各种状态的 AgentState
"""

from app.graph.state import AgentState


def make_initial_state(topic_direction: str = "AI技术") -> AgentState:
    """创建初始状态"""
    return {
        "topic_direction": topic_direction,
        "generated_topics": [],
        "selected_topic": "",
        "article_content": "",
        "review_feedback": "",
        "review_status": "pending",
        "revision_count": 0,
        "visual_points": [],
        "image_urls": [],
        "status": "initialized",
        "error": "",
        "node_metrics": [],
    }


def make_state_with_topics() -> AgentState:
    """创建已生成选题的状态"""
    state = make_initial_state()
    state["generated_topics"] = ["LangGraph 入门指南", "AI Agent 架构设计", "RAG 实战"]
    state["status"] = "topics_generated"
    return state


def make_state_with_article() -> AgentState:
    """创建已生成文章的状态"""
    state = make_state_with_topics()
    state["selected_topic"] = "LangGraph 入门指南"
    state["article_content"] = "# LangGraph 入门指南\n\n这是一篇关于 LangGraph 的技术文章。"
    state["status"] = "draft_completed"
    return state


def make_state_with_review_rejected() -> AgentState:
    """创建被审稿驳回的状态"""
    state = make_state_with_article()
    state["review_feedback"] = "请增加更多技术细节和代码示例"
    state["review_status"] = "rejected"
    return state
