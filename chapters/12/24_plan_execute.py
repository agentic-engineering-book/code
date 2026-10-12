"""Experiment 24 (Chapter 12): Plan, execute, replan."""
ROUTE_LENGTH = {"A": 3, "B": 5}
BLOCKED = {"A"}      # true in the world, unknown to the agent at the start
MAX_ACTIONS = 4


def act(action, position):
    """The environment: returns the new position and an observation."""
    kind, target = action
    if kind == "take":
        if target in BLOCKED:
            return position, f"Route {target} is blocked"
        return f"on {target}", f"on Route {target}"
    if position.startswith("on "):
        return "D", "arrived at D"
    return position, "cannot continue: not on a route"


def next_action(position, known_blocked):
    """A one-step decision made from the current state only."""
    if position == "start":
        open_routes = [r for r in ROUTE_LENGTH if r not in known_blocked]
        return ("take", min(open_routes, key=ROUTE_LENGTH.get))
    return ("continue", "D")


def make_plan(known_blocked):
    """A whole path from the start, built from what is currently known."""
    return [next_action("start", known_blocked), ("continue", "D")]


def drive(controller):
    position, known_blocked, log = "start", set(), []
    plan, plans_made = [], 0
    if controller != "reactive":
        plan, plans_made = make_plan(known_blocked), 1
    while position != "D" and len(log) < MAX_ACTIONS:
        if controller == "reactive":
            action = next_action(position, known_blocked)
        else:
            action = plan[0]
        position, observation = act(action, position)
        log.append(f"{action[0]} {action[1]} -> {observation}")
        if "blocked" in observation:
            known_blocked.add(action[1])
            if controller == "plan+replan":     # trigger: failed action
                plan, plans_made = make_plan(known_blocked), plans_made + 1
        elif controller != "reactive":
            plan = plan[1:]
    wasted = sum("blocked" in line for line in log)
    print(f"{controller}: success={position == 'D'} plans={plans_made} "
          f"actions={len(log)} wasted={wasted}")
    for line in log:
        print("   ", line)


for controller in ["reactive", "plan-first", "plan+replan"]:
    drive(controller)
