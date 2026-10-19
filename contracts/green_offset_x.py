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
class CarbonProject:
    project_id: str
    proposer: Address
    project_name: str
    description: str
    audit_report_url: str       # Satellite data or environmental sensor audit URL
    deposit_amount: bigint
    status: str                 # "PENDING", "VERIFIED", "REJECTED", "FAILED_EVIDENCE", "CANCELLED"
    verdict: str                # "VERIFIED_OFFSET", "INSUFFICIENT_IMPACT", "FAILED_EVIDENCE", "CANCELLED"
    impact_score: bigint        # 0 to 100 impact score
    audit_summary: str
    created_at: bigint
    resolved_at: bigint
    payout: bigint

class Contract(gl.Contract):
    """
    GreenOffsetX: Dynamic Carbon Credit & Environmental Impact Verifier Protocol on GenLayer
    """
    owner: Address
    project_count: bigint
    projects: TreeMap[str, CarbonProject]
    verified_count: bigint
    total_offset_issued: bigint

    def __init__(self):
        self.owner = _get_sender()
        self.project_count = bigint(0)
        self.verified_count = bigint(0)
        self.total_offset_issued = bigint(0)

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
    def submit_carbon_project(self, project_name: str, description: str, audit_report_url: str) -> str:
        """
        Submit a green/carbon offset project for autonomous environmental verification.
        """
        deposit = bigint(gl.message.value)
        clean_name = project_name.strip()
        clean_desc = description.strip()
        clean_url = _validate_url(audit_report_url)

        if len(clean_name) < 5:
            raise gl.UserError("Project name is too short.")
        if len(clean_desc) < 20:
            raise gl.UserError("Description is too short.")

        self.project_count += bigint(1)
        pid = str(self.project_count)
        now_ts = self._get_current_timestamp()

        self.projects[pid] = CarbonProject(
            project_id=pid,
            proposer=_get_sender(),
            project_name=clean_name,
            description=clean_desc,
            audit_report_url=clean_url,
            deposit_amount=deposit,
            status="PENDING",
            verdict="PENDING",
            impact_score=bigint(0),
            audit_summary="Awaiting validator carbon offset consensus.",
            created_at=now_ts if now_ts > bigint(0) else self.project_count,
            resolved_at=bigint(0),
            payout=bigint(0)
        )
        return pid

    @gl.public.write
    def verify_carbon_impact(self, project_id: str) -> None:
        """
        Validators scrape the environmental audit URL on-chain and use GenLayer LLM jury consensus
        to evaluate emission reduction and carbon offset validity.
        """
        if project_id not in self.projects:
            raise gl.UserError("Carbon project not found.")

        proj = self.projects[project_id]
        if proj.status != "PENDING":
            raise gl.UserError("Carbon project has already been verified.")

        name_local = str(proj.project_name)
        desc_local = str(proj.description)
        url_local = str(proj.audit_report_url)

        def leader_fn():
            web_content = ""
            try:
                res = gl.nondet.web.render(url_local, mode="text")
                if hasattr(res, "content"):
                    web_content = res.content
                elif isinstance(res, dict) and "body" in res:
                    web_content = res["body"]
                else:
                    web_content = str(res)
            except Exception:
                web_content = ""

            lower_web = web_content[:500].lower() if web_content else ""
            if len(web_content.strip()) < 15 or "404 not found" in lower_web or "error" in lower_web:
                return {
                    "impact_score": 0,
                    "verdict": "FAILED_EVIDENCE",
                    "audit_summary": "Audit report source is offline or inaccessible."
                }

            snippet = web_content[:4000]

            prompt = f"""You are an expert Environmental Auditor and Carbon Credit Verifier.
Evaluate the validity and emission reduction impact of the following carbon offset project based on the scraped audit report.

PROJECT NAME: {name_local}
DESCRIPTION: {desc_local}

SCRAPED AUDIT REPORT EVIDENCE:
\"\"\"
{snippet}
\"\"\"

EVALUATION RULES:
- Assign an impact_score from 0 to 100 based on verified carbon reduction and environmental additionality (0 = insufficient/fraudulent, 100 = exceptional carbon offset).
- Determine verdict: "VERIFIED_OFFSET" if impact_score >= 70, otherwise "INSUFFICIENT_IMPACT". If evidence is unparsable, return "FAILED_EVIDENCE".
- Provide a concise professional audit summary (max 250 characters).

OUTPUT FORMAT:
Respond ONLY with a VALID JSON object (no markdown, no backticks):
{{
  "impact_score": <integer 0-100>,
  "verdict": "VERIFIED_OFFSET" | "INSUFFICIENT_IMPACT" | "FAILED_EVIDENCE",
  "audit_summary": "<concise professional audit summary>"
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

                score = int(parsed.get("impact_score", 0))
                score = max(0, min(100, score))
                verdict = str(parsed.get("verdict", "INSUFFICIENT_IMPACT")).strip().upper()
                valid_v = ("VERIFIED_OFFSET", "INSUFFICIENT_IMPACT", "FAILED_EVIDENCE")
                if verdict not in valid_v:
                    verdict = "VERIFIED_OFFSET" if score >= 70 else "INSUFFICIENT_IMPACT"
                summary = str(parsed.get("audit_summary", "Audited."))[:250]

                return {
                    "impact_score": score,
                    "verdict": verdict,
                    "audit_summary": summary
                }
            except Exception as e:
                return {
                    "impact_score": 0,
                    "verdict": "FAILED_EVIDENCE",
                    "audit_summary": f"Evaluation error: {str(e)[:100]}"
                }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "verdict" not in leader:
                return False

            valid_v = ("VERIFIED_OFFSET", "INSUFFICIENT_IMPACT", "FAILED_EVIDENCE")
            l_v = str(leader.get("verdict", "")).strip().upper()
            if l_v not in valid_v:
                return False

            mine = leader_fn()
            m_v = str(mine.get("verdict", "")).strip().upper()

            if l_v != m_v:
                return False

            if l_v != "FAILED_EVIDENCE":
                l_score = int(leader.get("impact_score", 0))
                m_score = int(mine.get("impact_score", 0))
                if abs(l_score - m_score) > 20:
                    return False

            return True

        adjudication_res = gl.vm.run_nondet(leader_fn, validator_fn)
        if isinstance(adjudication_res, dict):
            final_res = adjudication_res
        else:
            try:
                final_res = json.loads(str(adjudication_res))
            except Exception:
                final_res = {"impact_score": 0, "verdict": "FAILED_EVIDENCE", "audit_summary": "Consensus parse failed."}

        score = int(final_res.get("impact_score", 0))
        score_clamped = max(0, min(100, score))
        verdict = str(final_res.get("verdict", "FAILED_EVIDENCE")).strip().upper()
        summary = str(final_res.get("audit_summary", "Processed."))

        proj.impact_score = bigint(score_clamped)
        proj.verdict = verdict
        proj.audit_summary = summary
        proj.status = "VERIFIED" if verdict == "VERIFIED_OFFSET" else ("REJECTED" if verdict == "INSUFFICIENT_IMPACT" else "FAILED_EVIDENCE")
        now_ts = self._get_current_timestamp()
        proj.resolved_at = now_ts if now_ts > bigint(0) else self.project_count

        if proj.status == "VERIFIED":
            self.verified_count += bigint(1)
            self.total_offset_issued += proj.deposit_amount
            proj.payout = proj.deposit_amount
            self.projects[project_id] = proj
            _safe_transfer(proj.proposer, proj.deposit_amount)
        elif proj.status == "REJECTED":
            proj.payout = bigint(0)
            self.projects[project_id] = proj
            _safe_transfer(self.owner, proj.deposit_amount)
        else:
            proj.payout = proj.deposit_amount
            self.projects[project_id] = proj
            _safe_transfer(proj.proposer, proj.deposit_amount)

    @gl.public.write
    def cancel_project(self, project_id: str) -> None:
        """Allow proposer to cancel pending project and recover deposit."""
        if project_id not in self.projects:
            raise gl.UserError("Carbon project not found.")

        proj = self.projects[project_id]
        if proj.status != "PENDING":
            raise gl.UserError("Only pending projects can be cancelled.")

        if _addr_str(_get_sender()) != _addr_str(proj.proposer):
            raise gl.UserError("Only project proposer can cancel.")

        proj.status = "CANCELLED"
        proj.verdict = "CANCELLED"
        proj.audit_summary = "Cancelled by proposer."
        refund = proj.deposit_amount
        proj.payout = refund
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
            "description": p.description,
            "audit_report_url": p.audit_report_url,
            "deposit_amount": str(p.deposit_amount),
            "status": p.status,
            "verdict": p.verdict,
            "impact_score": int(p.impact_score),
            "audit_summary": p.audit_summary,
            "created_at": str(p.created_at),
            "resolved_at": str(p.resolved_at),
            "payout": str(p.payout)
        })

    @gl.public.view
    def get_stats(self) -> str:
        return json.dumps({
            "total_projects": int(self.project_count),
            "verified_count": int(self.verified_count),
            "total_offset_issued": str(self.total_offset_issued)
        })
