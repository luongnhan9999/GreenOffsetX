# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json

try:
    gl.UserError = gl.vm.UserError
except Exception:
    pass

def _addr_str(addr: Address) -> str:
    """Safely format an Address instance into a lowercase hex string."""
    try:
        return addr.as_hex.lower()
    except Exception:
        return str(addr).lower()

def _get_sender() -> Address:
    """Safely resolve transaction sender across GenVM runtime environments."""
    try:
        if hasattr(gl, "message"):
            if hasattr(gl.message, "sender"):
                return gl.message.sender
            if hasattr(gl.message, "sender_address"):
                return gl.message.sender_address
    except Exception:
        pass
    try:
        if hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):
            s = gl.message_raw.get("from") or gl.message_raw.get("sender")
            if s:
                return Address(str(s))
    except Exception:
        pass
    raise gl.UserError("Cannot resolve sender address.")

def _safe_transfer(recipient: Address, amount: bigint) -> None:
    """Safely transfer native GEN tokens."""
    if amount <= bigint(0):
        return
    gl.get_contract_at(recipient).emit_transfer(value=u256(int(amount)))

def _validate_url(raw_url: str) -> str:
    """Validate URL scheme and block private/SSRF IP addresses."""
    clean = raw_url.strip()
    if not (clean.startswith("http://") or clean.startswith("https://")):
        raise gl.UserError("URL must start with http:// or https://")
    clean_lower = clean.lower()
    for blocked in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "192.168.", "10.", "172.16.", "169.254."):
        if blocked in clean_lower:
            raise gl.UserError("Local and private network URLs are prohibited.")
    return clean

@allow_storage
@dataclass
class CarbonMRVProject:
    project_id: str
    proposer: Address
    project_name: str
    ecosystem_type: str         # "MANGROVE", "REFORESTATION", "PEATLAND", "BIOCHAR"
    ground_sensor_url: str      # Source 1: In-situ IoT flux / soil carbon telemetry stream
    satellite_report_url: str   # Source 2: Independent multi-spectral remote sensing (NDVI / canopy)
    staked_bond: bigint         # Proposer security bond (slashed if fraud/spoofing detected)
    claimed_tonnes: bigint      # Target claimed metric tonnes of CO2 drawdown
    verified_tonnes: bigint     # Net verified metric tonnes of CO2 sequestered
    consistency_score: bigint   # Cross-source agreement score (0-100%)
    status: str                 # "PENDING", "VERIFIED", "REJECTED_DISCREPANCY", "FAILED_EVIDENCE", "CANCELLED"
    verdict: str                # "VERIFIED_ISSUANCE", "FRAUD_DISCREPANCY", "INSUFFICIENT_DATA", "CANCELLED"
    audit_summary: str          # Concise AI consensus findings
    payout_amount: bigint       # 85% net proceeds disbursed to eco-steward
    buffer_allocated: bigint    # 15% permanence buffer reserve locked against reversal risks
    created_at: bigint
    resolved_at: bigint

class Contract(gl.Contract):
    """
    GreenOffsetX: Autonomous Cross-Source MRV & Dynamic Carbon Credit Issuance Vault.
    Performs on-chain multi-source cross-correlation between ground IoT telemetry and
    independent satellite remote sensing, minting verified carbon credits with a 15%
    permanence buffer reserve and slashing fraudulent claimants.
    """
    owner: Address
    project_count: bigint
    projects: TreeMap[str, CarbonMRVProject]
    verified_count: bigint
    total_tonnes_verified: bigint
    buyer_pool_balance: bigint
    buffer_reserve_pool: bigint
    price_per_ton: bigint

    def __init__(self):
        self.owner = _get_sender()
        self.project_count = bigint(0)
        self.verified_count = bigint(0)
        self.total_tonnes_verified = bigint(0)
        self.buyer_pool_balance = bigint(0)
        self.buffer_reserve_pool = bigint(0)
        self.price_per_ton = bigint(10)  # Default 10 GEN per metric tonne CO2

    def _get_current_timestamp(self) -> bigint:
        try:
            from datetime import datetime
            dt_raw = getattr(gl.message, "datetime", None)
            if dt_raw is None and hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):
                dt_raw = gl.message_raw.get("datetime")
            if dt_raw:
                dt_str = str(dt_raw).strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(dt_str)
                ts = int(dt.timestamp())
                if ts > 0:
                    return bigint(ts)
        except Exception:
            pass
        try:
            if hasattr(gl, "block") and hasattr(gl.block, "timestamp"):
                ts = int(gl.block.timestamp)
                if ts > 0:
                    return bigint(ts)
        except Exception:
            pass
        return bigint(0)

    @gl.public.view
    def get_owner(self) -> str:
        return _addr_str(self.owner)

    @gl.public.view
    def get_project_count(self) -> int:
        return int(self.project_count)

    @gl.public.write.payable
    def fund_buyer_pool(self, sponsor_name: str, price_per_ton: int) -> None:
        """
        Institutional buyers/sponsors deposit liquidity to purchase verified carbon credits.
        """
        deposit = bigint(gl.message.value)
        if deposit <= bigint(0):
            raise gl.UserError("Deposit must be greater than zero.")
        clean_name = sponsor_name.strip()
        if len(clean_name) < 2:
            raise gl.UserError("Sponsor name is required.")

        self.buyer_pool_balance += deposit
        if price_per_ton > 0:
            self.price_per_ton = bigint(price_per_ton)

    @gl.public.write.payable
    def submit_carbon_mrv(
        self,
        project_name: str,
        ecosystem_type: str,
        ground_sensor_url: str,
        satellite_report_url: str,
        claimed_tonnes: int
    ) -> str:
        """
        Submit eco-project for cross-source MRV validation with a mandatory security stake bond.
        """
        stake = bigint(gl.message.value)
        if stake < bigint(500):
            raise gl.UserError("Minimum verification stake bond is 500 GEN.")

        clean_name = project_name.strip()
        clean_type = ecosystem_type.strip().upper()
        clean_ground = _validate_url(ground_sensor_url)
        clean_sat = _validate_url(satellite_report_url)

        if len(clean_name) < 5:
            raise gl.UserError("Project name is too short.")
        valid_ecosystems = ("MANGROVE", "REFORESTATION", "PEATLAND", "BIOCHAR", "AGROFORESTRY")
        if clean_type not in valid_ecosystems:
            raise gl.UserError("Invalid ecosystem type.")
        if claimed_tonnes <= 0:
            raise gl.UserError("Claimed tonnes must be greater than zero.")

        self.project_count += bigint(1)
        pid = str(self.project_count)
        now_ts = self._get_current_timestamp()

        self.projects[pid] = CarbonMRVProject(
            project_id=pid,
            proposer=_get_sender(),
            project_name=clean_name,
            ecosystem_type=clean_type,
            ground_sensor_url=clean_ground,
            satellite_report_url=clean_sat,
            staked_bond=stake,
            claimed_tonnes=bigint(claimed_tonnes),
            verified_tonnes=bigint(0),
            consistency_score=bigint(0),
            status="PENDING",
            verdict="PENDING",
            audit_summary="Awaiting decentralized cross-source MRV consensus.",
            payout_amount=bigint(0),
            buffer_allocated=bigint(0),
            created_at=now_ts if now_ts > bigint(0) else self.project_count,
            resolved_at=bigint(0)
        )
        return pid

    @gl.public.write
    def verify_carbon_mrv(self, project_id: str) -> None:
        """
        Autonomous Multi-Source MRV: Validators fetch both Ground IoT telemetry and Satellite
        spectral imagery directly on-chain, cross-correlate additionality, and detect sensor fraud.
        """
        if project_id not in self.projects:
            raise gl.UserError("Carbon project not found.")

        proj = self.projects[project_id]
        if proj.status != "PENDING":
            raise gl.UserError("Project has already undergone MRV verification.")

        name_local = str(proj.project_name)
        eco_local = str(proj.ecosystem_type)
        ground_url = str(proj.ground_sensor_url)
        sat_url = str(proj.satellite_report_url)
        target_tonnes = int(proj.claimed_tonnes)

        def leader_fn():
            # Source 1: Scrape In-situ IoT ground sensor stream
            ground_raw = ""
            try:
                g_res = gl.nondet.web.render(ground_url, mode="text")
                ground_raw = g_res.content if hasattr(g_res, "content") else (g_res.get("body", "") if isinstance(g_res, dict) else str(g_res))
            except Exception:
                ground_raw = ""

            # Source 2: Scrape Independent Satellite remote sensing observations
            sat_raw = ""
            try:
                s_res = gl.nondet.web.render(sat_url, mode="text")
                sat_raw = s_res.content if hasattr(s_res, "content") else (s_res.get("body", "") if isinstance(s_res, dict) else str(s_res))
            except Exception:
                sat_raw = ""

            # Handle offline / 404 dead links
            g_lower = ground_raw[:400].lower() if ground_raw else ""
            s_lower = sat_raw[:400].lower() if sat_raw else ""
            if len(ground_raw.strip()) < 15 or len(sat_raw.strip()) < 15 or "404 not found" in g_lower or "404 not found" in s_lower:
                return {
                    "verified_tonnes": 0,
                    "consistency_score": 0,
                    "verdict": "INSUFFICIENT_DATA",
                    "audit_summary": "One or more telemetry sources offline or inaccessible."
                }

            ground_snippet = ground_raw[:2500]
            sat_snippet = sat_raw[:2500]

            prompt = f"""You are an expert Ecological MRV (Measurement, Reporting, and Verification) Auditor.
Perform a strict multi-source cross-correlation between in-situ Ground IoT telemetry and independent Satellite Remote Sensing.

PROJECT: {name_local} (Ecosystem: {eco_local})
CLAIMED CARBON SEQUESTRATION: {target_tonnes} metric tonnes CO2e

[SOURCE 1: GROUND SENSOR / FLUX TOWER TELEMETRY]
\"\"\"
{ground_snippet}
\"\"\"

[SOURCE 2: SATELLITE REMOTE SENSING (NDVI / CANOPY BIOMASS)]
\"\"\"
{sat_snippet}
\"\"\"

CROSS-SOURCE EVALUATION RULES:
1. Cross-Source Consistency Index (0-100): Measure statistical agreement between Ground Telemetry and Satellite Observations.
2. Sensor Spoofing & Fraud Detection:
   - If ground sensors claim heavy carbon accumulation but satellite observations show deforestation, clear-cutting, fire scars, or negligible NDVI growth, flag as "FRAUD_DISCREPANCY".
3. Net Verified Sequestration (verified_tonnes):
   - Quantify actual verified metric tonnes of CO2 drawdown (integer between 0 and {target_tonnes}).
4. Final Verdict:
   - "VERIFIED_ISSUANCE": consistency_score >= 70 AND verified_tonnes > 0 AND no fraud detected.
   - "FRAUD_DISCREPANCY": irreconcilable contradiction or fabricated sensor telemetry.
   - "INSUFFICIENT_DATA": data corrupted, vague, or insufficient to prove additionality.
5. Provide concise audit summary (max 250 characters).

OUTPUT FORMAT:
Respond ONLY with a VALID JSON object (no markdown, no backticks):
{{
  "verified_tonnes": <integer 0-{target_tonnes}>,
  "consistency_score": <integer 0-100>,
  "verdict": "VERIFIED_ISSUANCE" | "FRAUD_DISCREPANCY" | "INSUFFICIENT_DATA",
  "audit_summary": "<concise audit conclusion>"
}}"""

            try:
                raw_res = gl.nondet.exec_prompt(prompt, response_format="json")
                parsed = None
                if isinstance(raw_res, dict):
                    parsed = raw_res
                elif hasattr(raw_res, "content") and isinstance(raw_res.content, dict):
                    parsed = raw_res.content
                else:
                    text = raw_res.content if hasattr(raw_res, "content") else str(raw_res)
                    cleaned = str(text).strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    parsed = json.loads(cleaned.strip())

                v_tonnes = int(parsed.get("verified_tonnes", 0))
                v_tonnes = max(0, min(target_tonnes, v_tonnes))
                score = int(parsed.get("consistency_score", 0))
                score = max(0, min(100, score))
                verdict = str(parsed.get("verdict", "INSUFFICIENT_DATA")).strip().upper()
                valid_v = ("VERIFIED_ISSUANCE", "FRAUD_DISCREPANCY", "INSUFFICIENT_DATA")
                if verdict not in valid_v:
                    verdict = "VERIFIED_ISSUANCE" if score >= 70 and v_tonnes > 0 else "INSUFFICIENT_DATA"
                summary = str(parsed.get("audit_summary", "MRV verified."))[:250]

                return {
                    "verified_tonnes": v_tonnes,
                    "consistency_score": score,
                    "verdict": verdict,
                    "audit_summary": summary
                }
            except Exception as e:
                return {
                    "verified_tonnes": 0,
                    "consistency_score": 0,
                    "verdict": "INSUFFICIENT_DATA",
                    "audit_summary": f"MRV parsing error: {str(e)[:100]}"
                }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "verdict" not in leader:
                return False

            valid_v = ("VERIFIED_ISSUANCE", "FRAUD_DISCREPANCY", "INSUFFICIENT_DATA")
            l_v = str(leader.get("verdict", "")).strip().upper()
            if l_v not in valid_v:
                return False

            mine = leader_fn()
            m_v = str(mine.get("verdict", "")).strip().upper()

            # Strict agreement on final verdict
            if l_v != m_v:
                return False

            # If verified, enforce bounded variance on consistency and verified tonnage
            if l_v == "VERIFIED_ISSUANCE":
                l_score = int(leader.get("consistency_score", 0))
                m_score = int(mine.get("consistency_score", 0))
                if abs(l_score - m_score) > 15:
                    return False

                l_tonnes = int(leader.get("verified_tonnes", 0))
                m_tonnes = int(mine.get("verified_tonnes", 0))
                max_tonnes_variance = max(10, target_tonnes * 20 // 100)
                if abs(l_tonnes - m_tonnes) > max_tonnes_variance:
                    return False

            return True

        adjudication = gl.vm.run_nondet(leader_fn, validator_fn)
        if isinstance(adjudication, dict):
            final = adjudication
        else:
            try:
                final = json.loads(str(adjudication))
            except Exception:
                final = {"verified_tonnes": 0, "consistency_score": 0, "verdict": "INSUFFICIENT_DATA", "audit_summary": "Consensus unparsed."}

        v_tonnes = max(0, min(target_tonnes, int(final.get("verified_tonnes", 0))))
        c_score = max(0, min(100, int(final.get("consistency_score", 0))))
        verdict = str(final.get("verdict", "INSUFFICIENT_DATA")).strip().upper()
        summary = str(final.get("audit_summary", "Completed."))

        proj.verified_tonnes = bigint(v_tonnes)
        proj.consistency_score = bigint(c_score)
        proj.verdict = verdict
        proj.audit_summary = summary
        now_ts = self._get_current_timestamp()
        proj.resolved_at = now_ts if now_ts > bigint(0) else self.project_count

        if verdict == "VERIFIED_ISSUANCE":
            proj.status = "VERIFIED"
            self.verified_count += bigint(1)
            self.total_tonnes_verified += proj.verified_tonnes

            # Calculate total valuation based on price_per_ton
            total_valuation = proj.verified_tonnes * self.price_per_ton
            effective_payout = total_valuation if total_valuation <= self.buyer_pool_balance else self.buyer_pool_balance

            # Split: 85% to proposer, 15% permanence buffer reserve
            buffer_portion = (effective_payout * bigint(15)) // bigint(100)
            net_proposer_reward = effective_payout - buffer_portion

            self.buyer_pool_balance -= effective_payout
            self.buffer_reserve_pool += buffer_portion

            proj.payout_amount = net_proposer_reward
            proj.buffer_allocated = buffer_portion
            self.projects[project_id] = proj

            # Return staked bond + net carbon reward to proposer
            total_disbursed = proj.staked_bond + net_proposer_reward
            _safe_transfer(proj.proposer, total_disbursed)

        elif verdict == "FRAUD_DISCREPANCY":
            # Detected sensor spoofing / fraudulent claim: Slash proposer bond!
            proj.status = "REJECTED_DISCREPANCY"
            proj.payout_amount = bigint(0)
            proj.buffer_allocated = bigint(0)
            # Slashed bond is confiscated into permanence buffer pool
            self.buffer_reserve_pool += proj.staked_bond
            self.projects[project_id] = proj

        else:
            # INSUFFICIENT_DATA: Refund staked bond safely
            proj.status = "FAILED_EVIDENCE"
            proj.payout_amount = bigint(0)
            proj.buffer_allocated = bigint(0)
            self.projects[project_id] = proj
            _safe_transfer(proj.proposer, proj.staked_bond)

    @gl.public.write
    def cancel_project(self, project_id: str) -> None:
        """Allow proposer to withdraw pending project and reclaim staked bond."""
        if project_id not in self.projects:
            raise gl.UserError("Carbon project not found.")

        proj = self.projects[project_id]
        if proj.status != "PENDING":
            raise gl.UserError("Only pending projects can be cancelled.")

        if _addr_str(_get_sender()) != _addr_str(proj.proposer):
            raise gl.UserError("Only project proposer can cancel.")

        proj.status = "CANCELLED"
        proj.verdict = "CANCELLED"
        proj.audit_summary = "Withdrawn by proposer before MRV."
        refund = proj.staked_bond
        now_ts = self._get_current_timestamp()
        proj.resolved_at = now_ts if now_ts > bigint(0) else self.project_count
        self.projects[project_id] = proj

        if refund > bigint(0):
            _safe_transfer(proj.proposer, refund)

    @gl.public.view
    def get_project(self, project_id: str) -> str:
        if project_id not in self.projects:
            raise gl.UserError("Carbon project not found.")
        p = self.projects[project_id]
        return json.dumps({
            "project_id": p.project_id,
            "proposer": _addr_str(p.proposer),
            "project_name": p.project_name,
            "ecosystem_type": p.ecosystem_type,
            "ground_sensor_url": p.ground_sensor_url,
            "satellite_report_url": p.satellite_report_url,
            "staked_bond": str(p.staked_bond),
            "claimed_tonnes": int(p.claimed_tonnes),
            "verified_tonnes": int(p.verified_tonnes),
            "consistency_score": int(p.consistency_score),
            "status": p.status,
            "verdict": p.verdict,
            "audit_summary": p.audit_summary,
            "payout_amount": str(p.payout_amount),
            "buffer_allocated": str(p.buffer_allocated),
            "created_at": str(p.created_at),
            "resolved_at": str(p.resolved_at)
        })

    @gl.public.view
    def get_vault_stats(self) -> str:
        return json.dumps({
            "total_projects": int(self.project_count),
            "verified_count": int(self.verified_count),
            "total_tonnes_verified": str(self.total_tonnes_verified),
            "buyer_pool_balance": str(self.buyer_pool_balance),
            "buffer_reserve_pool": str(self.buffer_reserve_pool),
            "price_per_ton": int(self.price_per_ton)
        })
