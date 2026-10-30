"""
Network reliability optimisation: deterministic node-disjoint paths (base case)
extended with probabilistic node failures and budgeted node hardening.

Base case adapted from Guéret, Prins & Sevaux (1999), Applications of
Optimisation with Xpress-MP (telecommunications network reliability).

Authors: Sudarshan Ellora, Mario  Celestina  Nanditha  H, Vinay  Kumar  Mansabdar, Mrunmayee  Tushar  Bhavsar
Date: 22/11/2025
Time: 16:04:20
"""
import itertools
import math
import networkx as nx

# ---------------------------
# Base-case edges
# ---------------------------
EDGES = [
    (1,2), (1,3), (1,11),
    (2,3), (2,8), (2,9),
    (3,4), (3,5), (3,9), (3,10), (3,11),
    (4,5), (4,6), (4,11),
    (5,9), (5,11),
    (6,7), (6,9), (6,10),
    (7,8), (7,10),
    (8,10),
    (9,10)
]

N = 11
SOURCE = 10
SINK = 11

# ---------------------------
# Node splitting
# ---------------------------
def build_node_split_digraph(edges, N, failed_nodes=set()):
    G = nx.DiGraph()

    for i in range(1, N+1):
        if i in failed_nodes:
            continue
        G.add_node(f"{i}_in")
        G.add_node(f"{i}_out")

        if i in (SOURCE, SINK):
            G.add_edge(f"{i}_in", f"{i}_out", capacity=1000)
        else:
            G.add_edge(f"{i}_in", f"{i}_out", capacity=1)

    for (u,v) in edges:
        if u in failed_nodes or v in failed_nodes:
            continue

        G.add_edge(f"{u}_out", f"{v}_in", capacity=1)
        G.add_edge(f"{v}_out", f"{u}_in", capacity=1)

    return G

# ---------------------------
# Max flow + flow graph
# ---------------------------
def compute_flow_and_residual(edges, N, failed_nodes=set()):
    G = build_node_split_digraph(edges, N, failed_nodes)
    s, t = f"{SOURCE}_out", f"{SINK}_in"

    if not (G.has_node(s) and G.has_node(t)):
        return 0, {}, G

    flow_value, flow_dict = nx.maximum_flow(G, s, t, capacity="capacity")

    H = nx.DiGraph()
    for u in flow_dict:
        for v, f in flow_dict[u].items():
            if f > 0:
                H.add_edge(u, v, flow=f)
    return int(flow_value), flow_dict, H

def extract_one_path(H):
    """
    Extract a single path from SOURCE to SINK from the flow graph H.
    """
    s = f"{SOURCE}_out"
    t = f"{SINK}_in"
    try:
        p = nx.shortest_path(H, s, t)
    except nx.NetworkXNoPath:
        return None

    orig = [SOURCE]
    for node in p:
        if node.endswith("_in"):
            num = int(node.split("_")[0])
            if num not in (SOURCE,) and (orig[-1] != num):
                orig.append(num)
    if orig[-1] != SINK:
        orig.append(SINK)

    return orig

def extract_node_paths_from_flow_graph(H, max_paths):
    """
    Extract multiple node-disjoint paths for deterministic base case.
    """
    paths = []
    H_copy = H.copy()
    s = f"{SOURCE}_out"
    t = f"{SINK}_in"

    for _ in range(max_paths):
        try:
            p = nx.shortest_path(H_copy, s, t)
        except nx.NetworkXNoPath:
            break

        # convert to original node list
        orig = [SOURCE]
        for node in p:
            if node.endswith("_in"):
                num = int(node.split("_")[0])
                if num != SOURCE and orig[-1] != num:
                    orig.append(num)
        if orig[-1] != SINK:
            orig.append(SINK)
        paths.append(orig)

        # remove used edges to avoid reuse
        for u, v in zip(p[:-1], p[1:]):
            if H_copy.has_edge(u, v):
                H_copy.remove_edge(u, v)

    return paths

# ---------------------------
# Deterministic base case
# ---------------------------
def base_case_paths(edges, N):
    flow_val, _, H = compute_flow_and_residual(edges, N)
    paths = extract_node_paths_from_flow_graph(H, flow_val)
    return flow_val, paths

# ---------------------------
# Probabilistic reliability
# ---------------------------
def default_node_failure_prob():
    p = [0.0] * (N+1)
    for i in range(1, N+1):
        p[i] = 0.10
    p[SOURCE] = p[SINK] = 0.0
    return p

def all_failure_subsets(nodes):
    nodes = list(nodes)
    for r in range(len(nodes)+1):
        for comb in itertools.combinations(nodes, r):
            yield set(comb)

def node_disjoint_paths_count(edges, N, failed_nodes):
    flow_val, _, _ = compute_flow_and_residual(edges, N, failed_nodes)
    return flow_val

def exact_expected_reliability(edges, N, node_failure_prob, collect=False):
    candidates = [i for i in range(1, N+1) if i not in (SOURCE, SINK)]
    total_prob_connect = 0.0
    total_expected_k = 0.0
    scenarios = []

    for failed in all_failure_subsets(candidates):
        prob = 1.0
        for i in candidates:
            prob *= node_failure_prob[i] if i in failed else (1-node_failure_prob[i])

        k = node_disjoint_paths_count(edges, N, failed)
        connected = (k >= 1)

        if k >= 1:
            total_prob_connect += prob

        total_expected_k += prob * k

        if collect:
            # surviving nodes
            surviving = sorted(set(range(1, N+1)) - failed)

            # example surviving path if connected
            example_path = None
            if connected:
                _, _, H_flow = compute_flow_and_residual(edges, N, failed)
                example_path = extract_one_path(H_flow)

            scenarios.append((failed, surviving, prob, k, connected, example_path))

    return total_prob_connect, total_expected_k, scenarios

# ---------------------------
# Hardening
# ---------------------------
def evaluate_harden_set_exact(edges, N, node_failure_prob, hardened_set):
    saved = {i: node_failure_prob[i] for i in hardened_set}
    for i in hardened_set:
        node_failure_prob[i] = 0.0

    try:
        prob, exp_k, _ = exact_expected_reliability(edges, N, node_failure_prob)
    finally:
        for i in saved:
            node_failure_prob[i] = saved[i]

    return prob, exp_k

def enumerate_best_harden(edges, N, node_failure_prob, B, max_enum=50000):
    candidates = [i for i in range(1,N+1) if i not in (SOURCE,SINK)]
    total = sum(math.comb(len(candidates), k) for k in range(B+1))
    if total > max_enum:
        raise ValueError("Enumeration too large")

    best_prob = -1
    best_set = set()

    for k in range(B+1):
        for comb in itertools.combinations(candidates, k):
            p, _ = evaluate_harden_set_exact(edges, N, node_failure_prob, comb)
            if p > best_prob:
                best_prob = p
                best_set = set(comb)

    return best_set, best_prob

# ---------------------------
# MAIN PROGRAM
# ---------------------------
def main():
    # BASE CASE
    print("BASE CASE (DETERMINISTIC)")
    base_flow, base_paths = base_case_paths(EDGES, N)
    print(f"Max node-disjoint paths: {base_flow}")
    for i, p in enumerate(base_paths, 1):
        print(f"Path {i}: " + " → ".join(map(str, p)))
    print()

    # EXTENSION
    node_failure_prob = default_node_failure_prob()
    prob, expk, _ = exact_expected_reliability(EDGES, N, node_failure_prob)

    B = 2
    best_set, best_prob = enumerate_best_harden(EDGES, N, node_failure_prob, B)

    print("EXTENSION (Probabilistic Reliability)")
    print(f"Connectivity probability: {prob:.6f}")
    print(f"Expected node-disjoint paths: {expk:.6f}")
    print(f"Best hardened nodes (B={B}): {sorted(best_set)}  → prob = {best_prob:.6f}")
    print()

    # SUMMARY
    print("SUMMARY")
    print(f"Deterministic max paths: {base_flow}")
    print(f"Probabilistic connectivity: {prob:.6f}")
    print(f"Expected disjoint paths: {expk:.6f}")
    print(f"Hardened set: {sorted(best_set)} (prob = {best_prob:.6f})")
    print()

    # ASK USER IF THEY WANT ALL SCENARIOS
    ans = input("Do you want to print all 512 failure scenarios? (yes/no): ").strip().lower()
    if ans not in ("yes", "y"):
        print("Skipping scenarios. Done.")
        return

    print("\n ALL FAILURE SCENARIOS")
    _, _, scenarios = exact_expected_reliability(EDGES, N, node_failure_prob, collect=True)

    for idx, (failed, surviving, prob_s, k, connected, example_path) in enumerate(scenarios, start=1):
        print(f"\nScenario {idx}:")
        print(f"  Failed nodes: {sorted(failed)}")
        print(f"  Surviving nodes: {surviving}")
        print(f"  k (node-disjoint paths): {k}")
        print(f"  Connected: {'YES' if connected else 'NO'}")
        if connected:
            print("  Example surviving path: " + " → ".join(map(str, example_path)))
        else:
            print("  Example surviving path: (none)")
        print(f"  Probability of scenario: {prob_s:.6f}")

    print("\nEnd of scenarios.")

if __name__ == "__main__":
    main()
