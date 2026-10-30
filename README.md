# Network Reliability Optimisation: Which Node Should You Protect?

A telecoms operator needs traffic to get from node 10 to node 11 even when routers fail. This project measures how resilient the network is, first under worst-case logic and then under realistic random failures. It then finds **which nodes to harden** on a limited budget.

![Network with node-disjoint paths](images/network_paths.png)

## The business question

If each router has a 10% chance of failing, how likely is the network to stay connected? And with budget to make **two** routers failure-proof, which ones should it be?

## Approach

**1. Base case: deterministic max-flow**
- Each node is split into an *in* and an *out* copy joined by a capacity-1 arc, so no node can carry more than one path.
- Max-flow on this graph equals the maximum number of **node-disjoint paths** (Menger's theorem).
- Result: **4 independent paths**, so the network survives any 3 router failures.

**2. Extension: probabilistic reliability**
- Each of the 9 intermediate nodes fails independently with p = 0.10. Source and sink never fail.
- **All 2⁹ = 512 failure scenarios** are enumerated exactly. For each, the code rebuilds the network, re-solves max-flow, and weights the result by the scenario's probability.
- Outputs: probability the network stays connected, and the expected number of surviving disjoint paths.

**3. Hardening optimisation**
- Every combination of up to B = 2 nodes is tested as "failure-proof" (46 combinations, each re-running all 512 scenarios), and the one that maximises connectivity is chosen.

## Results

| Metric | Value |
|---|---|
| Node-disjoint paths (deterministic) | **4** |
| Probability of staying connected (p = 0.10) | **99.916%** |
| Expected surviving disjoint paths | **3.26** of 4 |
| Best node(s) to harden, B = 2 | **Node 3 alone** |
| Connectivity after hardening node 3 | **100%** |

**Why node 3?** It's the only router directly linked to *both* the source and the sink, and it has the most links (7). Once it can't fail, the path 10 → 3 → 11 always exists, so connectivity is guaranteed. The second unit of budget adds nothing.

Hardening any one node, ranked:

| Node hardened | 3 | 9 | 4 | 6 | 5 | 1 | 2 | 8 | 7 |
|---|---|---|---|---|---|---|---|---|---|
| Connectivity | **100%** | 99.964% | 99.956% | 99.956% | 99.949% | 99.947% | 99.947% | 99.931% | 99.916% |

Node 7 is the least valuable to protect: losing it never reduces the number of disjoint paths.

**What this means for the business:** a deterministic model only says "survives 3 failures". The probabilistic version shows *where the remaining risk sits* and turns that into a specific, budgeted investment decision.

## How to run

```bash
pip install -r requirements.txt
python network_reliability.py     # base case, reliability, best hardening set; optionally prints all 512 scenarios
python make_diagram.py            # redraws images/network_paths.png
```

The full enumeration (512 scenarios × 46 hardening combinations) runs in seconds.

## Repo structure

```
├── network_reliability.py   # node-split max-flow, scenario enumeration, hardening search
├── make_diagram.py          # network visualisation with the disjoint paths highlighted
├── images/network_paths.png
└── requirements.txt
```

## Tech

Python · NetworkX (max-flow) · combinatorial enumeration · Matplotlib

## About

Built by **Mario Celestina Nanditha H** with Sudarshan Ellora, Vinay Kumar Mansabdar and Mrunmayee Tushar Bhavsar for MIS41160 Optimisation in Business, MSc Business Analytics, UCD Michael Smurfit Graduate Business School (2025). The base case is adapted from Guéret, Prins & Sevaux (1999), *Applications of Optimisation with Xpress-MP*.
