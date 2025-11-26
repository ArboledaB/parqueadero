#pragma once
#include <string>
#include <winsock2.h>
#include <ws2tcpip.h>

#define PORT 8080

class ServerSocket {
private:
    WSADATA wsaData;
    SOCKET servidor_fd;

public:
    ServerSocket(); 
    ~ServerSocket();
    std::string esperarMensaje();
};