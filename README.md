📘 LightIoT Project Documentation (Extended Full Details)

This document is a comprehensive technical and conceptual log of the LightIoT Simulation Project, capturing all phases of design, development, simulation, and evaluation performed over several months. It reflects both the theoretical and practical progression of the research, providing every minute detail necessary for replication, evaluation, and academic defense.

⸻

🧠 Project Background & Motivation

The proliferation of Medical IoT (MIoT) devices has revolutionized healthcare monitoring and delivery. However, these systems are often resource-constrained and exposed to significant security threats (e.g., replay attacks, MITM attacks). Traditional security solutions are either too heavy or not scalable. This thesis was born from the urgent need for a lightweight and energy-efficient security protocol for MIoT environments.

The core idea emerged from the base paper titled:

“LightIoT: Lightweight and Secure Communication for Energy-Efficient IoT in Health Informatics”

Our project extends this protocol by simulating it in a realistic OMNeT++ environment and enhancing it with multiple additional layers of protection and evaluation.

**Note on scope:** This repository implements a lightweight, **parameterized** simulation of anti‑replay mechanisms (symbolic HMAC tag, timestamp freshness window, duplicate‑ID filtering). Real cryptographic primitives (e.g., AES/HMAC byte‑level computation) are **not** executed inside the simulator; their costs are modeled via parameters.

⸻

⚡ Quick Start

```bash
# 1) Build (from repo root)
rm -rf out Makefile && \
opp_makemake -f --deep -o LightIoTSimulation -O out && \
make -j"$(nproc)"

# 2) Run a single scenario (headless)
./out/clang-release/LightIoTSimulation -u Cmdenv -n .:ned -f run_record.ini -c Secure50_record

# (GUI) Qtenv
./out/clang-release/LightIoTSimulation -u Qtenv  -n .:ned -f run_record.ini -c Secure5_record

# 3) Run all + aggregate + plot
./run-all.sh

# 4) View results
column -s, -t < results/summary_all_record.csv
ls -1 results/chart_*.png
```

🧩 Prerequisites

- **OMNeT++ 6.1** installed and environment loaded:
  ```bash
  source /path/to/omnetpp-6.1/setenv
  ```
- **C++ toolchain**: clang/gcc + make
- **Python 3.10+** with:
  ```bash
  pip install pandas matplotlib
  ```
- **OS tested**: Ubuntu 22.04 LTS

🚧 Project Phases Breakdown

✅ Phase 1: Requirements, Planning, and Architectural Design
	•	Reviewed and analyzed the original LightIoT paper.
	•	Identified implementation feasibility within OMNeT++.
	•	Determined major security threats to be modeled (Replay Attack, MITM, etc.).
	•	Selected evaluation metrics: energy consumption, packet delay, drop rate, node scalability.
	•	Designed the modular software architecture using:
	•	SensorNode
	•	GatewayNode
	•	CloudServer
	•	FakeNode (Attacker)

✅ Phase 2: OMNeT++ Simulation Code Implementation
	•	Developed simulation logic in C++:
	•	Message structures (`LightIoTMessage_m.*` minimal C++ class; `.msg` generator not used here)
	•	Node behaviors (`SensorNode.cc`, `GatewayNode.cc`, `CloudServer.cc`, `FakeNode.cc`)
	•	Logging systems (OMNeT++ scalars/vectors + CSV aggregation)
	•	Implemented lightweight security checks at the Gateway:
	    – symbolic HMAC tag verification ("VALID"/"INVALID")
	    – timestamp freshness window (`hmacWindow`)
	    – duplicate ID filtering
	•	Parameterized energy model (Forward=5mJ, Verify=5mJ) and optional processing delay (`procDelay`)
	•	Created `run_record.ini` for reproducible scenarios (Secure / NoSec / Attack) at 5, 20, and 50 nodes

Three main scenarios simulated:
	1.	NoSecurity — Base model with no security checks
	2.	Secure — Lightweight anti‑replay checks (HMAC tag + freshness window + duplicate‑ID)
	3.	Attack — FakeNode launches Replay Attack (and optional MITM variant via invalid HMAC)

✅ Phase 3: Execution and Parallel Simulation
	•	Built and executed scenarios using Cmdenv and Qtenv.
	•	Implemented robust logging for every packet in each scenario.
	•	Simulated across varying number of nodes: 5, 20, 50.
	•	Ensured reproducibility with randomized seeds and timestamps.
	•	Exported results to CSV format using logging hooks.

✅ Phase 4: Evaluation and Analysis
	•	Wrote Python scripts (plot_energy.py, plot_delay.py, plot_droprate.py) for result analysis.
	•	Plotted comparisons for Secure vs. Attack vs. NoSecurity.
	•	Metrics visualized:
	•	Average energy consumption (Sensor/Gateway separately)
	•	Average packet delay
	•	Packet drop rate under attack
	•	Observed the tradeoff between security and energy.
	•	Confirmed LightIoT reduces attack impact with acceptable energy overhead.

⸻

🛡️ Security Methods Used
	•	Symbolic HMAC Tag Verification at Gateway ("VALID"/"INVALID")
	•	Timestamp Freshness Window (`hmacWindow`) to block stale replays
	•	Duplicate Message‑ID Filtering (per‑run set of seen IDs)
	•	Configurable energy accounting (Forward=5mJ, Verify=5mJ); real cryptographic computation is not performed inside the simulator (kept parametric)

⸻

🎯 Threat Model & Assumptions

- **Attacker capability**: can sniff and inject packets on the path Sensor→Gateway (FakeNode models this). No computational break of crypto is assumed (Dolev–Yao style).
- **Replay**: adversary re-sends previously observed packets with stale timestamps; in MITM variant it may tamper the tag to `INVALID`.
- **Clocking**: loose synchronization assumed; the Gateway uses a **freshness window** (`hmacWindow`) for tolerance.
- **Identity/IDs**: each Sensor uses a unique ID offset; Gateway tracks a per-run set of seen IDs (duplicate filter).
- **Network**: the base runs assume an ideal channel (no loss/jitter) to isolate the effect of security. Sensitivity to channel effects can be added in future work.
- **Energy model**: verification/forwarding costs are **parametric**; no byte-level crypto is executed in the simulator.

⸻

🔄 System Message Flow

To clarify the internal packet processing in the **Secure** scenario implemented here (lightweight anti‑replay), the following is a step‑by‑step walkthrough:

1. **SensorNode Initialization**
   - Each SensorNode derives a unique base offset from its index (e.g., 100000, 200000, …).
   - A periodic timer is scheduled for data generation.

2. **Message Creation**
   - On each trigger, a `LightIoTMessage` is created.
   - Fields are set as:
     - `id = baseOffset + localCounter++` (unique per sensor)
     - `hmac = "VALID"` (symbolic tag; no real crypto)
     - `timestamp = simTime()`
   - The message is sent to the Gateway.

3. **GatewayNode Verification**
   - Gateway receives the message and accounts energy budget.
   - If `securityEnabled=true`, the following checks are applied:
     - **HMAC tag check:** `hmac == "VALID"`
     - **Freshness:** `simTime() - timestamp ≤ hmacWindow`
     - **Duplicate filter:** `id` not seen before in this run
   - Failing any check → **drop** and log; otherwise message is **forwarded**.
   - Optional processing delay `procDelay` is applied (models verification time).
   - Energy costs: `costVerify` (when enabled) and `costForward`.

4. **CloudServer Handling**
   - Receives forwarded messages.
   - Computes end‑to‑end delay `simTime() - timestamp` and updates counters.
   - Used only for measurement/logging in this project.

5. **FakeNode (Attacker)**
   - Periodically injects packets every `replayInterval` (default 2.5s).
   - **Replay mode:** fixed `id`, `hmac="VALID"`, and a stale `timestamp` (e.g., `simTime()-2s`).
   - **MITM mode:** increments `id` but sets `hmac="INVALID"` (always dropped in Secure).

⸻

📊 Data Collected (Energy/Delay/Drop Rate)

Core scalars are recorded per run and aggregated into `results/summary_all_record.csv`:

| Config                  | Nodes | Mode             | Cloud_TotalReceived | GW_Received | GW_Forwarded | GW_Dropped | GW_Battery_mJ | Sensor_AvgBattery_mJ | Cloud_AvgDelay_s | Fake_AttacksSent |
|-------------------------|-------|------------------|---------------------|-------------|--------------|------------|---------------|----------------------|------------------|------------------|
| Secure50_record         | 50    | Secure           | 468                 | 468         | 468          | 0          | 320           | 4812.8               | 0.001            | 0                |
| NoSec50_record          | 50    | NoSec            | 468                 | 468         | 468          | 0          | 2660          | 4812.8               | 0.0              | 0                |
| Attack50_record         | 50    | Attack           | 468                 | 471         | 468          | 3          | 305           | 4812.8               | 0.001            | 3                |
| AttackOnNoSec50_record  | 50    | Attack‑NoSec     | 479                 | 479         | 479          | 0          | 2605          | 4812.8               | 0.0167           | 4                |
| Attack50_window3s_record| 50    | Attack‑Window3s  | 476                 | 479         | 476          | 3          | 225           | 4812.8               | 0.0052           | 4                |

See `results/*.png` for the figures generated from this CSV (delay, energy, drops, and sensitivity plots).

🧪 Experiment Matrix (Configs)

| Config Name                  | Nodes | Security | Attacker | Notes                                  |
|-----------------------------|-------|----------|----------|----------------------------------------|
| Secure5_record              | 5     | ON       | OFF      | Baseline secure                        |
| Secure20_record             | 20    | ON       | OFF      |                                        |
| Secure50_record             | 50    | ON       | OFF      |                                        |
| NoSec5_record               | 5     | OFF      | OFF      | Baseline no-security                   |
| NoSec20_record              | 20    | OFF      | OFF      |                                        |
| NoSec50_record              | 50    | OFF      | OFF      |                                        |
| Attack5_record              | 5     | ON       | Replay   | 3 injections / 10s                     |
| Attack20_record             | 20    | ON       | Replay   |                                        |
| Attack50_record             | 50    | ON       | Replay   |                                        |
| AttackOnNoSec50_record      | 50    | OFF      | Replay   | Attacker against NoSec                 |
| Attack50_window3s_record    | 50    | ON       | Replay   | Freshness window = 3s (sensitivity)    |

📌 **Key Findings at a Glance**
- **Delay (E2E)**: NoSec ≈ 0 ms; Secure ≈ **1 ms**; Attack-on-Secure ≈ **1–5 ms** depending on window.
- **Gateway Energy**: Secure consumes ≈ **2×** NoSec (due to verification cost); at 50 nodes → NoSec ≈ **2660 mJ**, Secure ≈ **320 mJ**.
- **Replay Robustness**: Secure drops replay injections (3/10s). In **NoSec**, replays **pass through** (Cloud↑, AvgDelay↑).
- **Freshness Window Sensitivity (3s)**: at most one stale replay may pass; duplicates are blocked by the ID filter.

⸻

📁 Final File Structure Summary

thesis/
├── src/                      # OMNeT++ simulation code (C++)
│   ├── SensorNode.cc
│   ├── GatewayNode.cc
│   ├── CloudServer.cc
│   └── FakeNode.cc
├── ned/                      # NED topology files
│   ├── LightIoTNetwork.ned
│   ├── SensorNode.ned
│   ├── GatewayNode.ned
│   └── CloudServer.ned / FakeNode.ned
├── run_record.ini            # Main reproducible experiment matrix (Secure/NoSec/Attack, 5/20/50)
├── results/
│   ├── *.sca / *.vec         # OMNeT++ scalar/vector outputs
│   ├── summary_all_record.csv
│   └── chart_*.png           # Figures (delay/energy/drops/sensitivity)
├── plots/                    # (optional) additional figures
├── run-all.sh                # One‑click script: run all + aggregate + plot
└── README.md

⸻

🧪 Experimental Configuration & Runtime Behavior

▶️ **Simulation Environment**:
- **Simulator**: OMNeT++ 6.1
- **Execution Mode**: `Cmdenv` and `Qtenv`
- **Platform**: Ubuntu 22.04 LTS (tested)
- **Python**: 3.10+ with `pandas`, `matplotlib` (for plotting)

▶️ **Scenarios & Node Counts**:
- Node counts: 5, 20, 50
- Scenarios:
  - `NoSecurity`: security disabled (no verify, no procDelay)
  - `Secure`: symbolic HMAC + freshness window + duplicate‑ID
  - `Attack`: Replay via FakeNode (and optional MITM with invalid HMAC)

▶️ **Key Parameters**:
- Simulation time: 10s, seed: 123 (reproducible)
- Sensor send interval: ~1s (jittered)
- Replay injection: every 2.5s (3–4 replays per 10s)
- Freshness window: 1s (Secure); sensitivity run at 3s
- Energy model: `costForward_mJ = 5`, `costVerify_mJ = 5`
- Optional processing delay at Gateway: `procDelay = 1ms` (Secure)

▶️ **Outputs**:
- Scalars/Vectors → `results/*.sca`, `results/*.vec`
- Aggregated CSV → `results/summary_all_record.csv`
- Figures → `results/chart_*.png`

🧬 Reproducibility: Multi‑Seed & Confidence Intervals (Optional)

For statistical robustness in reports, you may repeat each configuration with multiple seeds and compute 95% confidence intervals.

**Option A — INI-based repeats**
```ini
[Config Secure50_CI] extends Secure50_record
repeat = 5
seed-set = ${repetition}
```
Run:
```bash
./out/clang-release/LightIoTSimulation -u Cmdenv -n .:ned -f run_record.ini -c Secure50_CI
```
This generates runs `-0..-4`. Aggregate them to compute mean/CI.

**Option B — Shell loop**
```bash
for SEED in 1 2 3 4 5; do
  ./out/clang-release/LightIoTSimulation -u Cmdenv -n .:ned -f run_record.ini -c Secure50_record -r $SEED || true
done
```

**Compute Mean & 95% CI (example Python)**
```python
import glob, pandas as pd, numpy as np
def pick(sca, metric):
    for line in open(sca):
        parts=line.split()
        if len(parts)>=4 and parts[0]=='scalar' and parts[2]==metric:
            return float(parts[3])
scas=sorted(glob.glob('results/Secure50_CI-*.sca'))
vals=[pick(s,'Cloud_AvgEndToEndDelay_s') for s in scas]
m=np.mean(vals); se=np.std(vals,ddof=1)/np.sqrt(len(vals)); ci=1.96*se
print('mean=',m,' 95%CI=±',ci)
```

✅ Sanity Checks (Commands)
```bash
# Forwarded equals Cloud received?
SCA=results/Secure50_record-0.sca
awk '$1=="scalar"&&$3=="GW_Forwarded"{f=$4} $1=="scalar"&&$3=="Cloud_TotalReceived"{c=$4} END{print "GW_Forwarded=",f," Cloud_TotalReceived=",c," OK?",(f==c)}' "$SCA"

# Energy consistency (example for NoSec50: ~5000 - 5*468 = 2660)
awk '$1=="scalar"&&$3=="GW_BatteryRemaining_mJ"{print "GW_Battery=", $4}' results/NoSec50_record-0.sca
```

🧹 .gitignore (recommended)
```
out/
results/*.sca
results/*.vec
results/*.elog
results/*.vci
results/*.csv
results/chart_*.png
LightIoTSimulation
*.tar.gz
*.zip
.vscode/
.idea/
```

⸻

📄 License & How to Cite

**License**: Choose and add a `LICENSE` file (e.g., MIT or Apache‑2.0). Until then, this repository defaults to “All rights reserved”.

**Suggested citation (edit with your details):**
```bibtex
@misc{LightIoT-Sim-2025,
  title        = {LightIoT: Lightweight Anti-Replay Simulation Framework for Medical IoT},
  author       = {<Your Name>},
  year         = {2025},
  howpublished = {\url{https://github.com/Ehsntb/ThesisV2}},
  note         = {OMNeT++ 6.1 artifacts and reproducible scripts}
}
```

### SensorNode.cc
**Purpose**: Simulates a medical sensor device transmitting data.

**Key Points**:
- Periodically creates `LightIoTMessage` with unique `id = baseOffset + localCounter`.
- Sets `hmac = "VALID"` (symbolic tag; no actual encryption/signing inside the simulator).
- Sets `timestamp = simTime()` and sends to Gateway.

---

### GatewayNode.cc
**Purpose**: Verifies and forwards packets toward the Cloud.

**Key Points**:
- Optional checks when `securityEnabled=true`: HMAC tag equality, freshness within `hmacWindow`, and duplicate‑ID filtering.
- Drops on failed checks; otherwise forwards (optionally with `procDelay`).
- Accounts per‑message energy: `costVerify` (if enabled) + `costForward`.

---

### CloudServer.cc
**Purpose**: Collects verified packets and measures end‑to‑end delay.

**Key Points**:
- Computes delay as `simTime() - timestamp` for each received message.
- Accumulates counters used in scalars/CSV.

---

### FakeNode.cc
**Purpose**: Simulates replay or MITM‑style injections.

**Key Points**:
- Periodically injects packets with a stale `timestamp` (replay), keeping `id` fixed, `hmac="VALID"`.
- In MITM mode, uses `hmac="INVALID"` (ensures drop under Secure).

---

### LightIoTMessage_m.*
**Purpose**: Minimal OMNeT++ C++ message class used in this project.

**Fields**:
- `int id`
- `const char* hmac`
- `simtime_t timestamp`