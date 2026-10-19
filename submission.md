# GreenOffsetX — GenLayer Builders Submission Brief

## 1. Project Title
**GreenOffsetX**: Dynamic Carbon Credit & Environmental Impact Verifier Protocol

## 2. One-line Pitch (Why this project DIES without GenLayer)
> *"GreenOffsetX cannot exist on legacy blockchains like Ethereum or Solana because verifying carbon sequestration requires on-chain web scraping of unstructured multi-spectral satellite imagery and sensor reports coupled with decentralized AI jury consensus to grade carbon additionality without centralized oracles."*

## 3. Live Studionet Deployment
- **Network:** GenLayer Studionet (`studionet`)
- **Chain ID:** `61999` (`0xF1EF`)
- **RPC URL:** `https://studio.genlayer.com/api`
- **Contract Address:** `0x5F922FacAc4Fd4d1a36FEcBf4286a9E1F0383F29`
- **Deployment Transaction Hash:** `0xe6e04072b30af6ccab48497174d0361e35302e15b529db1bcf618dcfaed6aa04`
- **Receipt Status:** `Status: 5 (FINALIZED)` | `Result: 6 (SUCCESS)`

## 4. Problem & Solution
- **Problem:** Carbon credit verification currently relies on centralized certifiers taking 6–18 months and tens of thousands in manual audit fees, leading to greenwashing, phantom forestry projects, and delayed liquidity for legitimate reforestation efforts.
- **Solution:** GreenOffsetX automates environmental verification on GenLayer. Validators scrape real-time satellite / LiDAR / sensor audit data on-chain (`gl.nondet.web.render`) and run decentralized LLM evaluation (`gl.vm.run_nondet`). An AI jury evaluates ecological additionality, scores impact from 0–100, and autonomously triggers credit issuance and token disbursements.

## 5. Contract Quality & Equivalence Principle
- Uses `gl.vm.run_nondet(leader_fn, validator_fn)`.
- Validators enforce semantic equality on the carbon verdict (`VERIFIED_OFFSET`, `INSUFFICIENT_IMPACT`, `FAILED_EVIDENCE`) and enforce a score delta tolerance `<= 20` points across LLM runs while permitting phrasing variations in the audit report summary.
- Comprehensive handling of edge cases (SSRF/local IP block, invalid URLs, offline 404 sources, unparsable JSON, and replay prevention).

## 6. Test Suite
- **Framework:** `gltest` + `pytest`
- **Result:** `10/10 PASSING` (100% test pass rate) covering initial state, submissions, input validations, consensus verdicts, refunds, and cancellations.
