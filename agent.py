"""
LangGraph agent: LLM + financial tools (+ optional quality control).
Run: python agent.py
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from prompts import qc_prompt, system_prompt
from tools import FINANCIAL_TOOLS


class AgentState(TypedDict):
    """Conversation state passed between graph nodes."""
    messages: Annotated[list, add_messages]


class Agent:
    """
    Financial agent built with LangGraph.
    Flow: user message -> LLM -> (tools loop) -> optional QC -> final answer
    """

    def __init__(
        self,
        model_name: str,
        tools: list,
        system: str = "",
        use_qc: bool = False,
    ):
        self.system = system
        # Bind tools so the LLM can request tool calls
        self.llm = ChatOllama(model=model_name, temperature=0).bind_tools(tools)

        graph = StateGraph(AgentState)

        graph.set_entry_point("BigBuck5")
        graph.add_node("BigBuck5", self.call_model)
        graph.add_node("tools", ToolNode(tools))
        graph.add_edge("tools", "BigBuck5")

        if use_qc:
            self.qc_llm = ChatOllama(model=model_name, temperature=0)
            graph.add_node("quality_control", self.evaluate_response)
            graph.add_conditional_edges(
                "BigBuck5",
                tools_condition,
                {"tools": "tools", "__end__": "quality_control"},
            )
            graph.add_conditional_edges(
                "quality_control",
                self.check_quality,
                {"APROVADO": END, "REJEITADO": "BigBuck5"},
            )
        else:
            graph.add_conditional_edges("BigBuck5", tools_condition)

        memory = MemorySaver()
        self.app = graph.compile(checkpointer=memory)

    def call_model(self, state: AgentState):
        """Call the LLM; inject system prompt once at the start of the thread."""
        messages = state["messages"]

        if self.system and not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system)] + messages

        response = self.llm.invoke(messages)
        return {"messages": [response]}

    def evaluate_response(self, state: AgentState):
        """QC node: second LLM pass checks the last assistant answer."""
        messages = state["messages"]
        ultima_resposta = messages[-1].content

        avaliacao = self.qc_llm.invoke(
            [
                HumanMessage(
                    content=f"{qc_prompt}\nAnswer to review:\n{ultima_resposta}"
                )
            ]
        )
        return {"messages": [AIMessage(content=avaliacao.content)]}

    def check_quality(self, state: AgentState):
        """Route to END if approved, else send back to the main model."""
        avaliacao = state["messages"][-1].content
        if "APROVADO" in avaliacao.upper():
            return "APROVADO"
        return "REJEITADO"


def create_agent(
    model_name: str = "gemma4:e2b",
    use_qc: bool = False,
) -> Agent:
    """
    Factory used by agent.py CLI and by the Streamlit frontend (Phase D).
    Keeps model name and tool list in one place.
    """
    return Agent(
        model_name=model_name,
        tools=FINANCIAL_TOOLS,
        system=system_prompt,
        use_qc=use_qc,
    )


def run_chat_loop(agent: Agent, thread_id: str = "conversa_1") -> None:
    """Interactive terminal chat for quick testing."""
    config = {"configurable": {"thread_id": thread_id}}

    print("BigBuck5 Financial Agent is online!")
    print("-" * 80)
    print("Ask about stocks, signals, or comparisons (e.g. signal for AAPL).")
    print("Type 'exit' to quit.")

    while True:
        pergunta = input("\nYou: ").strip()
        if pergunta.lower() in ("exit", "quit", "sair"):
            print("BigBuck5: Goodbye.")
            break

        novo_estado = {"messages": [HumanMessage(content=pergunta)]}
        resposta_final = ""

        try:
            for event in agent.app.stream(novo_estado, config=config):
                for key, value in event.items():
                    if key == "tools":
                        print("  [tools] fetching market data...")
                    elif key == "BigBuck5":
                        resposta_final = value["messages"][-1].content
                    elif key == "quality_control":
                        print("  [qc] reviewing answer...")
        except Exception as e:
            print(f"BigBuck5: Error — {e}")
            continue

        if resposta_final:
            print(f"\nBigBuck5: {resposta_final}")
        else:
            print("\nBigBuck5: No answer generated. Try again.")


if __name__ == "__main__":
    BigBuck5 = create_agent(model_name="gemma4:e2b", use_qc=False)
    run_chat_loop(BigBuck5)
