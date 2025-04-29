import os, asyncio, jwt, datetime, grpc
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient
from proto import messaging_service_pb2 as pb
from proto import messaging_service_pb2_grpc as pb_grpc

# JWT secret and MongoDB URI (shared settings for microservices)
SECRET     = os.getenv("SECRET_KEY", "dev")
MONGO_URI  = os.getenv("MONGO_URI", "mongodb://mongodb:27017")

# Connect to MongoDB (used for storing message history)
mongo      = AsyncIOMotorClient(MONGO_URI)
db         = mongo["messagingdb"]

# Helper function to get current UTC time
def utc(): return datetime.datetime.utcnow()

# Live Hub (in-memory user tracking)
class Hub:
    def __init__(self):
        self.queues:   dict[str, asyncio.Queue] = {}          # user → outbound queue
        self.channel:  dict[str, str]            = {}          # user → current channel
        self.members: defaultdict[str, set[str]] = defaultdict(set) # channel → set of users

    def login(self, user: str, q: asyncio.Queue):
        # Register new user in "Main" channel
        self.queues[user]  = q
        self.channel[user] = "Main"
        self.members["Main"].add(user)

    def logout(self, user: str):
        # Remove user from system on disconnect
        ch = self.channel.pop(user, None)
        if ch: self.members[ch].discard(user)
        self.queues.pop(user, None)

    # Send a message to a specific user
    async def unicast(self, user: str, env: pb.ServerEnvelope):
        q = self.queues.get(user)
        if q: await q.put(env)

    # Broadcast a message to all users in a specific channel
    async def broadcast(self, ch: str, env: pb.ServerEnvelope, *, exclude=None):
        for u in self.members[ch]:
            if u != exclude:
                await self.unicast(u, env)

hub = Hub()

# Messaging Service Implementation
class Messaging(pb_grpc.MessagingServiceServicer):
    # Main gRPC bidirectional stream between client and server
    async def Chat(self, req_iter, ctx):
        send_q: asyncio.Queue[pb.ServerEnvelope] = asyncio.Queue()
        user: str | None = None

        # Consumer task: processes incoming messages from client
        async def consume():
            nonlocal user
            async for env in req_iter:
                match env.WhichOneof("payload"):

                    # Validate user's JWT token
                    case "init":
                        try:
                            payload = jwt.decode(env.init.token, SECRET,
                                                 algorithms=["HS256"])
                            user = payload["sub"]
                            hub.login(user, send_q)
                            await send_q.put(pb.ServerEnvelope(
                                notice=f"Welcome {user}! You are now in channel Main."))
                            await self._send_history(user, "Main", send_q)
                        except jwt.InvalidTokenError:
                            await send_q.put(pb.ServerEnvelope(notice="Bad token"))
                            break

                    # Handle channel switching
                    case "join":
                        new_ch = env.join.name or "Main"
                        old_ch = hub.channel[user]

                        if new_ch == old_ch:
                            await send_q.put(pb.ServerEnvelope(
                                notice=f"You are already in {new_ch}"))
                            continue

                        # leave old
                        hub.members[old_ch].discard(user)
                        await hub.broadcast(old_ch,
                            pb.ServerEnvelope(notice=f"{user} left channel."),
                            exclude=user)

                        # join new
                        hub.channel[user] = new_ch
                        hub.members[new_ch].add(user)
                        await send_q.put(pb.ServerEnvelope(
                            notice=f"You joined {new_ch}"))
                        await hub.broadcast(new_ch,
                            pb.ServerEnvelope(notice=f"{user} joined {new_ch}"),
                            exclude=user)

                        # immediate history dump
                        await self._send_history(user, new_ch, send_q)

                    # Handle explicit leave (back to Main channel)
                    case "leave":
                        old_ch = env.leave.name or hub.channel[user]

                        # ignore if they’re not actually in that room or already in Main
                        if hub.channel[user] != old_ch or old_ch == "Main":
                            await send_q.put(pb.ServerEnvelope(
                                notice="You are already in Main." if old_ch=="Main"
                                       else f"You are not in {old_ch}"))
                            continue

                        # leave old_ch
                        hub.members[old_ch].discard(user)
                        await hub.broadcast(old_ch,
                            pb.ServerEnvelope(notice=f"{user} left channel."),
                            exclude=user)

                        # join Main
                        hub.channel[user] = "Main"
                        hub.members["Main"].add(user)
                        await send_q.put(pb.ServerEnvelope(
                            notice="You returned to Main."))
                        await hub.broadcast("Main",
                            pb.ServerEnvelope(notice=f"{user} joined Main."),
                            exclude=user)

                        # send Main history
                        await self._send_history(user, "Main", send_q)


                    # Public channel message
                    case "cm":
                        ch = hub.channel[user]
                        body = env.cm.body
                        await db.messages.insert_one({
                            "channel": ch, "sender": user,
                            "body": body, "ts": utc()
                        })
                        await hub.broadcast(ch,
                            pb.ServerEnvelope(cm=pb.ChannelMsg(
                                channel=ch, body=f"{user}: {body}"
                            )))

                    # Private message
                    case "pm":
                        pm = env.pm
                        await db.messages.insert_one({
                            "recipient": pm.recipient, "sender": user,
                            "body": pm.body, "ts": utc()
                        })
                        await hub.unicast(pm.recipient,
                            pb.ServerEnvelope(pm=pb.PrivateMsg(
                                recipient=pm.recipient,
                                body=f"(private) {user}: {pm.body}"
                            )))
                        await send_q.put(pb.ServerEnvelope(pm=pb.PrivateMsg(
                            recipient=pm.recipient,
                            body=f"(to {pm.recipient}) {pm.body}"
                        )))

        consumer = asyncio.create_task(consume())

        # Producer task: sends messages back to client
        try:
            while True:
                env = await send_q.get()
                yield env
        finally:
            consumer.cancel()
            if user: hub.logout(user)

    # Helper: Send recent message history of a channel
    async def _send_history(self, user: str, ch: str, q: asyncio.Queue, limit=100):
        cur = db.messages.find({"channel": ch},
                               sort=[("ts", -1)], limit=limit)
        items = [pb.ChannelMsg(
                    channel=ch,
                    body=f"{d['sender']}: {d['body']}")
                 async for d in cur][::-1]
        if items:
            await q.put(pb.ServerEnvelope(
                history_res=pb.HistoryRes(items=items)))

# Server Bootstrap
async def serve():
    server = grpc.aio.server()
    pb_grpc.add_MessagingServiceServicer_to_server(Messaging(), server)
    server.add_insecure_port("[::]:50054")
    await server.start()
    print("messaging_service ready on :50054")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
