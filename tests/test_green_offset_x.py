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

    stats = json.loads(contract.get_vault_stats())
    assert stats["total_projects"] == 0
    assert stats["verified_count"] == 0
    assert stats["total_tonnes_verified"] == "0"
    assert stats["buyer_pool_balance"] == "0"
    assert stats["buffer_reserve_pool"] == "0"
    assert stats["price_per_ton"] == 10


def test_fund_buyer_pool(contract, direct_vm, direct_bob):
    direct_vm.sender = direct_bob
    direct_vm.value = 20000

    contract.fund_buyer_pool(
        sponsor_name="Global Climate Fund ESG Pool",
        price_per_ton=15
    )

    stats = json.loads(contract.get_vault_stats())
    assert stats["buyer_pool_balance"] == "20000"
    assert stats["price_per_ton"] == 15


def test_submit_carbon_mrv_success(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 1000

    pid = contract.submit_carbon_mrv(
        project_name="Sumatra Mangrove Blue Carbon MRV Parcel",
        ecosystem_type="MANGROVE",
        ground_sensor_url="https://iot-sensors.eco/sumatra/flux-tower-stream.json",
        satellite_report_url="https://sentinel-hub.org/reports/sumatra-ndvi-2026.json",
        claimed_tonnes=500
    )

    assert pid == "1"
    assert contract.get_project_count() == 1

    p = json.loads(contract.get_project("1"))
    assert p["project_id"] == "1"
    assert p["proposer"] == direct_alice.as_hex.lower()
    assert "Sumatra Mangrove" in p["project_name"]
    assert p["ecosystem_type"] == "MANGROVE"
    assert p["staked_bond"] == "1000"
    assert p["claimed_tonnes"] == 500
    assert p["verified_tonnes"] == 0
    assert p["status"] == "PENDING"
    assert p["verdict"] == "PENDING"


def test_submit_carbon_mrv_validations(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 1000

    # 1. Short name (< 5 chars)
    with pytest.raises(Exception, match="Project name is too short"):
        contract.submit_carbon_mrv(
            project_name="Tree",
            ecosystem_type="MANGROVE",
            ground_sensor_url="https://sensors.org/telemetry",
            satellite_report_url="https://satellite.org/ndvi",
            claimed_tonnes=100
        )

    # 2. Invalid ecosystem
    with pytest.raises(Exception, match="Invalid ecosystem type"):
        contract.submit_carbon_mrv(
            project_name="Valid Rainforest Initiative",
            ecosystem_type="INDUSTRIAL_FACTORY",
            ground_sensor_url="https://sensors.org/telemetry",
            satellite_report_url="https://satellite.org/ndvi",
            claimed_tonnes=100
        )

    # 3. Stake bond below 500 GEN
    direct_vm.value = 400
    with pytest.raises(Exception, match="Minimum verification stake bond is 500 GEN"):
        contract.submit_carbon_mrv(
            project_name="Valid Rainforest Initiative",
            ecosystem_type="REFORESTATION",
            ground_sensor_url="https://sensors.org/telemetry",
            satellite_report_url="https://satellite.org/ndvi",
            claimed_tonnes=100
        )

    direct_vm.value = 1000
    # 4. Zero claimed tonnes
    with pytest.raises(Exception, match="Claimed tonnes must be greater than zero"):
        contract.submit_carbon_mrv(
            project_name="Valid Rainforest Initiative",
            ecosystem_type="REFORESTATION",
            ground_sensor_url="https://sensors.org/telemetry",
            satellite_report_url="https://satellite.org/ndvi",
            claimed_tonnes=0
        )

    # 5. SSRF / Localhost blocking
    with pytest.raises(Exception, match="Local and private network URLs are prohibited"):
        contract.submit_carbon_mrv(
            project_name="Valid Rainforest Initiative",
            ecosystem_type="REFORESTATION",
            ground_sensor_url="http://127.0.0.1:8080/sensor",
            satellite_report_url="https://satellite.org/ndvi",
            claimed_tonnes=100
        )


def test_verify_carbon_mrv_not_found(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    with pytest.raises(Exception, match="Carbon project not found"):
        contract.verify_carbon_mrv("999")


def test_verify_carbon_mrv_verified_issuance(contract, direct_vm, direct_alice, direct_bob):
    # 1. Sponsor funds buyer liquidity pool
    direct_vm.sender = direct_bob
    direct_vm.value = 10000
    contract.fund_buyer_pool("Climate ESG Liquidity Vault", price_per_ton=10)

    # 2. Proposer submits project with 1,000 GEN stake bond
    direct_vm.sender = direct_alice
    direct_vm.value = 1000
    pid = contract.submit_carbon_mrv(
        project_name="Amazonian Agroforestry Carbon Sink",
        ecosystem_type="AGROFORESTRY",
        ground_sensor_url="https://iot-ground.org/amazon/parcelA-flux.json",
        satellite_report_url="https://copernicus-sentinel.eu/amazon/canopy-ndvi.json",
        claimed_tonnes=400
    )

    ground_data = """
    {
      "sensor_station": "AMZ-FLUX-01",
      "co2_flux_net_uptake": "4.8 gC/m2/day",
      "biomass_annual_growth_rate": "8.5%",
      "soil_organic_carbon_gain": "1.2 tC/ha"
    }
    """

    sat_data = """
    {
      "mission": "Sentinel-2 Multi-Spectral",
      "mean_ndvi_spectral_index": 0.84,
      "canopy_cover_percentage": "91.2%",
      "deforestation_anomaly_detected": false
    }
    """

    sim_installMocks({
        "web_mocks": {
            ".*iot-ground.org.*": {"status": 200, "body": ground_data},
            ".*copernicus-sentinel.eu.*": {"status": 200, "body": sat_data}
        },
        "llm_mocks": {
            "verified_tonnes": 380,
            "consistency_score": 94,
            "verdict": "VERIFIED_ISSUANCE",
            "audit_summary": "High cross-source agreement (94%). Verified 380 tonnes CO2e drawdown with no anomaly flags."
        }
    }, vm=direct_vm)

    contract.verify_carbon_mrv(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "VERIFIED"
    assert p["verdict"] == "VERIFIED_ISSUANCE"
    assert p["verified_tonnes"] == 380
    assert p["consistency_score"] == 94

    # Valuation: 380 tonnes * 10 GEN = 3,800 GEN
    # 15% buffer reserve = 570 GEN
    # 85% net reward = 3,230 GEN
    assert p["payout_amount"] == "3230"
    assert p["buffer_allocated"] == "570"

    stats = json.loads(contract.get_vault_stats())
    assert stats["verified_count"] == 1
    assert stats["total_tonnes_verified"] == "380"
    # Remaining buyer pool: 10,000 - 3,800 = 6,200 GEN
    assert stats["buyer_pool_balance"] == "6200"
    # Buffer reserve pool: 570 GEN
    assert stats["buffer_reserve_pool"] == "570"


def test_verify_carbon_mrv_fraud_discrepancy_slashed(contract, direct_vm, direct_alice):
    # Proposer submits fake project with 1,000 GEN bond
    direct_vm.sender = direct_alice
    direct_vm.value = 1000
    pid = contract.submit_carbon_mrv(
        project_name="Highland Pine Reforestation Project",
        ecosystem_type="REFORESTATION",
        ground_sensor_url="https://fraudulent-sensor.org/highland-data.json",
        satellite_report_url="https://landsat.nasa.gov/highland-satellite.json",
        claimed_tonnes=600
    )

    ground_spoofed = """
    {
      "sensor": "SPOOFED_STREAM",
      "claimed_biomass_growth": "+65%",
      "reported_absorption": "600 tCO2e"
    }
    """

    sat_real = """
    {
      "mission": "Landsat-9 Thermal & Optical",
      "canopy_loss": "-45%",
      "wildfire_burn_scar": "CONFIRMED_RECENT_BURN",
      "mean_ndvi": 0.12
    }
    """

    sim_installMocks({
        "web_mocks": {
            ".*fraudulent-sensor.org.*": {"status": 200, "body": ground_spoofed},
            ".*landsat.nasa.gov.*": {"status": 200, "body": sat_real}
        },
        "llm_mocks": {
            "verified_tonnes": 0,
            "consistency_score": 8,
            "verdict": "FRAUD_DISCREPANCY",
            "audit_summary": "Critical contradiction: Ground sensor claims +65% growth while satellite confirms extensive wildfire burn scar and tree loss."
        }
    }, vm=direct_vm)

    contract.verify_carbon_mrv(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "REJECTED_DISCREPANCY"
    assert p["verdict"] == "FRAUD_DISCREPANCY"
    assert p["payout_amount"] == "0"
    assert p["verified_tonnes"] == 0

    # Proposer's 1,000 GEN staked bond is slashed into buffer reserve pool!
    stats = json.loads(contract.get_vault_stats())
    assert stats["buffer_reserve_pool"] == "1000"


def test_verify_carbon_mrv_failed_evidence_refund(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 800

    pid = contract.submit_carbon_mrv(
        project_name="Boreal Peatland Methane Abatement",
        ecosystem_type="PEATLAND",
        ground_sensor_url="https://peatland.org/sensor-stream.json",
        satellite_report_url="https://satellite.org/dead-link-404.json",
        claimed_tonnes=300
    )

    sim_installMocks({
        "web_mocks": {
            ".*peatland.org.*": {"status": 200, "body": "Ground water table normal"},
            ".*dead-link-404.*": {"status": 404, "body": "404 Not Found - Data unavailable"}
        }
    }, vm=direct_vm)

    contract.verify_carbon_mrv(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "FAILED_EVIDENCE"
    assert p["verdict"] == "INSUFFICIENT_DATA"
    assert p["payout_amount"] == "0"
    assert "offline or inaccessible" in p["audit_summary"]


def test_cannot_reverify_verified_project(contract, direct_vm, direct_alice, direct_bob):
    direct_vm.sender = direct_bob
    direct_vm.value = 5000
    contract.fund_buyer_pool("ESG Pool", price_per_ton=10)

    direct_vm.sender = direct_alice
    direct_vm.value = 1000
    pid = contract.submit_carbon_mrv(
        project_name="Coastal Kelp Blue Carbon Parcel",
        ecosystem_type="MANGROVE",
        ground_sensor_url="https://sensors.eco/kelp.json",
        satellite_report_url="https://sentinel.org/kelp.json",
        claimed_tonnes=200
    )

    sim_installMocks({
        "web_mocks": {
            ".*": {"status": 200, "body": "Valid verified marine telemetry"}
        },
        "llm_mocks": {
            "verified_tonnes": 200,
            "consistency_score": 90,
            "verdict": "VERIFIED_ISSUANCE",
            "audit_summary": "Kelp bed verified."
        }
    }, vm=direct_vm)

    contract.verify_carbon_mrv(pid)

    with pytest.raises(Exception, match="Project has already undergone MRV verification"):
        contract.verify_carbon_mrv(pid)


def test_cancel_project_by_proposer(contract, direct_vm, direct_alice):
    direct_vm.sender = direct_alice
    direct_vm.value = 600

    pid = contract.submit_carbon_mrv(
        project_name="Biochar Carbon Enriched Farmland",
        ecosystem_type="BIOCHAR",
        ground_sensor_url="https://agri.org/biochar-stream.json",
        satellite_report_url="https://satellite.org/soil-index.json",
        claimed_tonnes=150
    )

    contract.cancel_project(pid)

    p = json.loads(contract.get_project(pid))
    assert p["status"] == "CANCELLED"
    assert p["verdict"] == "CANCELLED"
    assert "Withdrawn by proposer" in p["audit_summary"]

    with pytest.raises(Exception, match="Only pending projects can be cancelled"):
        contract.cancel_project(pid)


def test_cancel_project_unauthorized(contract, direct_vm, direct_alice, direct_bob):
    direct_vm.sender = direct_alice
    direct_vm.value = 700

    pid = contract.submit_carbon_mrv(
        project_name="Degraded Soil Agroforestry Plot",
        ecosystem_type="AGROFORESTRY",
        ground_sensor_url="https://agri.org/sensors.json",
        satellite_report_url="https://satellite.org/canopy.json",
        claimed_tonnes=100
    )

    # Bob tries to cancel Alice's project
    direct_vm.sender = direct_bob
    with pytest.raises(Exception, match="Only project proposer can cancel"):
        contract.cancel_project(pid)
