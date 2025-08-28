import os
from dotenv import load_dotenv
import asyncio
import redis.asyncio as redis
import json

load_dotenv()

HOST = "lab3.redesuvg.cloud" 
PORT = 6379
PWD  = "UVGRedis2025"

class NetworkNodePubSub:
    def __init__(self, node_id, channels, neighbors=None):
        self.node_id = node_id
        self.channels = channels
        self.neighbors = neighbors if neighbors else []
        self.subscribed = set(channels)
        self.algorithm_logic = None

        self.redis = redis.Redis(host=HOST, port=PORT, password=PWD)
        self.pubsub = self.redis.pubsub()
    
    def set_algorithm(self, algorithm):
        self.algorithm_logic = algorithm
 
    async def start(self):
        await self.pubsub.subscribe(self.node_id)
        print(f"[{self.node_id}] Subscribed to own channel")

        for neighbor in self.neighbors:
            await self.pubsub.subscribe(neighbor)
            self.subscribed.add(neighbor)
            print(f"[{self.node_id}] Subscribed to neighbor channel {neighbor}")

        await self.send_hello("broadcast")

    async def listen(self):
        while True:
            message = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()

                try:
                    packet = json.loads(data)
                except Exception:
                    print(f"[{self.node_id}] Invalid message: {data}")
                    continue

                if packet.get("type") == "hello":
                    await self.handle_hello(packet)
                else:
                    if self.algorithm_logic:
                        await self.algorithm_logic.handle_message(packet)
            await asyncio.sleep(0.01)

    async def publish(self, channel, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        await self.redis.publish(channel, message)

    async def send_hello(self, target):
        hello_msg = {
            "proto": "lsr",
            "type": "hello",
            "from": self.node_id,
            "to": target,
            "ttl": 5,
            "headers": self.neighbors,
            "payload": ""
        }

        if target == "broadcast":
            for neighbor in self.neighbors:
                await self.publish(neighbor, hello_msg)
                print(f"[{self.node_id}] Hello sent to {neighbor}")
        else:
            await self.publish(target, hello_msg)
            print(f"[{self.node_id}] Hello sent directly to {target}")

    async def handle_hello(self, packet):
        sender = packet["from"]
        if sender == self.node_id:
            return

        print(f"[{self.node_id}] Hello received from {sender}")

        if sender not in self.subscribed:
            await self.pubsub.subscribe(sender)
            self.subscribed.add(sender)
            print(f"[{self.node_id}] Now subscribed to {sender} channel")
            await self.send_hello(sender)

