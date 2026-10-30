"""Draws the network with the four node-disjoint paths highlighted -> images/network_paths.png"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from network_reliability import EDGES, N, SOURCE, SINK, base_case_paths

G = nx.Graph(EDGES)
_, paths = base_case_paths(EDGES, N)
pos = nx.kamada_kawai_layout(G)
colours = ["#2a7de1", "#e8743b", "#19a979", "#945ecf"]

fig, ax = plt.subplots(figsize=(9, 7))
nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#c8c8c8", width=1.5)
for path, c in zip(paths, colours):
    nx.draw_networkx_edges(G, pos, edgelist=list(zip(path[:-1], path[1:])),
                           ax=ax, edge_color=c, width=4,
                           label=" → ".join(map(str, path)))
node_colours = ["#222" if n in (SOURCE, SINK) else ("#d62728" if n == 3 else "#f2f2f2") for n in G]
font_colours = {n: "white" if n in (SOURCE, SINK, 3) else "black" for n in G}
nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colours, edgecolors="#444", node_size=750)
for n, (x, y) in pos.items():
    ax.text(x, y, str(n), ha="center", va="center", fontsize=12, weight="bold", color=font_colours[n])
ax.set_title(f"4 node-disjoint paths from source {SOURCE} to sink {SINK}  (node 3 in red: the critical hub)", fontsize=12)
ax.legend(loc="lower left", fontsize=10, frameon=False)
ax.axis("off")
plt.tight_layout()
plt.savefig("images/network_paths.png", dpi=150)
print("saved images/network_paths.png")
