#!/usr/bin/env python3
"""Knowledge graph CLI for the H4YF project.

Usage:
  kg.py summary               Print CONTEXT.md content (pipe to file to save)
  kg.py add-node TYPE NAME [DESC]   Add a node
  kg.py add-edge SRC REL TGT [NOTE] Add a directed edge (accepts 8-char ID prefix)
  kg.py list [TYPE]           List nodes, optionally filtered by type
  kg.py query TERM            Search nodes by name or description
"""

import json
import sys
import os
import uuid
from datetime import datetime, timezone

GRAPH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'knowledge-graph.json')

VALID_TYPES = ['Decision', 'Component', 'Feature', 'Entity', 'Concept']
VALID_RELS = ['depends_on', 'implements', 'supersedes', 'relates_to', 'part_of', 'created_by']


def load_graph():
    with open(GRAPH_PATH) as f:
        return json.load(f)


def save_graph(graph):
    graph['metadata']['last_updated'] = datetime.now(timezone.utc).date().isoformat()
    with open(GRAPH_PATH, 'w') as f:
        json.dump(graph, f, indent=2)
    sys.stderr.write(f"Saved: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges\n")


def resolve_id(node_map, partial):
    if partial in node_map:
        return partial
    matches = [k for k in node_map if k.startswith(partial)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        sys.exit(f"Ambiguous ID prefix '{partial}' matches: {[m[:8] for m in matches]}")
    sys.exit(f"No node found with ID starting with '{partial}'")


def cmd_summary(graph):
    meta = graph['metadata']
    nodes = graph['nodes']
    edges = graph['edges']
    node_map = {n['id']: n for n in nodes}

    now = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        f"# H4YF Knowledge Graph Context",
        f"*Auto-generated from .claude/knowledge-graph.json — {now}*",
        f"*{len(nodes)} nodes · {len(edges)} edges*",
        "",
    ]

    by_type = {}
    for node in nodes:
        by_type.setdefault(node['type'], []).append(node)

    for t in VALID_TYPES:
        if t not in by_type:
            continue
        lines.append(f"## {t} Nodes")
        for n in sorted(by_type[t], key=lambda x: x.get('created', '')):
            desc = n.get('description', '')
            lines.append(f"- **{n['name']}** (`{n['id'][:8]}`): {desc}")
        lines.append("")

    if edges:
        lines.append("## Relationships")
        for e in edges:
            src_name = node_map.get(e['source'], {}).get('name', e['source'][:8])
            tgt_name = node_map.get(e['target'], {}).get('name', e['target'][:8])
            note = f" — {e['notes']}" if e.get('notes') else ""
            lines.append(f"- **{src_name}** `{e['relationship']}` **{tgt_name}**{note}")
        lines.append("")

    recent = sorted(nodes, key=lambda x: x.get('created', ''), reverse=True)[:5]
    if recent:
        lines.append("## Recent Activity")
        for n in recent:
            lines.append(f"- [{n.get('created', '?')}] {n['type']}: **{n['name']}**")
        lines.append("")

    lines.append("---")
    lines.append("*Update the graph: `python3 .claude/scripts/kg.py add-node TYPE NAME DESC`*")
    lines.append("*Regenerate: `python3 .claude/scripts/kg.py summary > CONTEXT.md`*")

    print("\n".join(lines))


def cmd_add_node(graph, args):
    if len(args) < 2:
        sys.exit("Usage: kg.py add-node TYPE NAME [DESCRIPTION]")
    ntype, name = args[0], args[1]
    description = args[2] if len(args) > 2 else ""

    if ntype not in VALID_TYPES:
        sys.exit(f"Invalid type '{ntype}'. Choose from: {', '.join(VALID_TYPES)}")

    node_id = str(uuid.uuid4())
    graph['nodes'].append({
        "id": node_id,
        "type": ntype,
        "name": name,
        "description": description,
        "created": datetime.now(timezone.utc).date().isoformat(),
        "tags": [],
        "properties": {}
    })
    save_graph(graph)
    print(f"Added {ntype}: {name} (id: {node_id[:8]})")


def cmd_add_edge(graph, args):
    if len(args) < 3:
        sys.exit("Usage: kg.py add-edge SOURCE_ID RELATIONSHIP TARGET_ID [NOTES]")
    source_partial, relationship, target_partial = args[0], args[1], args[2]
    notes = args[3] if len(args) > 3 else ""

    if relationship not in VALID_RELS:
        sys.exit(f"Invalid relationship '{relationship}'. Choose from: {', '.join(VALID_RELS)}")

    node_map = {n['id']: n for n in graph['nodes']}
    source_id = resolve_id(node_map, source_partial)
    target_id = resolve_id(node_map, target_partial)

    graph['edges'].append({
        "source": source_id,
        "target": target_id,
        "relationship": relationship,
        "created": datetime.now(timezone.utc).date().isoformat(),
        "notes": notes
    })
    save_graph(graph)
    print(f"Added edge: {node_map[source_id]['name']} --{relationship}--> {node_map[target_id]['name']}")


def cmd_list(graph, args):
    ntype = args[0] if args else None
    nodes = graph['nodes']
    if ntype:
        nodes = [n for n in nodes if n['type'].lower() == ntype.lower()]
    if not nodes:
        print("No nodes found.")
        return
    for n in sorted(nodes, key=lambda x: (x['type'], x.get('created', ''))):
        print(f"[{n['id'][:8]}] {n['type']}: {n['name']} — {n.get('description', '')[:80]}")


def cmd_query(graph, args):
    if not args:
        sys.exit("Usage: kg.py query SEARCH_TERM")
    term = ' '.join(args).lower()
    results = [
        n for n in graph['nodes']
        if term in n['name'].lower() or term in n.get('description', '').lower()
        or any(term in t.lower() for t in n.get('tags', []))
    ]
    if not results:
        print("No results found.")
        return
    for n in results:
        print(f"[{n['id'][:8]}] {n['type']}: {n['name']} — {n.get('description', '')[:80]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    graph = load_graph()
    cmd, args = sys.argv[1], sys.argv[2:]

    dispatch = {
        'summary': lambda: cmd_summary(graph),
        'add-node': lambda: cmd_add_node(graph, args),
        'add-edge': lambda: cmd_add_edge(graph, args),
        'list': lambda: cmd_list(graph, args),
        'query': lambda: cmd_query(graph, args),
    }

    if cmd not in dispatch:
        sys.exit(f"Unknown command '{cmd}'. Available: {', '.join(dispatch)}")

    dispatch[cmd]()


if __name__ == '__main__':
    main()
