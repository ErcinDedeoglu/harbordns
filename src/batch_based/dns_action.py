from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import List, Optional

class ActionType(Enum):
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"

@dataclass
class DNSAction:
    timestamp: datetime
    action_type: ActionType
    hostname: str
    type: str
    record_data: dict
    previous_data: Optional[dict] = None  # Only for MODIFY actions
    provider: str = 'cloudflare'
    target: Optional[str] = None
    ttl: str = '300'
    proxied: str = 'false'

    def __post_init__(self):
        # Set default target to hostname if not provided
        if self.target is None:
            self.target = self.hostname
        
        # Convert proxied to boolean and handle TTL
        self.proxied = self.proxied.lower() == 'true' if isinstance(self.proxied, str) else bool(self.proxied)
        # Force TTL to '1' if proxied is True
        if self.proxied:
            self.ttl = '1'

class DNSActionQueue:
    def __init__(self):
        self._actions: List[DNSAction] = []

    def add_action(self, action: DNSAction):
        # Remove any existing actions for the same hostname and type
        self._actions = [
            a for a in self._actions 
            if not (a.hostname == action.hostname and a.type == action.type)
        ]
        self._actions.append(action)

    def get_ready_actions(self, age_threshold_seconds: int) -> List[DNSAction]:
        current_time = datetime.now()
        ready_actions = []
        remaining_actions = []
        for action in self._actions:
            age = (current_time - action.timestamp).total_seconds()
            if age >= age_threshold_seconds:
                ready_actions.append(action)
            else:
                remaining_actions.append(action)
        self._actions = remaining_actions
        return ready_actions

    def __len__(self):
        return len(self._actions)