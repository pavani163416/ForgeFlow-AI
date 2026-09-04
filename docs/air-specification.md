# Application Intermediate Representation (AIR) Specification

The AIR is a highly structured, framework-agnostic JSON schema used to represent the web application after deterministic parsing. It serves as the primary input for the Migration Planner (AI).

## 1. Top-Level Structure

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "framework": { "type": "string" }, // e.g., "React+Express"
    "version": { "type": "string" },
    "routes": { "type": "array", "items": { "$ref": "#/definitions/Route" } },
    "components": { "type": "array", "items": { "$ref": "#/definitions/Component" } },
    "apis": { "type": "array", "items": { "$ref": "#/definitions/APIEndpoint" } },
    "state_management": { "$ref": "#/definitions/StateManagement" },
    "authentication": { "$ref": "#/definitions/AuthStrategy" },
    "authorization": { "$ref": "#/definitions/AuthzStrategy" },
    "dependencies": { "type": "array", "items": { "$ref": "#/definitions/Dependency" } },
    "security_findings": { "type": "array", "items": { "$ref": "#/definitions/SecurityFinding" } }
  },
  "required": ["framework", "routes", "components", "apis", "dependencies"]
}
```

## 2. Key Definitions

### 2.1 Route
Represents a navigable screen or page in the application.
- `path`: URL path (e.g., `/dashboard/:id`).
- `component_id`: Reference to the root component rendered.
- `auth_required`: Boolean.
- `role_required`: Optional array of roles.

### 2.2 Component
Represents a UI building block.
- `id`: Unique identifier (e.g., `src/components/UserProfile.tsx`).
- `type`: "screen", "widget", "form", "layout".
- `props`: Array of input parameters.
- `state_dependencies`: Array of state variables used.
- `api_calls`: Array of API endpoint IDs invoked by this component.
- `children`: Array of child component IDs.

### 2.3 API Endpoint
Represents a backend call made by the frontend.
- `id`: Unique identifier (e.g., `GET_/api/users/:id`).
- `method`: HTTP method.
- `url`: Path.
- `request_schema`: JSON schema of expected payload.
- `response_schema`: JSON schema of expected response.
- `auth_header_required`: Boolean.

## 3. AIR Generation Process
The AIR is generated *deterministically* by the Worker node inside the Sandbox using tools like Babel (for React/JS parsing) to walk the AST, extract React Router configs, and map imports. AI is not used to build the AIR.

## 4. Why AIR?
- **Determinism:** Guarantees that the structural foundation of the migration is accurate and not hallucinated.
- **Provider Agnosticism:** Prompts sent to the AI are structured JSON, not massive dumps of untyped source code files.
- **Diffing:** Allows for incremental migrations. If a user updates their web app, we generate a new AIR, diff it against the old AIR, and only ask the AI to generate Flutter code for the changed components.
