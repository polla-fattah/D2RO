"""
V2V Ad-Hoc Mesh Communication Network Simulator.
Simulates peer-to-peer telemetry, spatial broadcast radius, TTL multi-hop forwarding,
and event-driven congestion alerts.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Any

class MessageType(Enum):
    CONGESTION_ALERT = auto()
    LOCK_REQUEST = auto()
    LOCK_GRANT = auto()
    LOCK_RELEASE = auto()
    HEARTBEAT = auto()

@dataclass
class MeshPacket:
    """Telemetry packet exchanged over V2V mesh network."""
    msg_type: MessageType
    sender_id: int
    edge: Tuple[str, str]
    cost_penalty: float = 0.0
    priority: float = 0.0  # Tie-breaker (e.g. distance to goal or timestamp)
    ttl: int = 3           # Multi-hop time to live
    timestamp: float = 0.0
    packet_id: int = 0

class MeshNetwork:
    """
    Decentralized V2V Mesh Network Simulator.
    Delivers packets to peer agents within spatial communication radius.
    """
    def __init__(self, comm_radius: float = 300.0, packet_loss_rate: float = 0.0):
        self.comm_radius = comm_radius
        self.packet_loss_rate = packet_loss_rate
        self.agents: Dict[int, Any] = {}
        self.inbound_queues: Dict[int, List[MeshPacket]] = {}
        self.total_packets_transmitted: int = 0
        self.packet_counter: int = 0

    def register_agent(self, agent_id: int, agent_ref: Any) -> None:
        self.agents[agent_id] = agent_ref
        self.inbound_queues[agent_id] = []

    def unregister_agent(self, agent_id: int) -> None:
        if agent_id in self.agents:
            del self.agents[agent_id]
        if agent_id in self.inbound_queues:
            del self.inbound_queues[agent_id]

    def broadcast(self, sender_id: int, msg_type: MessageType, edge: Tuple[str, str],
                  cost_penalty: float = 0.0, priority: float = 0.0, ttl: int = 3,
                  current_time: float = 0.0) -> int:
        """
        Broadcasts packet to all peers within communication radius.
        Returns number of recipients.
        """
        sender = self.agents.get(sender_id)
        if not sender:
            return 0

        self.packet_counter += 1
        packet = MeshPacket(
            msg_type=msg_type,
            sender_id=sender_id,
            edge=edge,
            cost_penalty=cost_penalty,
            priority=priority,
            ttl=ttl,
            timestamp=current_time,
            packet_id=self.packet_counter
        )

        recipients_count = 0
        s_pos = sender.current_pos

        for peer_id, peer in self.agents.items():
            if peer_id == sender_id:
                continue

            p_pos = peer.current_pos
            dist = math.hypot(s_pos[0] - p_pos[0], s_pos[1] - p_pos[1])
            if dist <= self.comm_radius:
                self.inbound_queues[peer_id].append(packet)
                recipients_count += 1
                self.total_packets_transmitted += 1

        return recipients_count

    def fetch_inbound(self, agent_id: int) -> List[MeshPacket]:
        """Retrieves and clears inbound message queue for a specific agent."""
        queue = self.inbound_queues.get(agent_id, [])
        self.inbound_queues[agent_id] = []
        return queue
