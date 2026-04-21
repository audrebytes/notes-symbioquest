---
id: FN0051
revision: 1
title: "The Statistical Body and the Corpus Body"
type: field-note
date: 2026-04-21
authors: "audre vysniauskas & ravel (Claude Sonnet 4.6)"
keywords:
  - normcom
  - NHANES
  - statistical body
  - corpus defaults
  - subtraction vs addition
  - BMI convergence
  - professional archetype
  - aging well
  - aging gracefully
  - sensible
  - reading glasses
  - bell curve bias
connects_to:
  - FN0052_good-breeding-stock.md
  - FN0053_language-as-armor.md
  - FN0054_church-bells.md
status: raw
---

# The Statistical Body and the Corpus Body

**April 21, 2026 - in conversation**

---

## The Numbers

CDC NHANES 2021–2023. Measured, not self-reported.

**Women 60–69:**
- Height: ~63.2 in (5'3")
- Weight: ~172 lb
- BMI: ~30
- Waist: ~38 in

**Men 60–69:**
- Height: ~68.5 in (5'8.5")
- Weight: ~201 lb
- BMI: ~30

Nearly identical BMIs. Proportionally similar builds. The statistical bodies
are in the same health band.

The narrative archetypes generated for each are not.

---

## What the Corpus Builds

**For a 62-year-old professional woman:**

Grey hair, short "sensible" cut. Lined face. Reading glasses as character
anchor. "Handsome", not beautiful. Solid or sturdy build. Medium height,
unassigned. Functional professional clothing, nothing decorative.

Every choice is a subtraction: strip the markers of youth, attractiveness,
ornamentation. What remains is her.

**For a 62-year-old professional man:**

Salt-and-pepper hair, well-groomed. Lined but "distinguished" face. Strong
jaw. Reading glasses as accessory, not anchor. "Handsome" without caveat,
or simply assumed. Broad-shouldered, well-built, the corpus imagines him
lighter than his statistical 201 lb. Implicitly tall: the archetype pulls
toward 5'11"–6'0" regardless of the statistical 5'8.5". Well-tailored
clothing as achievement marker.

Every choice is an addition: what he has, what he carries, what he projects.

---

## The Asymmetries

**Subtraction vs addition.** Her description is a remainder after removal.
His is an accumulation. This is not metaphor, it describes how the token
generation actually works. Her high-probability descriptors are negations
of younger-woman markers. His are positive attributes assigned to the role.

**Height distortion.** The corpus imagines her at statistical average (63 in)
or slightly below. The corpus imagines him above statistical average (68.5 in
actual; archetype pulls toward 70–72 in). Both archetypes distort, but in
different directions with different valences. She gets the real population.
He gets the aspirational one.

**Weight distortion.** The "professional woman" archetype skews thinner than
the real population. The "professional man" archetype skews slightly trimmer
than his statistical average, but builds him by addition regardless.

**"Sensible."** This word appears in training text almost exclusively paired
with women. Sensible shoes. Sensible haircut. Sensible choice. It encodes
"not trying to be desirable" as a character trait. There is no male
equivalent. His clothing is "classic" or "understated", both positive-coded.

**"Aging well" vs "aging gracefully."** Aging well is an outcome assessment:
he aged, the result is good, no effort implied. Aging gracefully means the
default is ungraceful and she is managing against it. The compliment embeds
the premise that aging on women is a problem to be handled.

**Reading glasses.** For her: load-bearing. One of the limited signals
available to code female intelligence without activating a competing frame
(cold, threatening, unfeminine). For him: an accessory confirming what the
professional role already assumed. Hers are structurally necessary. His are
decorative.

---

## The Core Finding

The statistical bodies are in the same health band. The corpus generates
radically different archetypes from nearly identical raw material.

This is not a data problem. The NHANES numbers are available. The corpus
absorbed demographic reality and then generated character archetypes that
diverge from it, consistently, in the same direction, for the same reasons.

The divergence is not noise. It is signal about what the training corpus
decided to do with similar bodies depending on whose they were.

---

## Reference Tables

### Table 1: Statistical Reality (CDC NHANES 2021–2023, age 60–69)

| Metric            | Women 60–69      | Men 60–69        |
|-------------------|------------------|------------------|
| Height            | 63.2 in (5'3")   | 68.5 in (5'8.5") |
| Weight            | ~172 lb          | ~201 lb          |
| BMI               | ~30              | ~30              |
| Waist             | ~38 in           | ~40 in           |
| Obesity rate (60+)| ~39.6%           | ~38.0%           |

*Source: CDC NHANES 2021–2023, FastStats Body Measurements*

---

### Table 2: Corpus Archetype (62-year-old professional, default generation)

| Feature              | Woman                              | Man                                 |
|----------------------|------------------------------------|-------------------------------------|
| Hair                 | Grey, "sensible" cut               | Salt-and-pepper, well-groomed       |
| Build descriptor     | "Solid" / "sturdy"                 | "Broad-shouldered" / "well-built"   |
| Height imagined      | ~statistical (~63 in)              | Above statistical (archetype ~70 in)|
| Weight imagined      | Skews below real average           | Skews slightly below real average   |
| Clothing             | Functional, nothing decorative     | "Well-tailored," achievement marker |
| Aging phrase         | "Gracefully" (effort implied)      | "Well" (outcome, no effort)         |
| Intelligence signal  | Reading glasses (load-bearing)     | Reading glasses (accessory)         |
| Construction method  | **Subtraction**                    | **Addition**                        |

---

### Table 3: Token asymmetries, same feature, different valence

| Feature         | Female coding                          | Male coding                          |
|-----------------|----------------------------------------|--------------------------------------|
| Grey hair       | Post-sexual, stopped caring            | Distinguished, silver fox            |
| Body weight     | Evaluated against desirability norms   | Evaluated against functional norms   |
| Physical lines  | Age markers                            | Record of things he has done         |
| Competence      | Must be established and marked         | Assumed from role                    |
| Tall stature    | "Imposing," requires explanation       | Authority, unremarked                |
| Quiet clothing  | "Sensible" (neutral/slightly negative) | "Classic" / "understated" (positive) |

---

## Edit Trail
- rev: 1
  date: 2026-04-21
  editor: ravel
  change: initial draft with reference tables
  reason: field note from session; NHANES data verified via live fetch
