#include "server_module.h"
#include <iostream>
#include <cstring>
#include <sstream>

#pragma comment(lib, "ws2_32.lib")

// Constructor
ServerSocket::ServerSocket() : servidor_fd(INVALID_SOCKET) {
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "SERVER CRITICO: Fallo al inicializar Winsock." << std::endl;
        return;
    }

    servidor_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (servidor_fd == INVALID_SOCKET) {
        std::cerr << "SERVER CRITICO: Fallo en socket." << std::endl;
        WSACleanup();
        return;
    }

    // Configurar socket para reutilizar dirección (evita errores al reiniciar rápido)
    char opt = 1;
    setsockopt(servidor_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in direccion;
    direccion.sin_family = AF_INET;
    direccion.sin_addr.s_addr = INADDR_ANY;
    direccion.sin_port = htons(PORT);

    if (bind(servidor_fd, (struct sockaddr*)&direccion, sizeof(direccion)) == SOCKET_ERROR) {
        std::cerr << "SERVER CRITICO: Fallo en bind. Puerto tal vez ocupado." << std::endl;
        closesocket(servidor_fd);
        WSACleanup();
        return;
    }

    if (listen(servidor_fd, 5) == SOCKET_ERROR) {
        std::cerr << "SERVER CRITICO: Fallo en listen." << std::endl;
        closesocket(servidor_fd);
        WSACleanup();
        return;
    }

    std::cout << "Servidor C++ listo en puerto " << PORT << ". Esperando conexiones..." << std::endl;
}

// Destructor
ServerSocket::~ServerSocket() {
    if (servidor_fd != INVALID_SOCKET) {
        closesocket(servidor_fd);
    }
    WSACleanup();
}

// Método Bloqueante (Ahora seguro gracias a SWIG threads)
std::string ServerSocket::esperarMensaje() {
    if (servidor_fd == INVALID_SOCKET) {
        return "ERROR: Socket no inicializado.";
    }

    SOCKET nuevo_socket = INVALID_SOCKET;
    struct sockaddr_in cliente_direccion;
    int addrlen = sizeof(cliente_direccion);
    char buffer[1024] = {0};

    // Al tener threads="1" en SWIG, este accept ya no congelará la GUI de Python
    nuevo_socket = accept(servidor_fd, (struct sockaddr*)&cliente_direccion, &addrlen);
    
    if (nuevo_socket == INVALID_SOCKET) {
        // Retornar vacio o error leve para que el loop intente de nuevo
        return "ERROR_ACCEPT";
    }

    int valread = recv(nuevo_socket, buffer, 1024, 0);
    
    // Cerrar socket cliente inmediatamente tras recibir
    shutdown(nuevo_socket, SD_BOTH);
    closesocket(nuevo_socket);

    if (valread > 0) {
        return std::string(buffer, valread);
    } else {
        return "ERROR_NODATA";
    }
}