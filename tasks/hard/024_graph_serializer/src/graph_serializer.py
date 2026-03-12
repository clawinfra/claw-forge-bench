"""Graph serializer with cycle detection."""
import json


class Node:
    def __init__(self, id: str, value: object = None):
        self.id = id
        self.value = value
        self.edges: list[Node] = []

    def add_edge(self, node: "Node") -> None:
        self.edges.append(node)


def serialize_graph(root: Node) -> str:
    """Serialize a graph to JSON, detecting cycles."""
    visited: set[str] = set()
    result = _serialize_node(root, visited)
    return json.dumps(result, indent=2)


def _serialize_node(node: Node, visited: set[str]) -> dict:
    """Recursively serialize a node."""
    # Bug: checks visited AFTER accessing node properties
    # Self-referencing nodes cause infinite recursion
    entry = {
        "id": node.id,
        "value": node.value,
        "edges": [],
    }

    visited.add(node.id)

    for edge in node.edges:
        if edge.id not in visited:
            entry["edges"].append(_serialize_node(edge, visited))
        else:
            # Bug: doesn't include back-reference marker for self-refs
            pass

    return entry


def deserialize_graph(json_str: str) -> Node:
    """Deserialize a graph from JSON."""
    data = json.loads(json_str)
    nodes: dict[str, Node] = {}
    return _deserialize_node(data, nodes)


def _deserialize_node(data: dict, nodes: dict[str, Node]) -> Node:
    """Recursively deserialize a node."""
    node_id = data["id"]
    if node_id in nodes:
        return nodes[node_id]
    node = Node(node_id, data.get("value"))
    nodes[node_id] = node
    for edge_data in data.get("edges", []):
        if isinstance(edge_data, dict) and "ref" in edge_data:
            if edge_data["ref"] in nodes:
                node.edges.append(nodes[edge_data["ref"]])
        elif isinstance(edge_data, dict):
            node.edges.append(_deserialize_node(edge_data, nodes))
    return node
