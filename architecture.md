# Intel-RDTech Architecture

## Purpose

Intel-RDTech is an R&D intelligence system for aggregating and prioritizing scientific publications, industry news, regulatory announcements, company updates, and technology signals relevant to pharmaceutical R&D, scientific informatics, laboratory technology, and AI/ML-enabled discovery.

The system separates three questions that should not be collapsed into a single classifier:

1. **What is the scientific work about?** — scientific taxonomy and subject classification.
2. **Does the work matter to the Intel-RDTech intelligence profile?** — semantic relevance and ranking.
3. **What new themes are emerging across the literature?** — unsupervised clustering and trend detection.

## Current Pipeline

The initial implementation normalizes heterogeneous sources into a common record schema. Current sources include journal RSS feeds, FDA announcements, and bioRxiv preprints. PubMed, company sources, page-change monitoring, and additional scientific sources are planned.

```text
Sources
  |
  +-- RSS / Atom
  +-- bioRxiv API
  +-- PubMed [planned]
  +-- Regulatory sources
  +-- Company sources [planned]
  +-- Page monitoring [planned]
  |
  v
Normalized Record
  |
  v
Scientific Classification
  |
  v
Relevance Ranking
  |
  +-- High value
  +-- Relevant / watch
  +-- Background / archive
  |
  v
Trend / Cluster Analysis
  |
  v
Intel Console + Digests
```

## Scientific Intelligence Model Evaluation

The first bioRxiv retrieval demonstrated that deterministic keyword matching can provide useful recall but is not sufficiently precise as the primary semantic classification layer. In particular, the `ai_reliability` topic became a catch-all for papers containing terms such as *benchmark*, *validation*, *prediction*, *robustness*, or *reproducibility*, even when the underlying work was not about AI reliability in the intended R&D intelligence sense.

Three prebuilt approaches are therefore being evaluated for distinct roles: **OpenAlex**, **SPECTER2**, and **BERTopic**.

### Capability Comparison

| Capability                                    | OpenAlex             | SPECTER2             | BERTopic                   |
| --------------------------------------------- | -------------------- | -------------------- | -------------------------- |
| Assign scientific subject                     | **Primary strength** | Possible             | Emergent only              |
| Hierarchical taxonomy                         | **Excellent**        | None inherently      | None inherently            |
| Explain why paper was categorized             | **Strong**           | Moderate/weak        | Moderate                   |
| Match *your* scientific interests             | Moderate             | **Excellent**        | Weak                       |
| Rank 1,700 papers for you                     | Useful               | **Excellent**        | Not primary purpose        |
| Detect unexpected themes                      | Limited              | Moderate             | **Excellent**              |
| Detect emerging trends                        | Limited              | Possible             | **Excellent**              |
| Requires labeled Geno-relevant examples       | No                   | Eventually desirable | No                         |
| Handles a completely new paper                | **Yes**              | **Yes**              | Yes, but context dependent |
| Good replacement for current topic labels     | **Yes**              | Partly               | No                         |
| Good replacement for current relevance filter | Partly               | **Yes**              | No                         |

### Architectural Interpretation

These technologies should not initially be treated as three interchangeable classifiers. They address different layers of the intelligence problem.

#### OpenAlex — Scientific Taxonomy

Primary question:

> What is this scientific work about?

Potential role:

- Replace or substantially reduce hand-maintained topic keywords.
- Assign standardized scientific topics and hierarchical subject metadata.
- Provide interpretable subject classification for newly published work.
- Support broad domain filtering before more expensive semantic ranking.

#### SPECTER2 — Personalized Scientific Relevance

Primary question:

> How similar is this work to science that has previously been judged valuable to Intel-RDTech?

Potential role:

- Generate scientific-document embeddings.
- Compare new papers with positive reference papers.
- Rank papers according to semantic similarity to the intelligence profile.
- Learn a personalized relevance layer without requiring an exhaustive keyword vocabulary.

A curated set of positive and negative examples can become the initial relevance benchmark and, later, training data for a more explicit ranking model.

#### BERTopic — Emerging Theme and Trend Discovery

Primary question:

> What themes are appearing or accelerating across the incoming scientific literature?

Potential role:

- Cluster the relevant literature after classification/ranking.
- Identify topics not represented in the existing watch vocabulary.
- Measure changes in cluster volume over time.
- Surface emerging scientific or technology trends.

BERTopic is therefore considered a downstream intelligence-analysis component rather than the primary record classifier.

## Proposed Classification Architecture

```text
                         ALL SCIENTIFIC RECORDS
                                  |
                                  v
                         OPENALEX TAXONOMY
                     "What science is this?"
                                  |
                                  v
                         BROAD DOMAIN FILTER
                                  |
                                  v
                            SPECTER2
                       "Does it matter?"
                     semantic similarity
                                  |
                 +----------------+----------------+
                 |                |                |
                 v                v                v
              HIGH            RELEVANT           LOW
              VALUE             / WATCH         ARCHIVE
                 |                |
                 +--------+-------+
                          |
                          v
                       BERTopic
                          |
                          v
                   EMERGING CLUSTERS
                          |
                          v
                  "What is changing?"
```

This design deliberately separates **taxonomy**, **relevance**, and **trend detection**. An LLM may later operate on the small set of high-value records to generate summaries such as *what changed*, *why it matters*, and *how it relates to pharmaceutical R&D*. The LLM is not intended to be the first-pass classifier over the complete source corpus.

## Evidence Lifecycle

Scientific records should also be tracked independently by evidence maturity rather than conflating source authority with relevance.

```text
bioRxiv                         Journal / PubMed
PREPRINT                        PEER REVIEWED
   |                                  |
   +-------------> Scientific --------+
                    lifecycle
```

A bioRxiv record and its later peer-reviewed publication should be linked as stages of the same scientific signal when possible, rather than treated as unrelated records or simple duplicates.

Candidate evidence metadata:

- `preprint`
- `peer_reviewed`
- later regulatory or translational evidence where applicable

## Evaluation Strategy

The comparison above describes architectural fit, not measured predictive accuracy. Model selection should be based on a common benchmark derived from real Intel-RDTech records.

Create a manually reviewed gold-standard set of approximately 40–50 papers spanning obvious hits, borderline records, and obvious noise. Suggested relevance labels:

| Label | Meaning |
|---|---|
| 3 | Must surface |
| 2 | Relevant |
| 1 | Peripheral |
| 0 | Noise |

OpenAlex and SPECTER2 can then be evaluated against the same records using measurable criteria such as:

- precision
- recall
- ranking quality
- false-positive behavior
- false-negative behavior
- latency
- compute/API requirements
- explainability

BERTopic should be evaluated separately for cluster coherence and its ability to identify useful emerging themes rather than classification accuracy.

## Design Principle

The intelligence system should optimize for **signal quality**, not maximum collection volume. Source acquisition, scientific taxonomy, personalized relevance, evidence maturity, and emerging-trend detection remain separate dimensions so that improvements to one layer do not distort the others.
