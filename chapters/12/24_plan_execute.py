"""Experiment 24 (Chapter 12): Plan, execute, replan."""
import json

from agentic.live import OpenAIModel, schema

ROUTES = "Route A to D takes 3 hours. Route B to D takes 5 hours."
BLOCKED = {"A"}  # true in the world, unknown to the agent at the start
MAX_ACTIONS = 4
TOOLS = [schema("take_route", "Start driving on a route.", route="A or B"),
         schema("continue_to", "Drive on to the destination.",
                destination="the destination")]

EXAMPLE = ('[["take_route", {"route": "A"}], '
           '["continue_to", {"destination": "D"}]]')
planner = OpenAIModel(system="You plan trips. " + ROUTES + " Reply with a "
                      "JSON list of steps only, for example " + EXAMPLE + ".")


def act(tool, arguments, position):
    """The environment: returns the new position and an observation."""
    if tool == "take_route":
        route = arguments["route"]
        if route in BLOCKED:
            return position, f"Route {route} is blocked"
        return f"on {route}", f"on Route {route}"
    if position.startswith("on "):
        return "D", "arrived at D"
    return position, "cannot continue: not on a route"


def make_plan(known):
    request = "Goal: reach D." + (" Known: " + " ".join(known) if known
                                  else "")
    reply = planner.generate([{"role": "user", "content": request}])
    return json.loads(reply["answer"])


def drive(controller):
    position, known, log, plans_made = "start", [], [], 0
    driver = OpenAIModel(tools=TOOLS, system="You are driving. " + ROUTES)
    messages = [{"role": "user", "content": "Reach D."}]
    if controller != "reactive":
        plan, plans_made = make_plan(known), 1
    while position != "D" and len(log) < MAX_ACTIONS:
        if controller == "reactive":  # one model decision per step
            decision = driver.generate(messages)
            tool, arguments = decision["action"], decision["arguments"]
        else:
            tool, arguments = plan[0]
        position, observation = act(tool, arguments, position)
        log.append(f"{tool} {arguments} -> {observation}")
        if controller == "reactive":
            messages += [{"role": "assistant", "content": decision},
                         {"role": "tool", "content": observation}]
        if "blocked" in observation:
            known.append(observation + ".")
            if controller == "plan+replan":     # trigger: failed action
                plan, plans_made = make_plan(known), plans_made + 1
        elif controller != "reactive":
            plan = plan[1:]
    wasted = sum("blocked" in line for line in log)
    print(f"{controller}: success={position == 'D'} plans={plans_made} "
          f"actions={len(log)} wasted={wasted}")
    for line in log:
        print("   ", line)


for controller in ["reactive", "plan-first", "plan+replan"]:
    drive(controller)
