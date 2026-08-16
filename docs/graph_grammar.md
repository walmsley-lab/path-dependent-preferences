# Graph Visual Grammar and Exploration Contract (frozen)

*The node editor at `/lab/graph` implements this. Freeze before growth:
the graphs will carry ontology, evidence, causal claims, developmental
dependencies and eventually executable specifications, and a grammar
adopted late is a grammar not adopted.*

## 1. Shape encodes node semantics

| Shape | Meaning |
|---|---|
| rounded rectangle | observed entity or variable |
| dashed rounded rectangle | latent / hypothesized variable |
| circle | learned state or representation |
| hexagon | computation / transformation |
| diamond | comparison / decision |
| square port | interface (input/output boundary) |
| double outline | executable / formally specified component |
| container | subsystem, layer, or developmental phase |

Eight forms, no more. A ninth shape requires retiring one.

## 2. Line style encodes epistemic status

```
⋯⋯⋯  candidate      association or observational support only
┅┅┅  represented    information recoverable above a matched control
━━━  causal         a predicted-direction intervention moved behavior
                    more than its controls
═══  replicated     the causal result held across independent seeds
▬▬▬  authored       privileged ground truth (synthetic worlds only)
```

**Status is derived, never asserted.** `graph_spec.promote()` computes it
from the evidence vector by explicit rules; no hand-set status is
permitted, and a Playwright test fails the build if any edge renders as
causal without a supporting causal evidence entry.

## 3. Labels encode relationship semantics

`assigns · computes · compares · determines · predicts · precedes ·
facilitates · inhibits · represented in · influences · implements`

The same node pair may appear in different graphs with different
relations and even different directions; that is the point.

## 4. Color encodes graph family, never truth

Generator green, observational blue, developmental violet, mechanism
red. Colour never means "verified."

## 5. Layout encodes graph type

Hierarchical (left→right) for generator and mechanism; clustered for
observational; temporal for developmental.

**Positions are authored and stable.** They are stored in the spec and
never recomputed. Changing developmental age changes node and edge
*state* only, so a reader can distinguish "the model changed" from "the
layout algorithm moved things." A behavioral test asserts coordinate
equality across an age change.

## 6. Provenance is mandatory

Every evidence-bearing edge carries a provenance chain (run id →
checkpoint → artifact → commit). No chain, no edge.

## 7. Layout search and experimental search are different problems

*Layout* answers "where do nodes go" and is solved by authored
coordinates here. *Experimental search* answers "which unresolved
relationship deserves the next GPU-hour" and is the scientifically
important one. The frontier ranks unresolved edges by

    value ∝ uncertainty × downstream impact ÷ estimated cost

with uncertainty highest for edges that have representational support
but no causal test. Authored and replicated edges are excluded. The
ranking is advisory: it proposes, humans dispose.

## 8. The page specifies experiments; it does not launch them

"Design experiment" emits a specification — claim, test, required
controls, competence gate, expected evidence record — and says plainly
that compiling it into runnable configuration is Act II work. No
GPU-spending action exists on this surface. Permission tiers (design /
materialize / execute) are recorded in docs/observatory_foundry.md.
