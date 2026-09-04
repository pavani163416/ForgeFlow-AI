import os
import json
import re
from typing import Dict, Any, List, Optional
from app.air.schema import AIR, Route, APIEndpoint, Provenance, Dependency

class DeterministicAnalyzer:
    def __init__(self, source_dir: str, analyzer_version: str = "1.0", source_version: str = "unknown"):
        self.source_dir = source_dir
        self.analyzer_version = analyzer_version
        self.source_version = source_version
        self.framework = "unknown"
        self.language = "unknown"
        self.dependencies: List[Dependency] = []
        self.routes: List[Route] = []
        self.apis: List[APIEndpoint] = []

    def analyze(self) -> AIR:
        """
        Performs static analysis on the source directory and returns a deterministic AIR.
        """
        self._analyze_package_json()
        self._detect_framework()
        self._analyze_routes()
        self._analyze_apis()

        return AIR(
            air_version="1.0",
            analyzer_version=self.analyzer_version,
            source_version=self.source_version,
            framework=self.framework,
            language=self.language,
            dependencies=self.dependencies,
            routes=self.routes,
            apis=self.apis,
            # Other fields left to defaults/empty for initial implementation
        )

    def _analyze_package_json(self):
        pkg_path = os.path.join(self.source_dir, "package.json")
        if not os.path.exists(pkg_path):
            return
        
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
                
            deps = pkg_data.get("dependencies", {})
            dev_deps = pkg_data.get("devDependencies", {})
            
            for name, version in deps.items():
                self.dependencies.append(Dependency(
                    name=name,
                    version=str(version),
                    type="production",
                    provenance=Provenance(
                        confidence="HIGH",
                        source_file="package.json",
                        detection_method="package_json_parser"
                    )
                ))
                
            for name, version in dev_deps.items():
                self.dependencies.append(Dependency(
                    name=name,
                    version=str(version),
                    type="development",
                    provenance=Provenance(
                        confidence="HIGH",
                        source_file="package.json",
                        detection_method="package_json_parser"
                    )
                ))
        except Exception:
            pass # Failsafe against parsing errors

    def _detect_framework(self):
        # Very basic framework detection from dependencies
        dep_names = {d.name for d in self.dependencies}
        
        is_react = "react" in dep_names or "next" in dep_names
        is_express = "express" in dep_names
        
        if is_react and is_express:
            self.framework = "React+Express"
        elif is_react:
            self.framework = "React"
        elif is_express:
            self.framework = "Express"
            
        if "typescript" in dep_names:
            self.language = "TypeScript"
        else:
            # Fallback heuristic
            has_ts = False
            for root, _, files in os.walk(self.source_dir):
                if any(f.endswith(".ts") or f.endswith(".tsx") for f in files):
                    has_ts = True
                    break
            self.language = "TypeScript" if has_ts else "JavaScript"

    def _analyze_routes(self):
        # Basic deterministic route extraction (e.g. Next.js app router or express routes)
        # For this foundation, we implement a stub that simulates finding a route 
        # based on simple regexes on typical React files.
        for root, _, files in os.walk(self.source_dir):
            # Skip node_modules deterministically
            if "node_modules" in root:
                continue
                
            for file in files:
                if file.endswith((".jsx", ".tsx")):
                    file_path = os.path.join(root, file)
                    # This is highly simplified for the foundation step
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            if "Route" in content and "path=" in content:
                                paths = re.findall(r'path=["\']([^"\']+)["\']', content)
                                for path in paths:
                                    # Ensure determinism by checking if it exists
                                    if not any(r.path == path for r in self.routes):
                                        self.routes.append(Route(
                                            path=path,
                                            component_id=file,
                                            provenance=Provenance(
                                                confidence="MEDIUM",
                                                source_file=file_path.replace(self.source_dir, "").lstrip("/\\"),
                                                detection_method="regex_route_scanner"
                                            )
                                        ))
                    except Exception:
                        pass
        # Sort routes to guarantee deterministic order
        self.routes.sort(key=lambda x: x.path)

    def _analyze_apis(self):
        # Basic Express / Axios API extraction stub
        for root, _, files in os.walk(self.source_dir):
            if "node_modules" in root:
                continue
                
            for file in files:
                if file.endswith((".js", ".ts")):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            # Match app.get('/api/users', ...)
                            endpoints = re.findall(r'(app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content)
                            for _, method, path in endpoints:
                                api_id = f"{method.upper()}_{path}"
                                if not any(a.id == api_id for a in self.apis):
                                    self.apis.append(APIEndpoint(
                                        id=api_id,
                                        method=method.upper(),
                                        path=path,
                                        provenance=Provenance(
                                            confidence="HIGH",
                                            source_file=file_path.replace(self.source_dir, "").lstrip("/\\"),
                                            detection_method="regex_express_scanner"
                                        )
                                    ))
                    except Exception:
                        pass
        # Sort apis to guarantee deterministic order
        self.apis.sort(key=lambda x: x.id)
