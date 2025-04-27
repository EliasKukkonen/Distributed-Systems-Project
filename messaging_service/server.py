import os, asyncio, jwt, datetime, grpc
from collections import defaultdict
from motor.motor_asyncio import AsyncIOMotorClient
from proto import messaging_service_pb2 as pb
from proto import messaging_service_pb2_grpc as pb_grpc

# ──────────────────────────────────────────────────────────────
SECRET     = os.getenv("SECRET_KEY", "dev")
MONGO_URI  = os.getenv("MONGO_URI", "mongodb://mongodb:27017")
mongo      = AsyncIOMotorClient(MONGO_URI)
db         = mongo["messagingdb"]

def utc(): return datetime.datetime.utcnow()

# ───────────────────────── live-hub ───────────────────────────
class Hub:
    def __init__(self):
        self.queues:   dict[str, asyncio.Queue] = {}          # user → outbound queue
        self.channel:  dict[str, str]            = {}          # user → current channel
        self.members: defaultdict[str, set[str]] = defaultdict(set)

    def login(self, user: str, q: asyncio.Queue):
        self.queues[user]  = q
        self.channel[user] = "Main"
        self.members["Main"].add(user)

    def logout(self, user: str):
        ch = self.channel.pop(user, None)
        if ch: self.members[ch].discard(user)
        self.queues.pop(user, None)

    # helpers ---------------------------------------------------
    async def unicast(self, user: str, env: pb.ServerEnvelope):
        q = self.queues.get(user)
        if q: await q.put(env)

    async def broadcast(self, ch: str, env: pb.ServerEnvelope, *, exclude=None):
        for u in self.members[ch]:
            if u != exclude:
                await self.unicast(u, env)

hub = Hub()

# ──────────────────────── servicer ────────────────────────────
class Messaging(pb_grpc.MessagingServiceServicer):
    async def Chat(self, req_iter, ctx):
        send_q: asyncio.Queue[pb.ServerEnvelope] = asyncio.Queue()
        user: str | None = None

        # -------- consumer: client → server --------
        async def consume():
            nonlocal user
            async for env in req_iter:
                match env.WhichOneof("payload"):

                    # 1) first frame must be Init ---------------------------------
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

                    # 2) channel join (exclusive) ---------------------------------
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

                    # 2b) explicit leave -> return to Main  -------------------
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


                    # 3) message to current channel -------------------------------
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

                    # 4) private message ------------------------------------------
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

        # -------- producer: server → client -------------
        try:
            while True:
                env = await send_q.get()
                yield env
        finally:
            consumer.cancel()
            if user: hub.logout(user)

    # helper: send last N lines of a channel
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

# ───────────────────────── bootstrap ──────────────────────────
async def serve():
    server = grpc.aio.server()
    pb_grpc.add_MessagingServiceServicer_to_server(Messaging(), server)
    server.add_insecure_port("[::]:50054")
    await server.start()
    print("messaging_service ready on :50054")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
