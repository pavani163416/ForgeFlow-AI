import pytest
import os
import tempfile
from app.analysis.analyzer import DeterministicAnalyzer

@pytest.fixture
def mock_source_dir():
    with tempfile.TemporaryDirectory() as d:
        # Create a mock package.json
        with open(os.path.join(d, "package.json"), "w") as f:
            f.write('{"dependencies": {"react": "^18.0.0", "express": "^4.0.0"}}')
        
        # Create a mock React route
        os.makedirs(os.path.join(d, "src"))
        with open(os.path.join(d, "src", "App.tsx"), "w") as f:
            f.write('<Route path="/dashboard" component={Dashboard} />')
            
        # Create a mock API
        with open(os.path.join(d, "server.js"), "w") as f:
            f.write("app.get('/api/users', (req, res) => {})")
            
        yield d

def test_deterministic_analyzer(mock_source_dir):
    analyzer = DeterministicAnalyzer(mock_source_dir)
    air = analyzer.analyze()
    
    assert air.framework == "React+Express"
    assert air.language == "TypeScript"
    
    assert len(air.dependencies) == 2
    assert any(d.name == "react" for d in air.dependencies)
    
    assert len(air.routes) == 1
    assert air.routes[0].path == "/dashboard"
    assert air.routes[0].provenance.confidence == "MEDIUM"
    
    assert len(air.apis) == 1
    assert air.apis[0].id == "GET_/api/users"
    assert air.apis[0].provenance.confidence == "HIGH"
