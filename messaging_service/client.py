"""
CLI client for messaging_service
--------------------------------
• Talks to the gRPC server on MSG_ADDR (default localhost:50054).
• Supports :join, :leave, @nickname, :quit.
• Exposes run_messaging_ui(token) so chat_service can launch it from a sync menu.
"""

import os
import sys
import asyncio
import contextlib
import grpc
import jwt  


PROTO_DIR = os.path.join(os.path.dirname(__file__), "proto")
sys.path.insert(0, PROTO_DIR)

import messaging_service_pb2 as pb
import messaging_service_pb2_grpc as pb_grpc


ADDR = os.getenv("MSG_ADDR", "localhost:50054")


async def _chat_session(token: str):
    """Runs a single interactive messaging session. Returns when the user types :quit."""
    async with grpc.aio.insecure_channel(ADDR) as channel:
        stub = pb_grpc.MessagingServiceStub(channel)
        stream = stub.Chat()

        await stream.write(pb.ClientEnvelope(init=pb.Init(token=token)))


        async def sender():
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    continue
                text = line.rstrip("\n")

                if text == ":quit":
                    print("* Leaving messaging UI …")
                    await stream.done_writing()  # half-close the stream
                    break
                elif text.startswith(":join "):
                    await stream.write(pb.ClientEnvelope(
                        join=pb.JoinChannel(name=text.split(" ", 1)[1])))
                elif text.startswith(":leave "):
                    await stream.write(pb.ClientEnvelope(
                        leave=pb.LeaveChannel(name=text.split(" ", 1)[1])))
                elif text.startswith("@"):
                    nick, body = text[1:].split(" ", 1)
                    await stream.write(pb.ClientEnvelope(
                        pm=pb.PrivateMsg(recipient=nick, body=body)))
                else:
                    # channel="" means “current active channel”
                    await stream.write(pb.ClientEnvelope(
                        cm=pb.ChannelMsg(channel="", body=text)))

        async def receiver():
            try:
                async for srv in stream:
                    kind = srv.WhichOneof("payload")
                    if kind == "notice":
                        print(f"* {srv.notice}")
                    elif kind == "cm":
                        print(f"[{srv.cm.channel}] {srv.cm.body}")
                    elif kind == "pm":
                        print(srv.pm.body)
                    elif kind == "history_res":
                        for msg in srv.history_res.items:
                            print(f"[history {msg.channel}] {msg.body}")
            except grpc.aio.AioRpcError:
                # Stream closed by the other side – just exit receiver.
                pass

        recv_task = asyncio.create_task(receiver())
        await sender()            # blocks until :quit
        recv_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await recv_task       # drain cancellation



def run_messaging_ui(token: str):
    """Launch messaging UI; returns to caller when user types :quit or presses Ctrl-C."""
    try:
        asyncio.run(_chat_session(token))
    except KeyboardInterrupt:
        print("\n* Messaging session interrupted.")
