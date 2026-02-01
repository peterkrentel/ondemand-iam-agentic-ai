# Spec Policy (How We Use Specs)

**Purpose**: Lightweight guide for when and how to create specs.

**Status**: Active
**Last Updated**: 2026-02-01

---

## What Specs Are

Specs capture "what must be true." They are lightweight, explicit, and enforceable.

**Not specs**: Documentation, implementation details, aspirational goals
**Are specs**: Normative contracts, cross-boundary agreements, invariants

---

## When to Add or Update a Spec

**Add a spec when:**
- Cross-boundary contracts exist (API, events, schemas, configs)
- Multiple things depend on behavior (SDK + API, frontend + backend)
- Changes would break customers (public API, published SDK)
- Ambiguity caused a bug (two people interpreted behavior differently)

**Update a spec when:**
- Changing observable behavior (bug fix, feature, edge case)
- Adding/removing fields from contracts
- A bug reveals the spec was unclear

**DON'T spec when:**
- Still exploring (experimentation is allowed)
- Implementation details that don't affect contracts
- Behavior that's not relied upon yet

**Rule**: Exploration is allowed. Once behavior is relied upon, it must be specified.

---

## What Every Spec MUST Include

Keep it minimal. Every spec needs:

1. **Header** - Status, why this exists, where it's enforced
2. **Normative rules** - MUST / MUST NOT statements
3. **Examples** - Valid (EC-1, EC-2, ...) and invalid cases
4. **Validation** - Where enforced, what happens on violation

**That's it.** Don't add more unless you need it.

---

## Drift Rule

**Spec and implementation must not diverge.**

If they disagree:
1. Determine which is correct
2. Update the incorrect one
3. Do both in the same PR/commit

**Never:** Update code without updating spec, or vice versa.

---

## Compatibility Rules

**Backward-compatible** (allowed):
- Adding optional fields
- Adding new enum values
- Relaxing constraints

**Breaking** (requires version bump):
- Removing required fields
- Changing field types
- Removing enum values
- Changing semantics

---

## Enforcement

**Rule**: If a spec can't be enforced, it's documentation, not a spec.

Every spec MUST have validation:
- Unit tests (field validation, type checking)
- Contract tests (cross-boundary agreements)
- Integration tests (system invariants)
- CI checks (schema validation, drift detection)
- Runtime checks (production guardrails)

---

## Example: Good vs Bad Spec

**Good Spec** ✅
- Normative (MUST/MUST NOT)
- Concrete examples (EC-1, EC-2, ...)
- Enforced by tests
- Updated when behavior changes

**Bad Spec** ❌
- Vague ("should be fast")
- No examples
- No validation
- Out of sync with code

---

## Related Documents

- **[specs/README.md](README.md)** - Spec index and philosophy
- **[specs/event-schema.md](event-schema.md)** - Example of a good spec
- **[docs/CONTRACT_TESTING.md](../docs/CONTRACT_TESTING.md)** - How specs are validated

---

**This policy is itself a spec. If it's unclear or wrong, update it.**

