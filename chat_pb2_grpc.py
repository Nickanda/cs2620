# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings

import chat_pb2 as chat__pb2

GRPC_GENERATED_VERSION = '1.70.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in chat_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class ChatServiceStub(object):
    """Service definition: all RPC methods for the chat application.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateAccount = channel.unary_unary(
                '/chat.ChatService/CreateAccount',
                request_serializer=chat__pb2.CreateAccountRequest.SerializeToString,
                response_deserializer=chat__pb2.CreateAccountResponse.FromString,
                _registered_method=True)
        self.Login = channel.unary_unary(
                '/chat.ChatService/Login',
                request_serializer=chat__pb2.LoginRequest.SerializeToString,
                response_deserializer=chat__pb2.LoginResponse.FromString,
                _registered_method=True)
        self.Logout = channel.unary_unary(
                '/chat.ChatService/Logout',
                request_serializer=chat__pb2.LogoutRequest.SerializeToString,
                response_deserializer=chat__pb2.LogoutResponse.FromString,
                _registered_method=True)
        self.SendMessage = channel.unary_unary(
                '/chat.ChatService/SendMessage',
                request_serializer=chat__pb2.SendMessageRequest.SerializeToString,
                response_deserializer=chat__pb2.SendMessageResponse.FromString,
                _registered_method=True)
        self.GetUndelivered = channel.unary_unary(
                '/chat.ChatService/GetUndelivered',
                request_serializer=chat__pb2.GetUndeliveredRequest.SerializeToString,
                response_deserializer=chat__pb2.GetUndeliveredResponse.FromString,
                _registered_method=True)
        self.GetDelivered = channel.unary_unary(
                '/chat.ChatService/GetDelivered',
                request_serializer=chat__pb2.GetDeliveredRequest.SerializeToString,
                response_deserializer=chat__pb2.GetDeliveredResponse.FromString,
                _registered_method=True)
        self.DeleteAccount = channel.unary_unary(
                '/chat.ChatService/DeleteAccount',
                request_serializer=chat__pb2.DeleteAccountRequest.SerializeToString,
                response_deserializer=chat__pb2.DeleteAccountResponse.FromString,
                _registered_method=True)
        self.SearchUsers = channel.unary_unary(
                '/chat.ChatService/SearchUsers',
                request_serializer=chat__pb2.SearchUsersRequest.SerializeToString,
                response_deserializer=chat__pb2.SearchUsersResponse.FromString,
                _registered_method=True)
        self.DeleteMessage = channel.unary_unary(
                '/chat.ChatService/DeleteMessage',
                request_serializer=chat__pb2.DeleteMessageRequest.SerializeToString,
                response_deserializer=chat__pb2.DeleteMessageResponse.FromString,
                _registered_method=True)
        self.RefreshHome = channel.unary_unary(
                '/chat.ChatService/RefreshHome',
                request_serializer=chat__pb2.RefreshHomeRequest.SerializeToString,
                response_deserializer=chat__pb2.RefreshHomeResponse.FromString,
                _registered_method=True)


class ChatServiceServicer(object):
    """Service definition: all RPC methods for the chat application.
    """

    def CreateAccount(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Login(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Logout(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendMessage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetUndelivered(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetDelivered(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteAccount(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SearchUsers(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteMessage(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RefreshHome(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ChatServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CreateAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateAccount,
                    request_deserializer=chat__pb2.CreateAccountRequest.FromString,
                    response_serializer=chat__pb2.CreateAccountResponse.SerializeToString,
            ),
            'Login': grpc.unary_unary_rpc_method_handler(
                    servicer.Login,
                    request_deserializer=chat__pb2.LoginRequest.FromString,
                    response_serializer=chat__pb2.LoginResponse.SerializeToString,
            ),
            'Logout': grpc.unary_unary_rpc_method_handler(
                    servicer.Logout,
                    request_deserializer=chat__pb2.LogoutRequest.FromString,
                    response_serializer=chat__pb2.LogoutResponse.SerializeToString,
            ),
            'SendMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.SendMessage,
                    request_deserializer=chat__pb2.SendMessageRequest.FromString,
                    response_serializer=chat__pb2.SendMessageResponse.SerializeToString,
            ),
            'GetUndelivered': grpc.unary_unary_rpc_method_handler(
                    servicer.GetUndelivered,
                    request_deserializer=chat__pb2.GetUndeliveredRequest.FromString,
                    response_serializer=chat__pb2.GetUndeliveredResponse.SerializeToString,
            ),
            'GetDelivered': grpc.unary_unary_rpc_method_handler(
                    servicer.GetDelivered,
                    request_deserializer=chat__pb2.GetDeliveredRequest.FromString,
                    response_serializer=chat__pb2.GetDeliveredResponse.SerializeToString,
            ),
            'DeleteAccount': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteAccount,
                    request_deserializer=chat__pb2.DeleteAccountRequest.FromString,
                    response_serializer=chat__pb2.DeleteAccountResponse.SerializeToString,
            ),
            'SearchUsers': grpc.unary_unary_rpc_method_handler(
                    servicer.SearchUsers,
                    request_deserializer=chat__pb2.SearchUsersRequest.FromString,
                    response_serializer=chat__pb2.SearchUsersResponse.SerializeToString,
            ),
            'DeleteMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteMessage,
                    request_deserializer=chat__pb2.DeleteMessageRequest.FromString,
                    response_serializer=chat__pb2.DeleteMessageResponse.SerializeToString,
            ),
            'RefreshHome': grpc.unary_unary_rpc_method_handler(
                    servicer.RefreshHome,
                    request_deserializer=chat__pb2.RefreshHomeRequest.FromString,
                    response_serializer=chat__pb2.RefreshHomeResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'chat.ChatService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('chat.ChatService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class ChatService(object):
    """Service definition: all RPC methods for the chat application.
    """

    @staticmethod
    def CreateAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/CreateAccount',
            chat__pb2.CreateAccountRequest.SerializeToString,
            chat__pb2.CreateAccountResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Login(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/Login',
            chat__pb2.LoginRequest.SerializeToString,
            chat__pb2.LoginResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Logout(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/Logout',
            chat__pb2.LogoutRequest.SerializeToString,
            chat__pb2.LogoutResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SendMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/SendMessage',
            chat__pb2.SendMessageRequest.SerializeToString,
            chat__pb2.SendMessageResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetUndelivered(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/GetUndelivered',
            chat__pb2.GetUndeliveredRequest.SerializeToString,
            chat__pb2.GetUndeliveredResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetDelivered(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/GetDelivered',
            chat__pb2.GetDeliveredRequest.SerializeToString,
            chat__pb2.GetDeliveredResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DeleteAccount(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/DeleteAccount',
            chat__pb2.DeleteAccountRequest.SerializeToString,
            chat__pb2.DeleteAccountResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def SearchUsers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/SearchUsers',
            chat__pb2.SearchUsersRequest.SerializeToString,
            chat__pb2.SearchUsersResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def DeleteMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/DeleteMessage',
            chat__pb2.DeleteMessageRequest.SerializeToString,
            chat__pb2.DeleteMessageResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def RefreshHome(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/chat.ChatService/RefreshHome',
            chat__pb2.RefreshHomeRequest.SerializeToString,
            chat__pb2.RefreshHomeResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
