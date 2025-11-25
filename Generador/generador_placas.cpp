#include <iostream>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <string>
#include <ctime>
#include <cstdlib>
#include <thread>
#include <chrono>
#include <sstream>
#include <vector>

#pragma comment(lib, "ws2_32.lib")

#define PORT 8080
#define SERVER_IP "127.0.0.1"

std::string crearPlacaAleatoria() {
    std::string letras = "";
    for(int i=0; i<3; ++i) letras += (char)('A' + rand()%26);
    int numeros = rand() % 1000;
    char buff[10];
    sprintf(buff, "%03d", numeros);
    return letras + std::string(buff);
}

void enviarDatos(std::string mensaje) {
    WSADATA wsaData;
    SOCKET sock = INVALID_SOCKET;
    struct sockaddr_in serv_addr;

    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) return;

    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) { WSACleanup(); return; }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);
    serv_addr.sin_addr.s_addr = inet_addr(SERVER_IP);

    if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
        // No imprimir error si falla la conexión, simplemente salir
        closesocket(sock);
        WSACleanup();
        return;
    }

    send(sock, mensaje.c_str(), (int)mensaje.length(), 0);
    
    // Shutdown correcto
    shutdown(sock, SD_SEND);
    closesocket(sock);
    WSACleanup();
}

std::string obtenerHora() {
    time_t now = time(0);
    tm *ltm = localtime(&now);
    char buffer[80];
    strftime(buffer, 80, "%H:%M:%S", ltm);
    return std::string(buffer);
}

int main() {
    srand((unsigned int)time(0));
    std::cout << "=== GENERADOR DE TRAFICO (CLIENTE) ===" << std::endl;
    std::cout << "Presiona Ctrl+C para detener." << std::endl;

    std::vector<std::string> bancoPlacas;
    for(int i = 0; i < 50; i++) bancoPlacas.push_back(crearPlacaAleatoria());

    int contador = 0;
    while (true) {
        // Enviar un carro cada 1 a 3 segundos (más rápido que antes para probar fluidez)
        int ms = 1000 + (rand() % 2000);
        std::this_thread::sleep_for(std::chrono::milliseconds(ms));

        int indicePlaca = rand() % 50;
        std::string placa = bancoPlacas[indicePlaca];
        std::string hora = obtenerHora();
        int celda = 1 + (rand() % 20); 

        std::stringstream ss;
        ss << placa << ";" << hora << ";" << celda;
        
        std::cout << "[" << ++contador << "] Enviando: " << placa << " a celda " << celda << std::endl;
        enviarDatos(ss.str());
    }
    return 0;
}