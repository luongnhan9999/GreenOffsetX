# GreenOffsetX: Dynamic Carbon Credit & Environmental Impact Verifier Protocol

[![GenLayer Studionet](https://img.shields.io/badge/GenLayer-Studionet-purple.svg)](https://studio.genlayer.com)
[![GenVM Contract](https://img.shields.io/badge/GenVM-Python%20v0.2.16-blue.svg)](https://docs.genlayer.com)
[![Build Status](https://img.shields.io/badge/Tests-10%2F10%20Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

GreenOffsetX is a decentralized, autonomous carbon credit verification and environmental additionality evaluation protocol built natively on **GenLayer**. It completely replaces slow, expensive, and opaque manual carbon auditing with GenLayer's decentralized AI validator jury and real-time on-chain web scraping of sensor telemetry and multi-spectral satellite imagery reports.

---

## 🚀 Live Studionet Deployment

- **Network:** GenLayer Studionet (`studionet`)
- **Chain ID:** `61999` (`0xF1EF`)
- **RPC Endpoint:** `https://studio.genlayer.com/api`
- **Contract Address:** `0xC92244190819e09cC06602d4D8e0CA3E5e31baE4`
- **Deployment Transaction Hash:** `0xe6e04072b30af6ccab48497174d0361e35302e15b529db1bcf618dcfaed6aa04`
- **Finality Status:** `Status: 5 (FINALIZED)` | `Result: 6 (SUCCESS)`
- **Deployer Address:** `0xbB9014623E8Ffc5Db8694D46c982f3aDC6AE597A`

---

## 🎯 The Core Problem & GenLayer Fit

### The Problem
1. **Manual & Expensive Carbon Auditing:** Traditional carbon credit certification (e.g., Verra, Gold Standard) requires manual site visits and third-party desk audits taking 6–18 months and costing tens of thousands of dollars.
2. **Greenwashing & Fraud:** Static paper reports fail to prevent double counting or phantom reforestation projects where trees were never planted or died prematurely.
3. **Delayed Liquidity for Eco-Stewards:** Legitimate indigenous communities and reforestation projects must wait years before receiving monetization for verified carbon drawdown.

### Why GreenOffsetX CANNOT Exist on Traditional Blockchains
- **Solidity / EVM Limitations:** Deterministic smart contracts cannot access the web or fetch real-time environmental satellite telemetry (NDVI spectral index, drone LiDAR biomass scans) without centralized oracle intermediaries. Furthermore, EVM cannot parse unstructured ecological audit documentation or evaluate subjective additionality.
- **The GenLayer Solution:**
  - **On-chain Web Scraping (`gl.nondet.web.render`):** GenLayer validators directly fetch multi-spectral satellite audit data and sensor reports from the web on-chain.
  - **Decentralized LLM Jury Consensus (`gl.vm.run_nondet`):** A multi-validator AI jury independently evaluates carbon additionality, grades the environmental impact score (0–100), and reaches consensus on the verdict (`VERIFIED_OFFSET`, `INSUFFICIENT_IMPACT`, or `FAILED_EVIDENCE`).
  - **Autonomous Financial Settlement:** If verified, credits/bounties are disbursed immediately. If rejected, funds are directed according to protocol governance rules without human tampering.

---

## 🏛 Architecture & Consensus Mechanism

```
+-----------------------------------------------------------------------------------+
|                        Green Project Proposer / Eco-Steward                       |
+-----------------------------------------------------------------------------------+
                                         |
                                         | submit_carbon_project(name, desc, audit_url)
                                         v
+-----------------------------------------------------------------------------------+
|                       GreenOffsetX Intelligent Contract                           |
|             (0xC92244190819e09cC06602d4D8e0CA3E5e31baE4)                         |
+-----------------------------------------------------------------------------------+
                                         |
                                         | verify_carbon_impact(project_id)
                                         v
+-----------------------------------------------------------------------------------+
|                         GenLayer Decentralized AI Jury                            |
|                                                                                   |
|  [Leader Node]                                                                    |
|    - gl.nondet.web.render(audit_url) -> Scrapes satellite / sensor audit report    |
|    - gl.nondet.exec_prompt(...) -> Evaluates impact score (0-100) & verdict       |
|                                                                                   |
|  [Validator Nodes]                                                                |
|    - Independently render audit URL & run environmental verification              |
|    - Semantic Validation: Ensures verdict MATCHES exactly                         |
|    - Numerical Tolerance: Asserts impact_score delta <= 20 points                 |
|    - Allows natural language variation in audit summary                           |
+-----------------------------------------------------------------------------------+
                                         |
                   +---------------------+---------------------+
                   |                                           |
                   v                                           v
      [Status: VERIFIED]                              [Status: REJECTED]
  - Verdict: VERIFIED_OFFSET                      - Verdict: INSUFFICIENT_IMPACT
  - Instant Payout / Carbon Issuance              - Deposit forfeited to Protocol
  - Impact Score >= 70                            - Impact Score < 70
```

### Equivalence Principle Implementation
GreenOffsetX employs `gl.vm.run_nondet` with semantic validator consensus:
```python
def validator_fn(leader_res) -> bool:
    if not isinstance(leader_res, gl.vm.Return):
        return False
    leader = leader_res.calldata

    # Strict semantic check on carbon verdict
    mine = leader_fn()
    if mine.get("verdict") != leader.get("verdict"):
        return False

    # Score tolerance bound (<= 20 points difference allowed across LLM runs)
    if leader.get("verdict") != "FAILED_EVIDENCE":
        if abs(int(leader.get("impact_score", 0)) - int(mine.get("impact_score", 0))) > 20:
            return False

    return True
```

---

## 🧪 Comprehensive Test Suite (10/10 Passing)

GreenOffsetX features a complete test suite covering initial state, submissions, edge-case validations, and consensus verdicts:

```bash
pytest
```

Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Admin\Documents\genlayer\intel contract\GreenOffsetX
plugins: anyio-4.14.2, genlayer-test-0.29.2
collected 10 items

tests\test_green_offset_x.py ..........                                  [100%]

============================= 10 passed in 11.72s =============================
```

### Test Coverage Highlights:
1. `test_initial_state`: Confirms owner resolution and initial statistics counters.
2. `test_submit_carbon_project_success`: Validates project submission, deposit escrow, and storage state.
3. `test_submit_carbon_project_validations`: Tests edge cases: short name, short description, invalid URL scheme, and SSRF/private IP blocking.
4. `test_verify_carbon_project_not_found`: Prevents non-existent project verification.
5. `test_verify_carbon_impact_verified_success`: Validates positive carbon additionality (`VERIFIED_OFFSET`), impact score >= 70, and automated payout.
6. `test_verify_carbon_impact_insufficient_impact_rejected`: Evaluates low-impact projects (`INSUFFICIENT_IMPACT`), impact score < 70, and deposit handling.
7. `test_verify_carbon_impact_failed_evidence_refund`: Tests inaccessible/404 URL scenarios with safe deposit refunds.
8. `test_cannot_reverify_verified_project`: Prevents double verification or replay calls.
9. `test_cancel_project_by_proposer`: Enables proposer to cancel pending projects and recover escrow deposit.
10. `test_cancel_project_unauthorized`: Blocks non-proposers from cancelling carbon projects.

---

## 🛠 Project Structure

```
GreenOffsetX/
├── contracts/
│   └── green_offset_x.py         # Intelligent Contract on GenVM
├── scripts/
│   └── deploy_studionet.py       # Automated Studionet deployment script
├── tests/
│   ├── conftest.py               # gltest runner harness & mock injectors
│   └── test_green_offset_x.py    # 10 unit & consensus integration tests
├── deployment.json               # On-chain Studionet deployment record & receipt
├── gltest.config.yaml            # gltest runner configuration
├── requirements-dev.txt          # Python development dependencies
├── submission.md                 # GenLayer Builders Portal submission details
└── README.md                     # Technical documentation & architecture
```

---

## 📦 How to Deploy & Verify

### 1. Install Dependencies
```bash
pip install -r requirements-dev.txt
```

### 2. Run Tests Locally
```bash
pytest
```

### 3. Deploy to GenLayer Studionet
```bash
python scripts/deploy_studionet.py
```
