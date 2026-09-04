# ForgeFlow AI - Test Environment Setup

This document explains how to bootstrap the ForgeFlow AI test environment from a clean checkout to verify the Phase 2 Security Integration.

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (Required for PostgreSQL RLS testing)

## 1. Checkout & Virtual Environment
```bash
git clone <repository_url> forgeflow-ai
cd forgeflow-ai/backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## 3. Start Test Database
The database integration tests require an active PostgreSQL instance. We provide a `docker-compose.test.yml` for this purpose.

```bash
cd ..  # Back to root directory
docker-compose -f docker-compose.test.yml up -d
```
*Wait ~10 seconds for PostgreSQL to initialize.*

## 4. Run Tests
The test suite is built with `pytest` and automatically handles SQL migrations and schema initialization via `backend/tests/conftest.py`.

```bash
cd backend
python -m pytest tests/ -v
```

### Expected Output
If the database is running successfully, you will see output like:
```text
tests/test_auth.py ...                                                   [OK]
tests/test_authz.py ...                                                  [OK]
tests/test_idor.py ...                                                   [OK]
tests/test_rls.py ...                                                    [OK]
tests/test_upload_security.py ...                                        [OK]
tests/test_state_machine.py ...                                          [OK]
tests/test_worker.py ...                                                 [OK]
```

### Note on Database Tests
If `docker-compose` is unavailable on your machine, `test_rls.py` and other database-dependent tests will automatically **SKIP** rather than fail, but you will not be able to verify RLS tenant isolation locally. In this case, rely on the GitHub Actions CI pipeline which runs the exact same test suite inside a provisioned service container.
