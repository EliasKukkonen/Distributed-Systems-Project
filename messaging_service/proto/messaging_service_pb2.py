# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: messaging_service.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'messaging_service.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x17messaging_service.proto\x12\tmessaging\"\x15\n\x04Init\x12\r\n\x05token\x18\x01 \x01(\t\"\x1b\n\x0bJoinChannel\x12\x0c\n\x04name\x18\x01 \x01(\t\"\x1c\n\x0cLeaveChannel\x12\x0c\n\x04name\x18\x01 \x01(\t\"-\n\nPrivateMsg\x12\x11\n\trecipient\x18\x01 \x01(\t\x12\x0c\n\x04\x62ody\x18\x02 \x01(\t\"+\n\nChannelMsg\x12\x0f\n\x07\x63hannel\x18\x01 \x01(\t\x12\x0c\n\x04\x62ody\x18\x02 \x01(\t\",\n\nHistoryReq\x12\x0f\n\x07\x63hannel\x18\x01 \x01(\t\x12\r\n\x05limit\x18\x02 \x01(\x05\"2\n\nHistoryRes\x12$\n\x05items\x18\x01 \x03(\x0b\x32\x15.messaging.ChannelMsg\"\x86\x02\n\x0e\x43lientEnvelope\x12\x1f\n\x04init\x18\x01 \x01(\x0b\x32\x0f.messaging.InitH\x00\x12&\n\x04join\x18\x02 \x01(\x0b\x32\x16.messaging.JoinChannelH\x00\x12(\n\x05leave\x18\x03 \x01(\x0b\x32\x17.messaging.LeaveChannelH\x00\x12#\n\x02pm\x18\x04 \x01(\x0b\x32\x15.messaging.PrivateMsgH\x00\x12#\n\x02\x63m\x18\x05 \x01(\x0b\x32\x15.messaging.ChannelMsgH\x00\x12,\n\x0bhistory_req\x18\x06 \x01(\x0b\x32\x15.messaging.HistoryReqH\x00\x42\t\n\x07payload\"\xa5\x01\n\x0eServerEnvelope\x12\x10\n\x06notice\x18\x01 \x01(\tH\x00\x12#\n\x02pm\x18\x02 \x01(\x0b\x32\x15.messaging.PrivateMsgH\x00\x12#\n\x02\x63m\x18\x03 \x01(\x0b\x32\x15.messaging.ChannelMsgH\x00\x12,\n\x0bhistory_res\x18\x04 \x01(\x0b\x32\x15.messaging.HistoryResH\x00\x42\t\n\x07payload2T\n\x10MessagingService\x12@\n\x04\x43hat\x12\x19.messaging.ClientEnvelope\x1a\x19.messaging.ServerEnvelope(\x01\x30\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'messaging_service_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_INIT']._serialized_start=38
  _globals['_INIT']._serialized_end=59
  _globals['_JOINCHANNEL']._serialized_start=61
  _globals['_JOINCHANNEL']._serialized_end=88
  _globals['_LEAVECHANNEL']._serialized_start=90
  _globals['_LEAVECHANNEL']._serialized_end=118
  _globals['_PRIVATEMSG']._serialized_start=120
  _globals['_PRIVATEMSG']._serialized_end=165
  _globals['_CHANNELMSG']._serialized_start=167
  _globals['_CHANNELMSG']._serialized_end=210
  _globals['_HISTORYREQ']._serialized_start=212
  _globals['_HISTORYREQ']._serialized_end=256
  _globals['_HISTORYRES']._serialized_start=258
  _globals['_HISTORYRES']._serialized_end=308
  _globals['_CLIENTENVELOPE']._serialized_start=311
  _globals['_CLIENTENVELOPE']._serialized_end=573
  _globals['_SERVERENVELOPE']._serialized_start=576
  _globals['_SERVERENVELOPE']._serialized_end=741
  _globals['_MESSAGINGSERVICE']._serialized_start=743
  _globals['_MESSAGINGSERVICE']._serialized_end=827
# @@protoc_insertion_point(module_scope)
