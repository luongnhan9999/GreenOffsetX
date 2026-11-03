# GreenOffsetX: Autonomous Cross-Source MRV & Dynamic Carbon Credit Issuance Vault

## 1. Project Title
**GreenOffsetX**: Autonomous Cross-Source MRV & Dynamic Carbon Credit Issuance Vault

## 2. One-line Pitch
> *"GreenOffsetX is an autonomous carbon MRV and dynamic credit issuance vault on GenLayer that cross-correlates in-situ ground IoT telemetry with independent multi-spectral satellite remote sensing on-chain, eliminating centralized audit monopolies while slashing sensor fraud and automating 15% permanence buffer reserves."*

## 3. Live Studionet Deployment
- **Network:** GenLayer Studionet (`studionet`)
- **Chain ID:** `61999` (`0xF1EF`)
- **RPC URL:** `https://studio.genlayer.com/api`
- **Contract Address:** `0xD9388b6dB536475E0F0df5ca162186B4F0703917`
- **Deployment Transaction Hash:** `0xf7068fec5cfd2beaad9e5909916883c04fcb18252b60d2dff68b55c429e31cdf`
- **Receipt Status:** `Status: 5 (FINALIZED)` | `Result: 6 (SUCCESS)`
- **Deployer Address:** `0x17A59dD5Ba274C5e11a082a9f81D46704D9d1345`

## 4. Addressing the Previous Rejection & Why This is a Distinct Primitive
- **Previous Rejection Reason:** *"This submission materially repeats another contract mechanism in the current review cohort and is therefore not eligible as a distinct Intelligent Contract contribution."*
- **What Was Changed & Overhauled:**
  1. **From Single-URL Wrapper to Multi-Source Cross-Check MRV:** Rather than scraping 1 website and asking an LLM for a generic 0–100 score, the contract scrapes **two independent real-world sources on-chain**: in-situ ground IoT flux/biomass sensors (`ground_sensor_url`) and multi-spectral satellite remote sensing data (`satellite_report_url`).
  2. **Fraud Detection & Economic Bond Slashing:** Proposers must stake a verification bond (500+ GEN). If the AI jury detects a contradiction (e.g. ground sensor claims +65% growth while satellite confirms wildfire burn scars and canopy loss), the verdict is `FRAUD_DISCREPANCY` and the proposer's bond is **slashed** into the permanence reserve.
  3. **Real Carbon Vault Liquidity & Tranche Payouts:** Institutional carbon buyers deposit GEN into a `BuyerPool`. When a project is verified, the contract dynamically prices net tonnes ($\text{tCO}_2\text{e}$), disburses **85%** to the eco-proposer, and locks **15%** into an on-chain **Permanence Buffer Reserve** (industry-standard AFOLU risk buffer protecting against future reversals).
  4. **Multi-Dimensional Semantic Equivalence:** The `validator_fn` enforces strict agreement on the verdict, bounded variance on cross-source consistency ($\le 15$), and bounded variance on net verified tonnage ($\le 20\%$).

## 5. Comprehensive Test Suite
- **11/11 tests passing (`pytest`)**:
  - `test_initial_state`: Initial state, storage, and default parameters.
  - `test_fund_buyer_pool`: Sponsor liquidity deposits and custom carbon pricing.
  - `test_submit_carbon_mrv_success`: Staked bond deposit and dual-source registration.
  - `test_submit_carbon_mrv_validations`: Input boundaries, invalid ecosystems, stake thresholds, zero tonnes, and SSRF blocking.
  - `test_verify_carbon_mrv_not_found`: Non-existent project guard.
  - `test_verify_carbon_mrv_verified_issuance`: Dual-source cross-check happy path with 85/15 payout and buffer split.
  - `test_verify_carbon_mrv_fraud_discrepancy_slashed`: Sensor spoofing detection and bond slashing.
  - `test_verify_carbon_mrv_failed_evidence_refund`: Safe bond recovery on 404/dead streams.
  - `test_cannot_reverify_verified_project`: Replay protection.
  - `test_cancel_project_by_proposer`: Proposer cancellation and bond recovery.
  - `test_cancel_project_unauthorized`: Unauthorized cancellation prevention.

## 6. GitHub Repository
- **URL:** `https://github.com/luongnhan9999/GreenOffsetX`
