#!/usr/bin/env python3
"""Knowledge graph CLI — portable cross-session memory for Claude Code projects.

Usage:
  kg.py summary               Print CONTEXT.md (pipe to file: kg.py summary > CONTEXT.md)
  kg.py add-node TYPE NAME DESC    Add a node (TYPE: Decision Component Feature Entity Concept)
  kg.py update-node ID FIELD VAL   Update a node field (name | description | status)
  kg.py remove-node ID             Remove a node and all its edges
  kg.py add-edge SRC REL TGT [NOTE]  Add a directed edge (8-char ID prefix accepted)
  kg.py list [TYPE]            List nodes, optionally filtered by type
  kg.py query TERM             Search nodes by name, description, or tags
  kg.py neighbors ID           Show all nodes connected to a node
  kg.py validate               Check graph integrity (dangling edges, duplicate IDs)
  kg.py init NAME DESC         Initialise a fresh knowledge-graph.json

Node types:   Decision  Component  Feature  Entity  Concept
Relationships: depends_on  implements  supersedes  relates_to  part_of  created_by
Status values: active  deprecated  superseded
"""

import json
import sys
import os
import uuid
from datetime import datetime, timezone

GRAPH_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'knowledge-graph.json')

VALID_TYPES = ['Decision', 'Component', 'Feature', 'Entity', 'Concept']
VALID_RELS  = ['depends_on', 'implements', 'supersedes', 'relates_to', 'part_of', 'created_by']
VALID_STATUS = ['active', 'deprecated', 'superseded']

SUMMARY_LIMITS = {
    'Entity': None,       # always show all
    'Decision': None,     # always show all
    'Component': 20,
    'Feature': 20,
    'Concept': 10,
}
SUMMARY_MAX_EDGES = 40
SUMMARY_MAX_RECENT = 10


def now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def load_graph():
    try:
        with open(GRAPH_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"Graph not found at {GRAPH_PATH}. Run: kg.py init NAME DESC")
    except json.JSONDecodeError as e:
        sys.exit(f"Graph JSON is corrupt: {e}\nFix .claude/knowledge-graph.json before continuing.")


def save_graph(graph):
    graph['metadata']['last_updated'] = now_iso()
    with open(GRAPH_PATH, 'w') as f:
        json.dump(graph, f, indent=2)
    sys.stderr.write(f"[kg] Saved: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges\n")


def resolve_id(node_map, partial):
    if partial in node_map:
        return partial
    matches = [k for k in node_map if k.startswith(partial)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        sys.exit(f"Ambiguous ID prefix '{partial}' — matches: {[m[:12] for m in matches]}")
    sys.exit(f"No node found with ID starting with '{partial}'")


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_summary(graph):
    meta   = graph['metadata']
    nodes  = graph['nodes']
    edges  = graph['edges']
    node_map = {n['id']: n for n in nodes}

    project  = meta.get('project', 'Project')
    now      = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    active   = [n for n in nodes if n.get('status', 'active') == 'active']
    inactive = len(nodes) - len(active)

    lines = [
        f"# {project} Knowledge Graph Context",
        f"*Auto-generated — {now}*",
        f"*{len(active)} active nodes · {len(edges)} edges"
        + (f" · {inactive} deprecated/superseded" if inactive else "") + "*",
        "",
    ]

    by_type = {}
    for node in active:
        by_type.setdefault(node['type'], []).append(node)

    for t in VALID_TYPES:
        if t not in by_type:
            continue
        type_nodes = sorted(by_type[t], key=lambda x: x.get('created', ''))
        limit = SUMMARY_LIMITS.get(t)
        shown = type_nodes if limit is None else type_nodes[-limit:]
        omitted = len(type_nodes) - len(shown)

        lines.append(f"## {t} Nodes")
        if omitted:
            lines.append(f"*Showing {len(shown)} most recent of {len(type_nodes)} — use `kg.py list {t}` to see all*")
        for n in shown:
            desc = n.get('description', '')
            lines.append(f"- **{n['name']}** (`{n['id'][:8]}`): {desc}")
        lines.append("")

    active_ids = {n['id'] for n in active}
    active_edges = [e for e in edges
                    if e['source'] in active_ids and e['target'] in active_ids]
    if active_edges:
        shown_edges = active_edges[-SUMMARY_MAX_EDGES:]
        omitted_e = len(active_edges) - len(shown_edges)
        lines.append("## Relationships")
        if omitted_e:
            lines.append(f"*Showing {len(shown_edges)} most recent of {len(active_edges)}*")
        for e in shown_edges:
            src  = node_map.get(e['source'], {}).get('name', e['source'][:8])
            tgt  = node_map.get(e['target'], {}).get('name', e['target'][:8])
            note = f" — {e['notes']}" if e.get('notes') else ""
            lines.append(f"- **{src}** `{e['relationship']}` **{tgt}**{note}")
        lines.append("")

    recent = sorted(nodes, key=lambda x: x.get('created', ''), reverse=True)[:SUMMARY_MAX_RECENT]
    if recent:
        lines.append("## Recent Activity")
        for n in recent:
            ts = n.get('created', '?')[:10]
            status_tag = f" [{n['status']}]" if n.get('status', 'active') != 'active' else ""
            lines.append(f"- [{ts}] {n['type']}: **{n['name']}**{status_tag}")
        lines.append("")

    lines += [
        "---",
        "*Update: `python3 .claude/scripts/kg.py add-node TYPE NAME DESC`*",
        "*Regenerate: `python3 .claude/scripts/kg.py summary > CONTEXT.md`*",
    ]
    print("\n".join(lines))


def cmd_add_node(graph, args):
    if len(args) < 2:
        sys.exit("Usage: kg.py add-node TYPE NAME [DESCRIPTION]")
    ntype, name = args[0], args[1]
    description = args[2] if len(args) > 2 else ""

    if ntype not in VALID_TYPES:
        sys.exit(f"Invalid type '{ntype}'. Choose from: {', '.join(VALID_TYPES)}")

    node_id = str(uuid.uuid4())
    session = os.environ.get('KG_SESSION_ID', '')
    graph['nodes'].append({
        "id": node_id,
        "type": ntype,
        "name": name,
        "description": description,
        "status": "active",
        "created": now_iso(),
        "tags": [],
        "session_created": session,
        "properties": {}
    })
    save_graph(graph)
    print(f"Added {ntype}: {name} (id: {node_id[:8]})")


def cmd_update_node(graph, args):
    if len(args) < 3:
        sys.exit("Usage: kg.py update-node ID FIELD VALUE  (FIELD: name | description | status)")
    node_map = {n['id']: n for n in graph['nodes']}
    node_id  = resolve_id(node_map, args[0])
    field, value = args[1], args[2]

    if field not in ('name', 'description', 'status'):
        sys.exit("FIELD must be one of: name, description, status")
    if field == 'status' and value not in VALID_STATUS:
        sys.exit(f"Invalid status '{value}'. Choose from: {', '.join(VALID_STATUS)}")

    node = node_map[node_id]
    old  = node.get(field, '')
    node[field] = value
    node['updated'] = now_iso()
    save_graph(graph)
    print(f"Updated {field} on '{node['name']}': {old!r} → {value!r}")


def cmd_remove_node(graph, args):
    if not args:
        sys.exit("Usage: kg.py remove-node ID")
    node_map = {n['id']: n for n in graph['nodes']}
    node_id  = resolve_id(node_map, args[0])
    name     = node_map[node_id]['name']

    before_edges = len(graph['edges'])
    graph['nodes'] = [n for n in graph['nodes'] if n['id'] != node_id]
    graph['edges'] = [e for e in graph['edges']
                      if e['source'] != node_id and e['target'] != node_id]
    removed_edges = before_edges - len(graph['edges'])

    save_graph(graph)
    print(f"Removed node '{name}' and {removed_edges} connected edge(s)")


def cmd_add_edge(graph, args):
    if len(args) < 3:
        sys.exit("Usage: kg.py add-edge SOURCE_ID RELATIONSHIP TARGET_ID [NOTES]")
    source_partial, relationship, target_partial = args[0], args[1], args[2]
    notes = args[3] if len(args) > 3 else ""

    if relationship not in VALID_RELS:
        sys.exit(f"Invalid relationship '{relationship}'. Choose from: {', '.join(VALID_RELS)}")

    node_map  = {n['id']: n for n in graph['nodes']}
    source_id = resolve_id(node_map, source_partial)
    target_id = resolve_id(node_map, target_partial)

    graph['edges'].append({
        "source": source_id,
        "target": target_id,
        "relationship": relationship,
        "created": now_iso(),
        "notes": notes
    })
    save_graph(graph)
    print(f"Edge: {node_map[source_id]['name']} --{relationship}--> {node_map[target_id]['name']}")


def cmd_list(graph, args):
    ntype = args[0] if args else None
    nodes = graph['nodes']
    if ntype:
        nodes = [n for n in nodes if n['type'].lower() == ntype.lower()]
    if not nodes:
        print("No nodes found.")
        return
    for n in sorted(nodes, key=lambda x: (x['type'], x.get('created', ''))):
        status = f" [{n['status']}]" if n.get('status', 'active') != 'active' else ""
        print(f"[{n['id'][:8]}] {n['type']}{status}: {n['name']} — {n.get('description', '')[:80]}")


def cmd_query(graph, args):
    if not args:
        sys.exit("Usage: kg.py query SEARCH_TERM")
    term = ' '.join(args).lower()
    results = [
        n for n in graph['nodes']
        if term in n['name'].lower()
        or term in n.get('description', '').lower()
        or any(term in t.lower() for t in n.get('tags', []))
    ]
    if not results:
        print("No results found.")
        return
    for n in results:
        status = f" [{n['status']}]" if n.get('status', 'active') != 'active' else ""
        print(f"[{n['id'][:8]}] {n['type']}{status}: {n['name']} — {n.get('description', '')[:80]}")


def cmd_neighbors(graph, args):
    if not args:
        sys.exit("Usage: kg.py neighbors ID")
    node_map = {n['id']: n for n in graph['nodes']}
    node_id  = resolve_id(node_map, args[0])
    name     = node_map[node_id]['name']

    print(f"Neighbors of: {name} [{node_id[:8]}]")
    found = False
    for e in graph['edges']:
        if e['source'] == node_id:
            tgt  = node_map.get(e['target'], {})
            note = f" ({e['notes']})" if e.get('notes') else ""
            print(f"  → [{e['relationship']}] {tgt.get('name', '?')} [{e['target'][:8]}]{note}")
            found = True
        elif e['target'] == node_id:
            src  = node_map.get(e['source'], {})
            note = f" ({e['notes']})" if e.get('notes') else ""
            print(f"  ← [{e['relationship']}] {src.get('name', '?')} [{e['source'][:8]}]{note}")
            found = True
    if not found:
        print("  (no edges)")


def cmd_validate(graph):
    errors = []
    node_ids = {n['id'] for n in graph['nodes']}

    seen_ids = set()
    for n in graph['nodes']:
        if n['id'] in seen_ids:
            errors.append(f"Duplicate node ID: {n['id'][:8]}")
        seen_ids.add(n['id'])
        if n.get('type') not in VALID_TYPES:
            errors.append(f"Invalid type '{n.get('type')}' on node {n['id'][:8]} ({n.get('name')})")
        if n.get('status', 'active') not in VALID_STATUS:
            errors.append(f"Invalid status '{n.get('status')}' on node {n['id'][:8]} ({n.get('name')})")

    for i, e in enumerate(graph['edges']):
        if e['source'] not in node_ids:
            errors.append(f"Edge {i}: dangling source {e['source'][:8]}")
        if e['target'] not in node_ids:
            errors.append(f"Edge {i}: dangling target {e['target'][:8]}")
        if e.get('relationship') not in VALID_RELS:
            errors.append(f"Edge {i}: invalid relationship '{e.get('relationship')}'")

    if errors:
        print(f"Graph validation FAILED ({len(errors)} error(s)):")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"Graph OK: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges — no issues found.")


def cmd_init(args):
    if len(args) < 2:
        sys.exit("Usage: kg.py init PROJECT_NAME PROJECT_DESCRIPTION")
    name, description = args[0], args[1]

    if os.path.exists(GRAPH_PATH):
        sys.exit(f"Graph already exists at {GRAPH_PATH}. Delete it first to reinitialise.")

    graph = {
        "version": "1.1",
        "metadata": {
            "project": name,
            "description": description,
            "created": now_iso(),
            "last_updated": now_iso()
        },
        "nodes": [],
        "edges": []
    }
    os.makedirs(os.path.dirname(GRAPH_PATH), exist_ok=True)
    with open(GRAPH_PATH, 'w') as f:
        json.dump(graph, f, indent=2)
    print(f"Initialised knowledge graph for '{name}' at {GRAPH_PATH}")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd  = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'init':
        cmd_init(args)
        return

    graph = load_graph()

    dispatch = {
        'summary':     lambda: cmd_summary(graph),
        'add-node':    lambda: cmd_add_node(graph, args),
        'update-node': lambda: cmd_update_node(graph, args),
        'remove-node': lambda: cmd_remove_node(graph, args),
        'add-edge':    lambda: cmd_add_edge(graph, args),
        'list':        lambda: cmd_list(graph, args),
        'query':       lambda: cmd_query(graph, args),
        'neighbors':   lambda: cmd_neighbors(graph, args),
        'validate':    lambda: cmd_validate(graph),
    }

    if cmd not in dispatch:
        sys.exit(f"Unknown command '{cmd}'. Available: {', '.join(dispatch)}")

    dispatch[cmd]()


if __name__ == '__main__':
    main()
