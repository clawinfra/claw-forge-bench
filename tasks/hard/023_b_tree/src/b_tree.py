"""B-Tree implementation (order 3)."""


class BTreeNode:
    def __init__(self, leaf: bool = True):
        self.keys: list[int] = []
        self.children: list[BTreeNode] = []
        self.leaf = leaf


class BTree:
    def __init__(self, order: int = 3):
        self.root = BTreeNode()
        self.order = order  # max keys per node = order - 1

    def search(self, key: int, node: BTreeNode | None = None) -> bool:
        """Search for a key in the B-tree."""
        if node is None:
            node = self.root
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return True
        if node.leaf:
            return False
        return self.search(key, node.children[i])

    def insert(self, key: int) -> None:
        """Insert a key into the B-tree."""
        root = self.root
        if len(root.keys) == self.order - 1:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        self._insert_non_full(self.root, key)

    def _insert_non_full(self, node: BTreeNode, key: int) -> None:
        """Insert into a node that is not full."""
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(0)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == self.order - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key)

    def _split_child(self, parent: BTreeNode, index: int) -> None:
        """Split a full child node."""
        order = self.order
        child = parent.children[index]
        mid = (order - 1) // 2

        new_node = BTreeNode(leaf=child.leaf)
        # Bug: takes wrong slice — includes median in both halves
        new_node.keys = child.keys[mid:]  # Should be mid+1
        # Bug: doesn't promote median to parent correctly
        parent.keys.insert(index, child.keys[mid])
        child.keys = child.keys[:mid + 1]  # Should be :mid

        if not child.leaf:
            new_node.children = child.children[mid:]  # Wrong split
            child.children = child.children[:mid + 1]

        parent.children.insert(index + 1, new_node)

    def in_order(self) -> list[int]:
        """Return all keys in sorted order."""
        result: list[int] = []
        self._in_order(self.root, result)
        return result

    def _in_order(self, node: BTreeNode, result: list[int]) -> None:
        """In-order traversal."""
        for i, key in enumerate(node.keys):
            if not node.leaf and i < len(node.children):
                self._in_order(node.children[i], result)
            result.append(key)
        if not node.leaf and len(node.children) > len(node.keys):
            self._in_order(node.children[-1], result)
