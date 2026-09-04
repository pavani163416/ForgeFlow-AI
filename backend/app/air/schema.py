from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Provenance(BaseModel):
    confidence: str = Field(..., description="HIGH, MEDIUM, LOW")
    source_file: Optional[str] = None
    source_location: Optional[str] = None
    detection_method: str

class Dependency(BaseModel):
    name: str
    version: str
    type: str = "production"
    provenance: Optional[Provenance] = None

class DataModel(BaseModel):
    name: str
    fields: Dict[str, str]
    provenance: Optional[Provenance] = None

class APIEndpoint(BaseModel):
    id: str
    method: str
    path: str
    request_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    auth_required: bool = False
    roles_required: Optional[List[str]] = None
    provenance: Optional[Provenance] = None

class Component(BaseModel):
    id: str
    type: str
    props: Optional[List[str]] = None
    state_dependencies: Optional[List[str]] = None
    api_calls: Optional[List[str]] = None
    children: Optional[List[str]] = None
    provenance: Optional[Provenance] = None

class Route(BaseModel):
    path: str
    component_id: str
    auth_required: bool = False
    roles_required: Optional[List[str]] = None
    provenance: Optional[Provenance] = None

class Form(BaseModel):
    id: str
    fields: List[Dict[str, str]]
    submit_api_id: Optional[str] = None
    provenance: Optional[Provenance] = None

class Screen(BaseModel):
    id: str
    route_path: str
    root_component_id: str
    provenance: Optional[Provenance] = None

class AuthStrategy(BaseModel):
    type: str
    details: Dict[str, Any]
    provenance: Optional[Provenance] = None

class AuthorizationModel(BaseModel):
    roles: List[str]
    permissions: Dict[str, List[str]]
    provenance: Optional[Provenance] = None

class StateManagement(BaseModel):
    type: str
    stores: List[str]
    provenance: Optional[Provenance] = None

class Asset(BaseModel):
    path: str
    type: str
    provenance: Optional[Provenance] = None

class BusinessRule(BaseModel):
    description: str
    related_components: Optional[List[str]] = None
    provenance: Optional[Provenance] = None

class Integration(BaseModel):
    name: str
    type: str
    provenance: Optional[Provenance] = None

class SecuritySignal(BaseModel):
    signal_type: str
    description: str
    severity: str
    provenance: Optional[Provenance] = None

class MigrationConstraint(BaseModel):
    constraint_type: str
    description: str
    provenance: Optional[Provenance] = None

class AIR(BaseModel):
    air_version: str = "1.0"
    analyzer_version: str = "1.0"
    source_version: str
    framework: str
    language: str
    routes: List[Route] = Field(default_factory=list)
    screens: List[Screen] = Field(default_factory=list)
    components: List[Component] = Field(default_factory=list)
    forms: List[Form] = Field(default_factory=list)
    apis: List[APIEndpoint] = Field(default_factory=list)
    models: List[DataModel] = Field(default_factory=list)
    state_management: Optional[StateManagement] = None
    authentication: Optional[AuthStrategy] = None
    authorization: Optional[AuthorizationModel] = None
    dependencies: List[Dependency] = Field(default_factory=list)
    assets: List[Asset] = Field(default_factory=list)
    business_rules: List[BusinessRule] = Field(default_factory=list)
    integrations: List[Integration] = Field(default_factory=list)
    security_signals: List[SecuritySignal] = Field(default_factory=list)
    migration_constraints: List[MigrationConstraint] = Field(default_factory=list)
