import pytest
import json
from gltest import *
from conftest import sim_installMocks


@pytest.fixture
def contract(direct_deploy):
    return direct_deploy("contracts/green_offset_x.py")


def test_initial_state(contract, direct_vm):
    assert contract.get_project_count() == 0
    owner_str = contract.get_owner().lower()
    expected_sender = direct_vm.sender.hex().lower() if isinstance(direct_vm.sender, bytes) else str(direct_vm.sender).lower()
    if not expected_sender.startswith("0x"):
        expected_sender = "0x" + expected_sender
    assert owner_str == expected_sender

    stats = json.loads(contract.get_stats())
    assert stats["total_projects"] == 0
    assert stats["verified_count"] == 0
    assert stats["total_offset_issued"] == "0"


def test_submit_carbon_project_success(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 5000

    pid = contract.submit_carbon_project(
        project_name="Amazonian Reforestation Canopy Initiative",
        description="Reforestation project restoring native biodiversity with verifiable multi-spectral satellite imagery and carbon sequestration tracking.",
        audit_report_url="https://climate-registry.org/reports/amazon-reforestation-2026.json"
    )

    assert pid == "1"
    assert contract.get_project_count() == 1

    p = json.loads(contract.get_project("1"))
    assert p["project_id"] == "1"
    assert p["proposer"] == direct_alice.as_hex.lower()
    assert "Amazonian Reforestation" in p["project_name"]
    assert p["deposit_amount"] == "5000"
    assert p["status"] == "PENDING"
    assert p["verdict"] == "PENDING"
    assert p["impact_score"] == 0

    stats = json.loads(contract.get_stats())
    assert stats["total_projects"] == 1


def test_submit_carbon_project_validations(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 1000

    # 1. Short name (< 5 chars)
    with pytest.raises(Exception, match="Project name is too short"):
        contract.submit_carbon_project(
            project_name="Eco",
            description="Valid description with more than twenty characters long.",
            audit_report_url="https://climate-registry.org/audit/123"
        )

    # 2. Short description (< 20 chars)
    with pytest.raises(Exception, match="Description is too short"):
        contract.submit_carbon_project(
            project_name="Valid Project Name",
            description="Too short",
            audit_report_url="https://climate-registry.org/audit/123"
        )

    # 3. Invalid URL scheme
    with pytest.raises(Exception, match="URL must start with http:// or https://"):
        contract.submit_carbon_project(
            project_name="Valid Project Name",
            description="Valid description with more than twenty characters long.",
            audit_report_url="ftp://climate-registry.org/audit/123"
        )

    # 4. SSRF / Localhost attempt
    with pytest.raises(Exception, match="Local and private network URLs are prohibited"):
        contract.submit_carbon_project(
            project_name="Valid Project Name",
            description="Valid description with more than twenty characters long.",
            audit_report_url="http://127.0.0.1:8000/audit"
        )


def test_verify_carbon_project_not_found(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="Carbon project not found"):
        contract.verify_carbon_impact("999")


def test_verify_carbon_impact_verified_success(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 8000

    pid = contract.submit_carbon_project(
        project_name="Mangrove Blue Carbon Sequestration Basin",
        description="Restoration of degraded coastal mangrove forests with drone LiDAR biomass measurements and satellite NDVI ground truthing.",
        audit_report_url="https://bluecarbon.org/audits/mangrove-basin-alpha.json"
    )

    audit_web_content = """
    {
      "project": "Mangrove Blue Carbon Sequestration Basin",
      "biomass_growth_rate": "12.4%",
      "verified_carbon_offset_tco2e": 45000,
      "ndvi_spectral_index": 0.82,
      "audit_status": "APPROVED_VERIFIED_ADDITIONALITY"
    }
    """

    sim_installMocks({
        "web_mocks": {
            ".*bluecarbon.org.*": {"status": 200, "body": audit_web_content}
        },
        "llm_mocks": {
            "impact_score": 88,
            "verdict": "VERIFIED_OFFSET",
            "audit_summary": "Extensive mangrove biomass growth and satellite NDVI verification confirm 45,000 tCO2e additionality."
        }
    }, vm=direct_vm)

    contract.verify_carbon_impact(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "VERIFIED"
    assert p["verdict"] == "VERIFIED_OFFSET"
    assert p["impact_score"] == 88
    assert p["payout"] == "8000"
    assert "mangrove biomass growth" in p["audit_summary"]

    stats = json.loads(contract.get_stats())
    assert stats["verified_count"] == 1
    assert stats["total_offset_issued"] == "8000"


def test_verify_carbon_impact_insufficient_impact_rejected(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 4000

    pid = contract.submit_carbon_project(
        project_name="Suburban Lawn Replacement Initiative",
        description="Converting residential turf grass into decorative gravel gardens with minimal documented carbon sequestration impact.",
        audit_report_url="https://climate-registry.org/audits/suburban-lawn.json"
    )

    audit_web_content = """
    {
      "project": "Suburban Lawn Replacement Initiative",
      "biomass_growth_rate": "0.1%",
      "verified_carbon_offset_tco2e": 2,
      "audit_status": "NEGLIGIBLE_IMPACT"
    }
    """

    sim_installMocks({
        "web_mocks": {
            ".*climate-registry.org.*": {"status": 200, "body": audit_web_content}
        },
        "llm_mocks": {
            "impact_score": 25,
            "verdict": "INSUFFICIENT_IMPACT",
            "audit_summary": "Insignificant carbon sequestration detected. Project fails environmental additionality threshold."
        }
    }, vm=direct_vm)

    contract.verify_carbon_impact(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "REJECTED"
    assert p["verdict"] == "INSUFFICIENT_IMPACT"
    assert p["impact_score"] == 25
    assert p["payout"] == "0"
    assert "Insignificant carbon sequestration" in p["audit_summary"]

    stats = json.loads(contract.get_stats())
    assert stats["verified_count"] == 0
    assert stats["total_offset_issued"] == "0"


def test_verify_carbon_impact_failed_evidence_refund(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 3500

    pid = contract.submit_carbon_project(
        project_name="Boreal Peatland Restoration Zone",
        description="Peatland re-wetting project to prevent methane leakage with water table sensor telemetry.",
        audit_report_url="https://climate-registry.org/broken-link-404"
    )

    sim_installMocks({
        "web_mocks": {
            ".*broken-link-404.*": {"status": 404, "body": "404 Not Found - Sensor stream unavailable"}
        }
    }, vm=direct_vm)

    contract.verify_carbon_impact(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "FAILED_EVIDENCE"
    assert p["verdict"] == "FAILED_EVIDENCE"
    assert p["impact_score"] == 0
    assert p["payout"] == "3500"
    assert "offline or inaccessible" in p["audit_summary"]

    stats = json.loads(contract.get_stats())
    assert stats["verified_count"] == 0
    assert stats["total_offset_issued"] == "0"


def test_cannot_reverify_verified_project(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 2000

    pid = contract.submit_carbon_project(
        project_name="Highland Reforestation Ridge",
        description="Planting 50,000 native pine saplings on eroded slopes with verifiable satellite tracking.",
        audit_report_url="https://forestry.org/audits/highland.json"
    )

    sim_installMocks({
        "web_mocks": {
            ".*": {"status": 200, "body": "Valid verified satellite report"}
        },
        "llm_mocks": {
            "impact_score": 85,
            "verdict": "VERIFIED_OFFSET",
            "audit_summary": "Highland reforestation verified successfully."
        }
    }, vm=direct_vm)

    contract.verify_carbon_impact(pid)

    with pytest.raises(Exception, match="Carbon project has already been verified"):
        contract.verify_carbon_impact(pid)


def test_cancel_project_by_proposer(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 1500

    pid = contract.submit_carbon_project(
        project_name="Urban Rooftop Garden Array",
        description="Installation of green roof vegetated mats across commercial warehouse complex.",
        audit_report_url="https://urban-eco.org/audits/rooftop1.json"
    )

    contract.cancel_project(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "CANCELLED"
    assert p["verdict"] == "CANCELLED"
    assert p["payout"] == "1500"
    assert "Cancelled by proposer" in p["audit_summary"]

    with pytest.raises(Exception, match="Only pending projects can be cancelled"):
        contract.cancel_project(pid)


def test_cancel_project_unauthorized(contract, direct_vm, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    direct_vm.value = 1000

    pid = contract.submit_carbon_project(
        project_name="Biochar Soil Enrichment Parcel",
        description="Distribution of pyrolysis biochar to agricultural soils for permanent carbon sequestration.",
        audit_report_url="https://biochar-test.org/audits/parcel4.json"
    )

    # Bob tries to cancel Alice's project
    direct_vm.sender = direct_bob
    with pytest.raises(Exception, match="Only project proposer can cancel"):
        contract.cancel_project(pid)
