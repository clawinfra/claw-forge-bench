"""Singly linked list implementation."""


class Node:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node


class LinkedList:
    def __init__(self):
        self.head = None
        self._size = 0

    def append(self, value):
        """Append a value to the end."""
        new_node = Node(value)
        if not self.head:
            self.head = new_node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = new_node
        self._size += 1

    def delete(self, value):
        """Delete first occurrence of value. Returns True if found."""
        if not self.head:
            return False
        if self.head.value == value:
            self.head = self.head.next
            self._size -= 1
            return True
        current = self.head
        while current.next:
            if current.next.value == value:
                # Bug: doesn't handle when deleting the tail node properly
                # (works for middle nodes but the loop continues past None)
                current.next = current.next.next
                # Bug: forgot to decrement size
                return True
            current = current.next
        return False

    def to_list(self) -> list:
        """Convert to Python list."""
        result = []
        current = self.head
        while current:
            result.append(current.value)
            current = current.next
        return result

    def __len__(self):
        return self._size
