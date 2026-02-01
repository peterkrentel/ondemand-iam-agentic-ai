# AIMgentix Specifications

**Intent**: Specs describe "what should be true" about AIMgentix's behavior.

**Principle**: No behavior change should exist only in code. Decisions must be recorded in specs.

---

## 📁 Current Specs

### **[event-schema.md](event-schema.md)** ✅

**Why it exists**: Event schema crosses SDK/API/DB boundaries. Changes break all clients.

**Status**: Active
**Validation**: Pydantic models + contract tests (see `docs/CONTRACT_TESTING.md`)

---

## 🎯 When to Add a New Spec

Ask: **"Have we been bitten here yet?"**

- ✅ **Yes** → Write a spec
- ❌ **No** → Leave it implicit for now

**Examples of "being bitten":**

- Frontend/backend disagree on API contract
- Someone asks "what does this return?"
- An agent guesses wrong about behavior
- A bug reveals ambiguity
- Multiple implementations drift

---

## 📝 Spec Template

When you need to create a new spec:

```markdown
# [Component] Specification

**Status**: Draft | Active | Deprecated
**Last Updated**: YYYY-MM-DD
**Why This Exists**: [What pain does it prevent?]
**Validation**: [How is it enforced?]

## Intent

What problem does this solve?

## Guarantees

What MUST be true?

## Examples

Concrete examples of correct behavior

## Validation

How is this spec enforced? (Tests, CI, runtime checks)

## When to Update This Spec

When should this be revised?
```

---

## 🔄 Spec Evolution Process

1. **Exploration** - No spec required, experiment freely
2. **Decision** - Once behavior is relied upon, document it
3. **Enforcement** - Add validation (tests, CI, runtime checks)
4. **Refinement** - Update spec as requirements change

---

## ✅ Success Criteria

Specs are working when:

1. ✅ A new contributor can understand intent by reading specs
2. ✅ Any AI agent can implement features from specs alone
3. ✅ Spec violations fail loudly (tests, CI, runtime)
4. ✅ No "tribal knowledge" - everything is documented

---

## 📚 Related Documentation

- **[ARCHITECTURE.md](../docs/ARCHITECTURE.md)** - Describes "how" the system works
- **[OPERATIONS.md](../docs/OPERATIONS.md)** - Describes "where" to deploy
- **[CONTRACT_TESTING.md](../docs/CONTRACT_TESTING.md)** - Describes how specs are validated
- **Specs** - Define "what must be true"

**Key Difference**: Docs describe, specs define contracts.

---

**This is an incremental shift, not a rewrite. Apply pragmatically.**

