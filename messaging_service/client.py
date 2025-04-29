"""
CLI client for messaging_service
--------------------------------
• Connects to messaging_service gRPC server at localhost:50054.
• Supports joining channels, sending private messages, and quitting.
• Called by chat_service after user login.
"""

import os
import sys
import asyncio
import contextlib
import grpc
import jwt  

# Add path to find generated proto modules
PROTO_DIR = os.path.join(os.path.dirname(__file__), "proto")
sys.path.insert(0, PROTO_DIR)

import messaging_service_pb2 as pb
import messaging_service_pb2_grpc as pb_grpc


ADDR = os.getenv("MSG_ADDR", "localhost:50054")

# Private function to handle a chat session
async def _chat_session(token: str):
    """Runs a single interactive messaging session. Returns when the user types :quit."""
    async with grpc.aio.insecure_channel(ADDR) as channel:
        stub = pb_grpc.MessagingServiceStub(channel)
        stream = stub.Chat()

        # Send initial authentication frame
        await stream.write(pb.ClientEnvelope(init=pb.Init(token=token)))

        # Print available chat commands
        print(
        "\nMessaging service menu:\n"
        "1. Join or create a channel   (:join <channel>)\n"
        "2. Leave a channel            (:leave <channel>)\n"
        "3. Send a private message     (@<username> <message>)\n"
        "4. Exit messaging service     (:quit)\n"
        "Type a message and press enter to chat")

        # Sender coroutine: sends user input to server
        async def sender():
            loop = asyncio.get_event_loop()
            while True:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    continue
                text = line.rstrip("\n")

                if text == ":quit":
                    print("\nReturning to chat service...")
                    await stream.done_writing()  # Close sending side
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

        # Receiver coroutine: receives server updates
        async def receiver():
            try:
                async for srv in stream:
                    kind = srv.WhichOneof("payload")
                    if kind == "notice":
                        print(f"\n{srv.notice}")

                        # Re-show menu if it's a join or leave event
                        if any(phrase in srv.notice for phrase in [
                        "joined", "left", "returned", "You joined", "You returned"
                        ]):
                            print(
                            "\nMessaging service menu:\n"
                            "1. Join or create a channel   (:join <channel>)\n"
                            "2. Leave a channel            (:leave <channel>)\n"
                            "3. Send a private message     (@<username> <message>)\n"
                            "4. Exit messaging service     (:quit)\n"
                            "Type a message and press Enter to chat.\n")
                    elif kind == "cm":
                        print(f"[{srv.cm.channel}] {srv.cm.body}")
                    elif kind == "pm":
                        print(srv.pm.body)
                    elif kind == "history_res":
                        for msg in srv.history_res.items:
                            print(f"[history] [{msg.channel}] {msg.body}")
                        print()
            except grpc.aio.AioRpcError:
                pass # Server closed the stream

        recv_task = asyncio.create_task(receiver())
        await sender()            # blocks until :quit
        recv_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await recv_task       # Drain any pending work

# Public function to run the messaging UI
def run_messaging_ui(token: str):
    """Launch messaging UI; returns to caller when user types :quit or presses Ctrl-C."""
    try:
        asyncio.run(_chat_session(token))
    except KeyboardInterrupt:
        print("\nReturning to chat service...")
