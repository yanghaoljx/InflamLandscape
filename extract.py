"""Prepare evidence review packets and validate structured extraction output."""
import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
FIELDS = (
    "paper_id", "source", "source_D", "relation", "target", "target_D",
    "species", "sample", "condition", "comparator", "target_attribute",
    "evidence_type", "claim_status", "evidence_span", "source_locator",
)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(source):
    raw = source.read_bytes()
    paper = json.loads(raw)
    paper_id = paper.get("paper_id")
    passages = paper.get("passages")
    if not isinstance(paper_id, str) or not paper_id.strip() or not passages:
        raise ValueError("Supply a paper_id and at least one passage.")
    locators = set()
    for passage in passages:
        locator = passage["locator"]
        if not isinstance(locator, str) or not locator.strip() or locator in locators:
            raise ValueError("Passage locators must be nonempty and unique.")
        if not isinstance(passage["text"], str) or not passage["text"].strip():
            raise ValueError("Passage text must be nonempty.")
        locators.add(locator)
    return {
        "instructions": (BASE / "extraction_prompt.md").read_text(encoding="utf-8"),
        "vocabulary": read_json(BASE / "vocabulary.json"),
        "paper": paper,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
    }


def expand_domains(expression):
    domains = set()
    for part in expression.split("/"):
        if "–" in part:
            first, last = part.split("–")
            domains.update(f"D{number}" for number in range(int(first[1:]), int(last[1:]) + 1))
        else:
            domains.add(part)
    return domains


def validate(packet, result):
    paper = packet["paper"]
    locators = {p["locator"] for p in paper["passages"]}
    taxonomy = {(row[0], row[4], row[5]) for row in packet["vocabulary"]["taxonomy"]}
    relations = {
        name: (expand_domains(source), expand_domains(target))
        for name, source, target, _ in packet["vocabulary"]["relations"]
    }
    edges = result.get("edges")
    if not isinstance(edges, list):
        raise ValueError("The result must contain an edges array.")
    for index, edge in enumerate(edges, start=1):
        for key in FIELDS:
            if not isinstance(edge.get(key), str) or not edge[key].strip():
                raise ValueError(f"Edge {index}: missing or invalid {key}.")
        if edge["paper_id"] != paper["paper_id"] or edge["source_locator"] not in locators:
            raise ValueError(f"Edge {index}: paper ID or locator is not in the packet.")
        if edge["relation"] not in relations:
            raise ValueError(f"Edge {index}: unknown relation.")
        for endpoint, domains in zip(("source", "target"), relations[edge["relation"]]):
            domain = edge[f"{endpoint}_D"]
            if domain not in domains:
                raise ValueError(f"Edge {index}: relation does not allow {endpoint} domain {domain}.")
            level1 = edge[f"{endpoint}_level1"]
            level2 = edge[f"{endpoint}_level2"]
            if domain == "H":
                if edge[endpoint] != "INFLAMMAGING" or level1 is not None or level2 is not None:
                    raise ValueError(f"Edge {index}: H must be the central concept INFLAMMAGING.")
            elif (domain, level1, level2) not in taxonomy:
                raise ValueError(f"Edge {index}: unknown {endpoint} taxonomy path.")
    return len(edges)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("source", type=Path)
    prep.add_argument("packet", type=Path)
    check = commands.add_parser("validate")
    check.add_argument("packet", type=Path)
    check.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            packet = prepare(args.source)
            with args.packet.open("x", encoding="utf-8") as output:
                json.dump(packet, output, ensure_ascii=False, indent=2)
                output.write("\n")
        else:
            count = validate(read_json(args.packet), read_json(args.result))
            print(f"Validated {count} structured edge(s).")
    except (AttributeError, KeyError, TypeError, ValueError, OSError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
