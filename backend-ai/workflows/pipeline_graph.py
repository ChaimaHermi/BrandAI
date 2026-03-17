from langgraph.graph import StateGraph

from agents.idea_clarifier import IdeaClarifierAgent
from agents.base_agent import PipelineState


clarifier = IdeaClarifierAgent()


async def run_clarifier(state: PipelineState):

    result = await clarifier.run(state)

    state.clarified_idea = result

    return state


def build_graph():

    graph = StateGraph(PipelineState)

    graph.add_node("idea_clarifier", run_clarifier)

    graph.set_entry_point("idea_clarifier")

    graph.set_finish_point("idea_clarifier")

    return graph.compile()