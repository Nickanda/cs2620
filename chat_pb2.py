# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: chat.proto
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
    'chat.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nchat.proto\x12\x04\x63hat\":\n\x14\x43reateAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"8\n\x15\x43reateAccountResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"K\n\rLoginResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x19\n\x11undelivered_count\x18\x03 \x01(\x05\"!\n\rLogoutRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"1\n\x0eLogoutResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"G\n\x12SendMessageRequest\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x10\n\x08receiver\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\"P\n\x13SendMessageResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x18\n\x10undeliv_messages\x18\x03 \x01(\x05\"?\n\x15GetUndeliveredRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x14\n\x0cnum_messages\x18\x02 \x01(\x05\"6\n\x07Message\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0e\n\x06sender\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\"Z\n\x16GetUndeliveredResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x1f\n\x08messages\x18\x03 \x03(\x0b\x32\r.chat.Message\"=\n\x13GetDeliveredRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x14\n\x0cnum_messages\x18\x02 \x01(\x05\"X\n\x14GetDeliveredResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x1f\n\x08messages\x18\x03 \x03(\x0b\x32\r.chat.Message\"(\n\x14\x44\x65leteAccountRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"8\n\x15\x44\x65leteAccountResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"%\n\x12SearchUsersRequest\x12\x0f\n\x07pattern\x18\x01 \x01(\t\"4\n\x13SearchUsersResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\r\n\x05users\x18\x02 \x03(\t\"=\n\x14\x44\x65leteMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x13\n\x0bmessage_ids\x18\x02 \x03(\x05\"R\n\x15\x44\x65leteMessageResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x18\n\x10undeliv_messages\x18\x03 \x01(\x05\"&\n\x12RefreshHomeRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"P\n\x13RefreshHomeResponse\x12\x0e\n\x06status\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x18\n\x10undeliv_messages\x18\x03 \x01(\x05\x32\xb2\x05\n\x0b\x43hatService\x12H\n\rCreateAccount\x12\x1a.chat.CreateAccountRequest\x1a\x1b.chat.CreateAccountResponse\x12\x30\n\x05Login\x12\x12.chat.LoginRequest\x1a\x13.chat.LoginResponse\x12\x33\n\x06Logout\x12\x13.chat.LogoutRequest\x1a\x14.chat.LogoutResponse\x12\x42\n\x0bSendMessage\x12\x18.chat.SendMessageRequest\x1a\x19.chat.SendMessageResponse\x12K\n\x0eGetUndelivered\x12\x1b.chat.GetUndeliveredRequest\x1a\x1c.chat.GetUndeliveredResponse\x12\x45\n\x0cGetDelivered\x12\x19.chat.GetDeliveredRequest\x1a\x1a.chat.GetDeliveredResponse\x12H\n\rDeleteAccount\x12\x1a.chat.DeleteAccountRequest\x1a\x1b.chat.DeleteAccountResponse\x12\x42\n\x0bSearchUsers\x12\x18.chat.SearchUsersRequest\x1a\x19.chat.SearchUsersResponse\x12H\n\rDeleteMessage\x12\x1a.chat.DeleteMessageRequest\x1a\x1b.chat.DeleteMessageResponse\x12\x42\n\x0bRefreshHome\x12\x18.chat.RefreshHomeRequest\x1a\x19.chat.RefreshHomeResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_CREATEACCOUNTREQUEST']._serialized_start=20
  _globals['_CREATEACCOUNTREQUEST']._serialized_end=78
  _globals['_CREATEACCOUNTRESPONSE']._serialized_start=80
  _globals['_CREATEACCOUNTRESPONSE']._serialized_end=136
  _globals['_LOGINREQUEST']._serialized_start=138
  _globals['_LOGINREQUEST']._serialized_end=188
  _globals['_LOGINRESPONSE']._serialized_start=190
  _globals['_LOGINRESPONSE']._serialized_end=265
  _globals['_LOGOUTREQUEST']._serialized_start=267
  _globals['_LOGOUTREQUEST']._serialized_end=300
  _globals['_LOGOUTRESPONSE']._serialized_start=302
  _globals['_LOGOUTRESPONSE']._serialized_end=351
  _globals['_SENDMESSAGEREQUEST']._serialized_start=353
  _globals['_SENDMESSAGEREQUEST']._serialized_end=424
  _globals['_SENDMESSAGERESPONSE']._serialized_start=426
  _globals['_SENDMESSAGERESPONSE']._serialized_end=506
  _globals['_GETUNDELIVEREDREQUEST']._serialized_start=508
  _globals['_GETUNDELIVEREDREQUEST']._serialized_end=571
  _globals['_MESSAGE']._serialized_start=573
  _globals['_MESSAGE']._serialized_end=627
  _globals['_GETUNDELIVEREDRESPONSE']._serialized_start=629
  _globals['_GETUNDELIVEREDRESPONSE']._serialized_end=719
  _globals['_GETDELIVEREDREQUEST']._serialized_start=721
  _globals['_GETDELIVEREDREQUEST']._serialized_end=782
  _globals['_GETDELIVEREDRESPONSE']._serialized_start=784
  _globals['_GETDELIVEREDRESPONSE']._serialized_end=872
  _globals['_DELETEACCOUNTREQUEST']._serialized_start=874
  _globals['_DELETEACCOUNTREQUEST']._serialized_end=914
  _globals['_DELETEACCOUNTRESPONSE']._serialized_start=916
  _globals['_DELETEACCOUNTRESPONSE']._serialized_end=972
  _globals['_SEARCHUSERSREQUEST']._serialized_start=974
  _globals['_SEARCHUSERSREQUEST']._serialized_end=1011
  _globals['_SEARCHUSERSRESPONSE']._serialized_start=1013
  _globals['_SEARCHUSERSRESPONSE']._serialized_end=1065
  _globals['_DELETEMESSAGEREQUEST']._serialized_start=1067
  _globals['_DELETEMESSAGEREQUEST']._serialized_end=1128
  _globals['_DELETEMESSAGERESPONSE']._serialized_start=1130
  _globals['_DELETEMESSAGERESPONSE']._serialized_end=1212
  _globals['_REFRESHHOMEREQUEST']._serialized_start=1214
  _globals['_REFRESHHOMEREQUEST']._serialized_end=1252
  _globals['_REFRESHHOMERESPONSE']._serialized_start=1254
  _globals['_REFRESHHOMERESPONSE']._serialized_end=1334
  _globals['_CHATSERVICE']._serialized_start=1337
  _globals['_CHATSERVICE']._serialized_end=2027
# @@protoc_insertion_point(module_scope)
