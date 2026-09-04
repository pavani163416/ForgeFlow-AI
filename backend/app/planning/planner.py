from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.air.schema import AIR, Route, APIEndpoint, Provenance
from app.security.models import SecurityFinding

class MobileScreen(BaseModel):
    name: str
    derived_from_route: str
    components: List[str] = Field(default_factory=list)
    requires_auth: bool = False

class MobileService(BaseModel):
    name: str
    methods: List[str]
    derived_from_apis: List[str]

class MigrationPlan(BaseModel):
    target_platform: str = "Flutter"
    screens: List[MobileScreen] = Field(default_factory=list)
    services: List[MobileService] = Field(default_factory=list)
    unsupported_features: List[str] = Field(default_factory=list)
    manual_actions: List[str] = Field(default_factory=list)
    security_requirements: List[str] = Field(default_factory=list)

class MigrationPlanner:
    """
    Derives a structured Mobile architecture from the Web AIR.
    Explicitly flags unsupported features rather than inventing behavior.
    """
    def __init__(self, air: AIR, security_findings: List[SecurityFinding]):
        self.air = air
        self.security_findings = security_findings
        
    def generate_plan(self) -> MigrationPlan:
        plan = MigrationPlan()
        
        # 1. Map Routes to Screens
        for route in self.air.routes:
            screen_name = self._route_to_screen_name(route.path)
            plan.screens.append(MobileScreen(
                name=screen_name,
                derived_from_route=route.path,
                requires_auth=route.auth_required
            ))
            
        # 2. Map APIs to Services
        # Very basic grouping by resource path
        service_map = {}
        for api in self.air.apis:
            resource = api.path.split('/')[1] if len(api.path.split('/')) > 1 else "core"
            if resource not in service_map:
                service_map[resource] = []
            service_map[resource].append(api.id)
            
        for resource, apis in service_map.items():
            plan.services.append(MobileService(
                name=f"{resource.capitalize()}Service",
                methods=[],
                derived_from_apis=apis
            ))
            
        # 3. Security Requirements
        has_critical = any(f.severity == "CRITICAL" for f in self.security_findings)
        if has_critical:
            plan.security_requirements.append("CRITICAL security findings must be resolved before finalizing the Flutter build.")
            
        if self.air.authentication:
            if "cookie" in str(self.air.authentication).lower():
                plan.unsupported_features.append("Cookie-based web authentication")
                plan.manual_actions.append("Implement secure token storage (e.g. Flutter Secure Storage) instead of relying on cookies.")

        return plan
        
    def _route_to_screen_name(self, path: str) -> str:
        if path == "/":
            return "HomeScreen"
        clean = path.strip("/").replace("-", "_").split("/")[0]
        return f"{clean.capitalize()}Screen"
