# 📋 Spec-Driven Development & Contract Testing

## Overview

AIMgentix follows a **spec-driven development** approach where contracts (schemas, types, enums) are the source of truth for the API and SDK. All code changes must maintain contract compatibility.

## Contract Layers

### 1. **Pydantic Models (Backend)**
Located in: `backend/app/models.py`

- **AuditEvent**: Core event schema with strict typing
- **ActorType**: Enum defining agent/human/system actors
- **ActionType**: Enum defining action types (tool_call, http_request, etc.)
- **EventStatus**: Enum defining status values (success, error, pending)
- **AuditEventResponse**: Response model for event queries

These models serve as:
- Request/response validation contracts
- OpenAPI schema generation source
- Database schema contracts

### 2. **SDK Models**
Located in: `sdk/aimgentix/events.py`

- **AuditEvent**: Dataclass matching backend schema
- **ActorType, ActionType, EventStatus**: Enums matching backend exactly

The SDK models **must** maintain 100% compatibility with backend models to ensure seamless integration.

### 3. **OpenAPI Schema**
Auto-generated from FastAPI at: `/openapi.json`

- Provides machine-readable API contract
- Generated from Pydantic models
- Validated in contract tests

---

## Contract Testing Strategy

### Backend Contract Tests
**File**: `backend/tests/test_contracts.py`

Tests validate:
1. ✅ **OpenAPI Schema Generation**
   - Schema exists and is valid OpenAPI 3.x
   - All required endpoints are documented
   - Schema completeness (all fields present)
   - Enum definitions match code

2. ✅ **Enum Exhaustiveness**
   - All enum values are accepted by API
   - Invalid enum values are rejected (422)
   - All enums have expected counts

3. ✅ **Pydantic Validation**
   - Required fields are enforced
   - Optional fields can be null/omitted
   - Type validation works correctly
   - Metadata must be a dictionary

4. ✅ **Schema Consistency**
   - Enum counts remain stable
   - Model serialization works correctly
   - Response models validate properly

### SDK Contract Tests
**File**: `sdk/tests/test_contracts.py`

Tests validate:
1. ✅ **Enum Consistency**
   - SDK enum values match backend exactly
   - All expected enum values present
   - Enum counts match backend

2. ✅ **Data Model Contract**
   - Required fields present and correct
   - Auto-generated fields work (event_id, timestamp)
   - Optional fields work correctly
   - Default values correct (metadata = {})

3. ✅ **Serialization**
   - to_dict() produces correct structure
   - Enums converted to strings
   - Timestamps in ISO8601 format
   - JSON serializable output

4. ✅ **Data Integrity**
   - Event IDs are unique
   - Timestamps are UTC
   - Metadata dicts not shared between instances

---

## CI/CD Integration

### Build and Test Workflow
**File**: `.github/workflows/build-test.yml`

Contract validation runs on every PR and push:

```yaml
contract-validation:
  - Run backend contract tests
  - Run SDK contract tests
  - Enforce with pytest (no continue-on-error)
```

### What Gets Validated

1. **On Every PR/Push**:
   - Backend contract tests (17 tests)
   - SDK contract tests (19 tests)
   - OpenAPI schema validation
   - Enum exhaustiveness
   - Type validation

2. **Flake8 Linting**:
   - Critical errors (E9, F63, F7, F82) **block** the build
   - Code quality issues are warnings only

3. **Integration Tests**:
   - Health endpoint checks
   - OpenAPI docs accessibility
   - Event creation and retrieval

---

## Contract Change Process

### Adding a New Enum Value

**Example**: Adding a new `ActionType`

1. **Update Backend Enum** (`backend/app/models.py`):
   ```python
   class ActionType(str, Enum):
       # ... existing values
       NEW_ACTION = "new_action"  # Add new value
   ```

2. **Update SDK Enum** (`sdk/aimgentix/events.py`):
   ```python
   class ActionType(str, Enum):
       # ... existing values
       NEW_ACTION = "new_action"  # Must match exactly
   ```

3. **Update Tests**:
   - Backend: Enum count assertion in `test_enum_count_consistency`
   - SDK: Enum count assertion in `test_enum_counts`
   - Add test cases if needed

4. **Update Documentation**:
   - `docs/API_SPEC.md`: Add to ActionType enum list
   - Update OpenAPI descriptions if needed

5. **Verify**:
   ```bash
   # Backend
   cd backend
   pytest tests/test_contracts.py -v
   
   # SDK
   cd sdk
   pytest tests/test_contracts.py -v
   ```

### Adding a New Required Field

**Example**: Adding `session_id` to `AuditEvent`

1. **Update Backend Model** (`backend/app/models.py`):
   ```python
   class AuditEvent(BaseModel):
       # ... existing fields
       session_id: str = Field(..., description="Session identifier")
   ```

2. **Update SDK Model** (`sdk/aimgentix/events.py`):
   ```python
   @dataclass
   class AuditEvent:
       # ... existing fields
       session_id: str
   ```

3. **Update Database** (`backend/app/db.py`):
   - Add column to `AuditEventDB`
   - Create migration if needed

4. **Update Tests**:
   - Add `session_id` to test fixtures
   - Update required fields assertions
   - Add specific tests for new field

5. **Update Documentation**:
   - `docs/API_SPEC.md`: Add to request body fields
   - Update examples with new field

⚠️ **Breaking Change**: Adding required fields breaks backward compatibility!

### Adding an Optional Field

**Example**: Adding `error_message` to `AuditEvent`

1. **Update Backend Model**:
   ```python
   error_message: Optional[str] = Field(None, description="Error message if status is error")
   ```

2. **Update SDK Model**:
   ```python
   error_message: Optional[str] = None
   ```

3. **Update Tests**:
   - Verify field is optional in `test_optional_fields_allowed_null`
   - Add test for when field is present

4. **Update Documentation**:
   - Mark as optional in API docs

✅ **Non-Breaking**: Optional fields are backward compatible!

---

## Schema Validation Tools

### Manual Validation

```bash
# Validate OpenAPI schema
curl http://localhost:8000/openapi.json | jq '.'

# Validate backend contracts
cd backend
pytest tests/test_contracts.py -v

# Validate SDK contracts
cd sdk
pytest tests/test_contracts.py -v

# Run all tests
cd backend && pytest -v && cd ../sdk && pytest -v
```

### Automated Validation

Contracts are validated automatically in CI/CD on:
- Every pull request
- Every push to main/develop
- Manual workflow dispatch

---

## Best Practices

### ✅ DO

1. **Always update both backend and SDK** when changing contracts
2. **Run contract tests locally** before pushing
3. **Update documentation** when changing public APIs
4. **Use semantic versioning** for breaking changes
5. **Add tests for new enum values** or fields
6. **Validate OpenAPI schema** after model changes

### ❌ DON'T

1. **Don't change enum values** without version bump
2. **Don't add required fields** without migration strategy
3. **Don't remove fields** without deprecation period
4. **Don't skip contract tests** (they're fast!)
5. **Don't use `continue-on-error`** for contract tests in CI
6. **Don't bypass Pydantic validation** with `model_construct()`

---

## Contract Test Coverage

### Current Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| Backend Contracts | 17 | 100% |
| SDK Contracts | 19 | 100% |
| OpenAPI Schema | 4 | 100% |
| Enum Exhaustiveness | 9 | 100% |
| Pydantic Validation | 4 | 100% |

### What's Tested

- ✅ Schema generation and validation
- ✅ All enum values accepted
- ✅ Invalid values rejected
- ✅ Required/optional fields
- ✅ Type validation
- ✅ Serialization correctness
- ✅ Timestamp UTC enforcement
- ✅ UUID uniqueness
- ✅ Metadata isolation

### What's NOT Tested (Future)

- ⏳ Cross-version compatibility
- ⏳ Schema migration testing
- ⏳ Performance under load
- ⏳ Concurrent request validation

---

## Troubleshooting

### Contract Test Failures

**Problem**: Backend tests fail with enum mismatch
```
AssertionError: Expected 3 but got 4
```
**Solution**: Update enum count in `test_enum_count_consistency`

---

**Problem**: SDK tests fail with serialization error
```
KeyError: 'new_field'
```
**Solution**: Add new field to SDK dataclass and to_dict() method

---

**Problem**: OpenAPI schema missing endpoint
```
AssertionError: '/v1/new-endpoint' not in paths
```
**Solution**: Ensure FastAPI route is decorated and app is imported correctly

---

## Version History

### v1.0 (Current)
- Initial contract testing framework
- Backend contract tests (17 tests)
- SDK contract tests (19 tests)
- OpenAPI validation
- CI/CD integration

### Future Enhancements
- Cross-version compatibility testing
- Schema migration validation
- Performance contract testing
- Contract documentation generation

---

## Resources

- **Pydantic Documentation**: https://docs.pydantic.dev/
- **FastAPI OpenAPI**: https://fastapi.tiangolo.com/tutorial/metadata/
- **JSON Schema**: https://json-schema.org/
- **API Design Guidelines**: https://github.com/microsoft/api-guidelines

---

**Maintained by**: Peter Krentel  
**Last Updated**: 2026-01-31  
**Status**: ✅ Active and Enforced
