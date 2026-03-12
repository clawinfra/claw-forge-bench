"""Event emitter with listener management."""


class EventEmitter:
    def __init__(self):
        self._listeners: dict[str, list] = {}

    def on(self, event: str, callback) -> None:
        """Register a listener for an event."""
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback) -> None:
        """Remove a listener for an event."""
        if event in self._listeners:
            self._listeners[event].remove(callback)

    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event, calling all registered listeners."""
        if event not in self._listeners:
            return
        # Bug: iterating over list while it can be mutated by off()
        for listener in self._listeners[event]:
            listener(*args, **kwargs)

    def once(self, event: str, callback) -> None:
        """Register a one-time listener."""
        def wrapper(*args, **kwargs):
            self.off(event, wrapper)
            callback(*args, **kwargs)
        self.on(event, wrapper)

    def listener_count(self, event: str) -> int:
        """Return number of listeners for an event."""
        return len(self._listeners.get(event, []))
