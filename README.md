# GreenOffsetX: Autonomous Cross-Source MRV & Dynamic Carbon Credit Issuance Vault

[![GenLayer Studionet](https://img.shields.io/badge/GenLayer-Studionet-purple.svg)](https://studio.genlayer.com)
[![GenVM Contract](https://img.shields.io/badge/GenVM-Python%20v0.2.16-blue.svg)](https://docs.genlayer.com)
[![Build Status](https://img.shields.io/badge/Tests-11%2F11%20Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**GreenOffsetX** is an autonomous, on-chain carbon credit verification and issuance primitive built natively on **GenLayer**. It solves the multi-billion-dollar bottleneck of centralized, opaque, and fraud-prone carbon auditing (Verra, Gold Standard) by executing **autonomous on-chain multi-source MRV (Measurement, Reporting, and Verification)**: cross-correlating in-situ ground IoT sensor telemetry with independent multi-spectral satellite remote sensing data on-chain.

---

## 🚀 Live Studionet Deployment

- **Network:** GenLayer Studionet (`studionet`)
- **Chain ID:** `61999` (`0xF1EF`)
- **RPC Endpoint:** `https://studio.genlayer.com/api`
- **Contract Address:** `0xD9388b6dB536475E0F0df5ca162186B4F0703917`
- **Deployment Transaction Hash:** `0xf7068fec5cfd2beaad9e5909916883c04fcb18252b60d2dff68b55c429e31cdf`
- **Live Interaction Tx Hash (`fund_buyer_pool`):** `0xd51a3f1f2df4bd5fe9aba99becc9e4d110dbf164b2c8816e5771f8efe11b453d`
- **Finality Status:** `Status: 5 (FINALIZED)` | `Result: 6 (SUCCESS)`
- **Deployer Address:** `0x17A59dD5Ba274C5e11a082a9f81D46704D9d1345`

---

## 🎯 The Core Problem & Why GenLayer is Strictly Necessary

### 1. The Real-World Bottleneck in Carbon Markets
- **Centralized Auditing Monopoly:** Traditional carbon accreditation takes 6 to 18 months, costs \$50,000+ in manual consultancy, and relies on static PDF self-reports.
- **Sensor Spoofing & Phantom Forests:** Bad actors tamper with ground soil sensors or submit fabricated reforestation claims while clear-cutting or wildfires are occurring. Single-source audit methods consistently fail to detect these contradictions.
- **Non-Permanence Risk:** Forest fires, logging, and pest outbreaks can reverse carbon storage overnight. Without a programmatic buffer reserve pool, buyers purchase "junk" credits with zero insurance against reversal.

### 2. Why GreenOffsetX CANNOT Exist on Ethereum / Solana / L2s
- **EVM Oracles Cannot Multi-Cross-Check Unstructured Data:** Solidity cannot scrape raw, dynamic IoT data streams alongside multi-spectral satellite observation indexes (e.g., Copernicus Sentinel-2 NDVI spectral bands) without trusting a single centralized intermediary oracle.
- **Deterministic Smart Contracts Cannot Synthesize Complex Evidence:** Traditional blockchains cannot determine whether an 8.5% flux tower biomass growth rate correlates truthfully with an NDVI satellite vegetation index of 0.84.
- **The GenLayer Primitive:**
  1. **Dual On-Chain Web Scrapes (`gl.nondet.web.render`):** GenLayer validators independently fetch both the in-situ ground sensor stream AND the third-party satellite registry.
  2. **Multi-Validator AI Jury (`gl.vm.run_nondet`):** Evaluates cross-source consistency, detects sensor spoofing / fraud, and grades verified net carbon sequestration ($\Delta \text{tCO}_2\text{e}$).
  3. **Autonomous Vault Clearing:** Splits proceeds between eco-proposer payout (85%) and a decentralized permanence risk buffer (15%), while automatically slashing fraud deposits.

---

## 🏛 Architecture & Mechanism Design

```
                     [Institutional Carbon Buyers / ESG Sponsors]
                                          |
                                          v  fund_buyer_pool(amount, price_per_ton)
             +------------------------------------------------------------------+
             |         GreenOffsetX Autonomous Issuance & Vault Contract        |
             |                   (0xD9388b6dB536475E0F0df5ca162186B4F0703917)    |
             +------------------------------------------------------------------+
                     ^                                         |
                     | submit_carbon_mrv(...)                  | 85% Net Carbon Payout
        [Eco-Project Proposer]                                 v
        (Stakes 500+ GEN Bond)                       [Eco-Project Proposer]
                                                               +
                                                 [Permanence Buffer Reserve (15%)]
                                                 (AFOLU Risk Buffer against reversal)
                                                               ^
                                                               | verify_carbon_mrv(id)
             +-------------------------------------------------+----------------+
             |                    GenLayer Multi-Source AI Jury                 |
             |                                                                  |
             |   Source 1: In-situ IoT Flux Tower & Soil Carbon Sensor Stream   |
             |   Source 2: Independent Sentinel-2 / Landsat Satellite Telemetry |
             |                                                                  |
             |   1. Cross-Source Consistency Index (0-100%)                     |
             |   2. Sensor Spoofing & Deforestation Contradiction Detection     |
             |   3. Net Sequestration Volume (verified_tonnes CO2e)             |
             |   4. Semantic Validator Equivalence (Verdict + Bounded Variance) |
             +-------------------------------------------------+----------------+
                                                               |
                     +-----------------------------------------+-----------------------------------------+
                     |                                                                                   |
                     v                                                                                   v
      [VERIFIED_ISSUANCE]                                                                 [FRAUD_DISCREPANCY]
  - Consistency Index >= 70%                                                          - Ground vs Satellite contradiction
  - 85% Disbursed to Proposer                                                         - Proposer Staked Bond is SLASHED
  - 15% Allocated to Permanence Buffer                                                - Slashed Bond transferred to Buffer
```

---

## ⚖️ Equivalence Principle & Consensus Verification

GreenOffsetX does not use fragile format-only comparisons or generic loose bounds. It enforces a strict multi-dimensional semantic consensus:

```python
def validator_fn(leader_res) -> bool:
    if not isinstance(leader_res, gl.vm.Return):
        return False
    leader = leader_res.calldata

    # Strict agreement on final verdict
    mine = leader_fn()
    if mine.get("verdict") != leader.get("verdict"):
        return False

    # If verified, enforce bounded variance on consistency score and tonnage
    if leader.get("verdict") == "VERIFIED_ISSUANCE":
        # Consistency score tolerance <= 15 points
        if abs(int(leader.get("consistency_score", 0)) - int(mine.get("consistency_score", 0))) > 15:
            return False

        # Tonnage variance tolerance <= 20% of target claim
        max_tonnes_variance = max(10, target_tonnes * 20 // 100)
        if abs(int(leader.get("verified_tonnes", 0)) - int(mine.get("verified_tonnes", 0))) > max_tonnes_variance:
            return False

    return True
```

---

## 🧪 Comprehensive Test Suite (11/11 Passing)

Run the full automated test suite locally:
```bash
pytest
```

Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Admin\Documents\genlayer\intel contract\GreenOffsetX
plugins: anyio-4.14.2, genlayer-test-0.29.2
collected 11 items

tests\test_green_offset_x.py ...........                                 [100%]

============================= 11 passed in 11.78s =============================
```

### Test Cases Summary:
1. `test_initial_state`: Verifies contract initialization, vault parameters, and initial stats.
2. `test_fund_buyer_pool`: Tests sponsor liquidity deposits into the carbon buyer pool and custom price-per-ton configuration.
3. `test_submit_carbon_mrv_success`: Tests project submission with security bond stake, target tonnes, and dual telemetry URLs.
4. `test_submit_carbon_mrv_validations`: Tests strict input validation (short name, invalid ecosystem, low stake bond, zero tonnes, private IP / SSRF blocking).
5. `test_verify_carbon_mrv_not_found`: Rejects non-existent project verification.
6. `test_verify_carbon_mrv_verified_issuance`: Full happy path: IoT ground flux + Sentinel-2 satellite cross-check $\rightarrow$ 94% consistency $\rightarrow$ 380 tonnes verified $\rightarrow$ 85% proposer payout + 15% permanence buffer reserve allocation.
7. `test_verify_carbon_mrv_fraud_discrepancy_slashed`: Fraud detection: Ground sensor reports +65% growth while satellite confirms wildfire burn scar $\rightarrow$ Verdict `FRAUD_DISCREPANCY` $\rightarrow$ Proposer's 1,000 GEN bond is **slashed** into the buffer reserve.
8. `test_verify_carbon_mrv_failed_evidence_refund`: Handles 404 / dead sensor streams gracefully with safe bond refund.
9. `test_cannot_reverify_verified_project`: Replay protection ensuring audited projects cannot be re-executed.
10. `test_cancel_project_by_proposer`: Allows proposer to withdraw a pending submission and recover the security bond.
11. `test_cancel_project_unauthorized`: Restricts cancellation to the legitimate proposer.

---

## 🛠 Project Directory Structure

```
GreenOffsetX/
├── contracts/
│   └── green_offset_x.py         # Production GenVM Intelligent Contract Primitive
├── scripts/
│   └── deploy_studionet.py       # Automated Studionet deployment script
├── tests/
│   ├── conftest.py               # GenLayer VM mock harness & loader patches
│   └── test_green_offset_x.py    # 11 unit & consensus integration tests
├── deployment.json               # Verified Studionet on-chain transaction receipt
├── gltest.config.yaml            # gltest runner configuration
├── requirements-dev.txt          # Python dependencies
├── submission.md                 # GenLayer Builders Portal submission details
└── README.md                     # Comprehensive technical documentation
```
