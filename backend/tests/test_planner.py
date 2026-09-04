import pytest
from app.planning.planner import MigrationPlanner
from app.air.schema import AIR, Route, APIEndpoint, Provenance, AuthStrategy
from app.security.models import SecurityFinding
import uuid

def test_migration_planner_routing():
    air = AIR(
        source_version="v1", framework="React", language="TypeScript",
        routes=[
            Route(path="/", component_id="Home", provenance=Provenance(confidence="HIGH", detection_method="manual")),
            Route(path="/user-profile", component_id="Profile", auth_required=True, provenance=Provenance(confidence="HIGH", detection_method="manual"))
        ],
        apis=[
            APIEndpoint(id="GET_/api/users", method="GET", path="/api/users", provenance=Provenance(confidence="HIGH", detection_method="manual"))
        ]
    )
    
    planner = MigrationPlanner(air, [])
    plan = planner.generate_plan()
    
    assert plan.target_platform == "Flutter"
    assert len(plan.screens) == 2
    assert plan.screens[0].name == "HomeScreen"
    assert plan.screens[1].name == "User_profileScreen"
    assert plan.screens[1].requires_auth is True
    
    assert len(plan.services) == 1
    assert plan.services[0].name == "ApiService"
    assert plan.services[0].derived_from_apis == ["GET_/api/users"]

def test_migration_planner_security_constraints():
    air = AIR(
        source_version="v1", framework="React", language="TypeScript",
        authentication=AuthStrategy(type="session", details={"mechanism": "cookie"}, provenance=Provenance(confidence="HIGH", detection_method="manual"))
    )
    
    findings = [
        SecurityFinding(
            finding_id=str(uuid.uuid4()), organization_id="org", project_id="proj", migration_id="mig",
            source_version="v1", scanner="test", rule_id="test", category="test", severity="CRITICAL",
            title="test", description="test", confidence="HIGH"
        )
    ]
    
    planner = MigrationPlanner(air, findings)
    plan = planner.generate_plan()
    
    assert "CRITICAL security findings must be resolved" in plan.security_requirements[0]
    assert "Cookie-based web authentication" in plan.unsupported_features[0]
