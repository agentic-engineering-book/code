"""Experiment 24: Plan, execute, replan as a LangGraph cycle. See README."""
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from framework_examples.support import chat

ROUTES = "Route A to D takes 3 hours. Route B to D takes 5 hours."
BLOCKED = {"A"}  # true in the world, unknown to the agent at the start
MAX_ACTIONS = 4
EXAMPLE = ('[["take_route", {"route": "A"}], '
           '["continue_to", {"destination": "D"}]]')


def act(name, arguments, position):
    """The environment: returns the new position and an observation."""
    if name == "take_route":
        route = arguments["route"]
        if route in BLOCKED:
            return position, f"Route {route} is blocked"
        return f"on {route}", f"on Route {route}"
    if position.startswith("on "):
        return "D", "arrived at D"
    return position, "cannot continue: not on a route"


def reactive():
    """One model decision per step, as in the ReAct loop of Experiment 22."""
    world = {"position": "start"}

    def step(name, arguments):
        world["position"], observation = act(name, arguments,
                                             world["position"])
        return observation

    @tool
    def take_route(route: str) -> str:
        """Start driving on a route (A or B)."""
        return step("take_route", {"route": route})

    @tool
    def continue_to(destination: str) -> str:
        """Drive on to the destination."""
        return step("continue_to", {"destination": destination})

    tools = [take_route, continue_to]
    model = chat().bind_tools(tools, parallel_tool_calls=False)
    builder = StateGraph(MessagesState)
    builder.add_node("model", lambda s: {"messages": [model.invoke(
        [("system", "You are driving. " + ROUTES)] + s["messages"])]})
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_conditional_edges("tools", lambda s: END if sum(
        isinstance(m, ToolMessage) for m in s["messages"]) >= MAX_ACTIONS
        else "model", ["model", END])
    result = builder.compile().invoke({"messages": [("human", "Reach D.")]})
    log = []
    for message in result["messages"]:
        if isinstance(message, AIMessage) and message.tool_calls:
            call = message.tool_calls[0]
            log.append(f"{call['name']} {call['args']}")
        elif isinstance(message, ToolMessage):
            log[-1] += " -> " + message.content
    return {"position": world["position"], "plans": 0, "log": log}


class State(TypedDict, total=False):
    plan: list
    position: str
    known: list
    plans: int
    log: Annotated[list, operator.add]


def planned(replan):
    planner = chat() | JsonOutputParser()

    def plan(state):
        known = state.get("known", [])
        request = "Goal: reach D." + (" Known: " + " ".join(known)
                                      if known else "")
        steps = planner.invoke([
            ("system", "You plan trips. " + ROUTES + " Reply with a JSON "
             "list of steps only, for example " + EXAMPLE + "."),
            ("human", request)])
        return {"plan": steps, "plans": state.get("plans", 0) + 1}

    def execute(state):
        (name, arguments), rest = state["plan"][0], state["plan"][1:]
        position, observation = act(name, arguments, state["position"])
        update = {"position": position,
                  "log": [f"{name} {arguments} -> {observation}"]}
        if "blocked" in observation:  # the plan's assumption failed
            update["known"] = state.get("known", []) + [observation + "."]
        else:
            update["plan"] = rest
        return update

    def after_execute(state):
        if state["position"] == "D" or len(state["log"]) >= MAX_ACTIONS:
            return END
        if replan and "blocked" in state["log"][-1]:
            return "plan"  # trigger: a failed action
        return "execute" if state["plan"] else END

    builder = StateGraph(State)
    builder.add_node("plan", plan)
    builder.add_node("execute", execute)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "execute")
    builder.add_conditional_edges("execute", after_execute,
                                  ["plan", "execute", END])
    return builder.compile().invoke({"position": "start", "log": []},
                                    {"recursion_limit": 20})


def run():
    lines = []
    for name, drive in [("reactive", reactive),
                        ("plan-first", lambda: planned(False)),
                        ("plan+replan", lambda: planned(True))]:
        final = drive()
        wasted = sum("blocked" in line for line in final["log"])
        lines.append(f"{name}: success={final['position'] == 'D'} "
                     f"plans={final['plans']} actions={len(final['log'])} "
                     f"wasted={wasted}")
        lines += ["    " + line for line in final["log"]]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
