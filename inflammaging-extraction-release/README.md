# InflammagingKB evidence extraction

This package documents the paper-to-evidence workflow for the InflammagingKB
v1.6 re-extraction. The historical workflow prepared full-text review packets
and used batch-specific curation scripts to register evidence in SQLite.
`extraction_prompt.md` reconstructs the reusable extraction rules from those
artifacts. `extract.py` is a portable implementation of packet preparation and
output validation, independent of the historical ledger and review environment.
`vocabulary.json` preserves the taxonomy paths and relation definitions from the
v1.6 extraction snapshot. It covers the extraction-stage vocabulary.

## Knowledge architecture

`H` is the central concept **INFLAMMAGING**. The six domains describe
contextual roles around it. Within each domain, entities sit under a level-1
and level-2 category. Domain codes are roles, so they do not imply six mandatory
steps in a causal chain.

| Domain | Role | Question |
|---|---|---|
| D1 | Inflammaging drivers | Why |
| D2 | Mechanisms | How |
| D3 | Inflammatory mediators and inter-organ transmission | By what |
| D4 | Target organs and cellular responses | Where |
| D5 | Organ-specific inflammaging phenotypes | What happens |
| D6 | Age-related diseases and outcomes | What outcome |

An evidence edge connects two classified endpoints and records the paper,
sample, comparator, measured attribute and source locator. The example
connects **D1 → Endogenous danger accumulation → Cellular damage products
and debris → Cellular debris** to **D3 → Soluble cytokines → Interleukins →
Circulating IL-6** using `INCREASES`. The validator checks each full path and
tests whether the relation allows the two endpoint domains in that order.

The extraction prompt includes the full v1.6 taxonomy and relation table.
It directs the reviewer from a specific reported result to candidate entities,
contextual roles, full category paths and the final evidence edge. The
input packet includes these instructions and the machine-readable vocabulary.

## Quick start

Requires Python 3.9+ and no third-party packages.

```sh
python3 extract.py prepare examples/paper.json packet.json
python3 extract.py validate packet.json examples/result.json
```

Provide a JSON document with a stable `paper_id` (for example a PMID or DOI)
and a list of passages with unique `locator` and `text` fields. Include the
relevant methods, results, tables, and figure captions to preserve comparators
and endpoint definitions. Give the generated packet to your chosen reviewer or
LLM, save the JSON response, and run the validator on it. The examples are
fictional and let you exercise packet generation and validation offline.
The CLI does not call an LLM or download papers. Validation checks required
fields, full taxonomy paths, relation direction by domain and locator references. Scientific review still
requires checking the claims and relationship direction against the source.

Record the model and version, settings, prompt revision, input hash and manual
changes when using this package for a new extraction. Source articles, supplementary
files, and reviewed evidence records are managed separately.
