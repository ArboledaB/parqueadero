# **🚗 Sistema de Gestión de Parqueadero Asíncrono (C++ & Python)**

Este proyecto implementa un sistema distribuido para la gestión de un parqueadero de 20 celdas. Utiliza comunicación **TCP/IP Sockets** para desacoplar la generación de tráfico (Cliente C++) de la lógica de negocio y visualización (Servidor Python/Tkinter).

## **💡 Arquitectura y Concurrencia (La Solución Asíncrona)**

El desafío principal fue evitar que la recepción de datos de red, una operación **bloqueante** (accept() en C++), congelara la interfaz gráfica de Tkinter (Python). La solución se basa en una arquitectura de Múltiples Hilos y el uso de **SWIG** para interactuar de forma segura.

### **1\. Desacoplamiento de Hilos y Liberación del GIL**

El sistema opera con dos hilos principales para asegurar la fluidez de la GUI:

| Componente | Hilo de Ejecución | Rol | Bloqueo |
| :---- | :---- | :---- | :---- |
| **ParqueaderoApp (GUI)** | Hilo Principal (Tkinter) | Pinta la interfaz y extrae datos de la cola. | **NO se bloquea.** |
| **escuchar\_datos\_loop** | Hilo Secundario (threading.Thread) | Llama al código C++ para esperar datos. | **SÍ se bloquea** (espera de red). |

La clave es el archivo server\_module.i de SWIG, que incluye la directiva %module(threads="1"). Esto indica que mientras la función C++ ServerSocket::esperarMensaje() está bloqueada esperando una conexión, debe **liberar el GIL (Global Interpreter Lock)** de Python, permitiendo al Hilo Principal de Tkinter seguir ejecutándose.

### **2\. Flujo Asíncrono de Datos (Cola FIFO)**

La comunicación entre el hilo de red y el hilo de la GUI se realiza de forma segura a través de una **Cola FIFO** (queue.Queue):

1. **Recepción (Hilo Secundario)**: El hilo de red recibe el mensaje de C++ y lo coloca inmediatamente en la cola (cola\_mensajes.put(datos)).  
2. **Procesamiento (Hilo Principal)**: El método verificar\_cola (ejecutado por self.root.after(100, ...) cada 100ms) extrae los datos de la cola de forma no bloqueante (cola\_mensajes.get\_nowait()) y ejecuta la lógica de negocio.

Esto garantiza que las manipulaciones de la GUI siempre se realicen en el Hilo Principal de Tkinter, evitando errores de concurrencia y congelamientos.

## **🛠️ Estructura del Proyecto**

La estructura de carpetas se organiza para facilitar la compilación y ejecución de cada componente:

ProyectoParqueadero/  
├── Generador/  
│   └── generador\_placas.cpp   \<-- Cliente C++ (generador.exe)  
├── LibreriaServer/  
│   ├── server\_module.h        \<-- Definición de la clase ServerSocket  
│   ├── server\_module.cpp      \<-- Lógica del socket (bind, listen, accept, recv)  
│   └── server\_module.i        \<-- Interfaz SWIG con directiva threads="1"  
├── Visualizador/  
│   └── visualizador.py        \<-- Servidor Lógico, Manejo de Hilos y Tkinter GUI  
├── DIAGRAMA\_UML.PNG           \<-- Diagrama de Clases UML del proyecto  
├── build.bat                  \<-- Script de Compilación (Windows/MSVC/SWIG)  
└── clean.bat                  \<-- Script de Limpieza

## **⚙️ Instrucciones de Compilación y Ejecución (Windows)**

**Requisitos Previos:**

1. **Visual Studio 2022:** Para acceder al compilador cl (necesario para MSVC).  
2. **SWIG:** Debe estar instalado y accesible en la variable de entorno PATH.  
3. **Python 3.13:** Asegúrese de que las rutas de inclusión y librería en el script build.bat sean correctas.

### **1\. Consola de Desarrollo**

Todos los comandos deben ejecutarse desde la consola **x64 Native Tools Command Prompt for VS 2022**.

### **2\. Proceso de Compilación**

Ejecute los scripts desde la carpeta raíz del proyecto:

\# Limpiar compilaciones anteriores (opcional pero recomendado)  
clean.bat

\# Compilar Generador y Librería SWIG  
build.bat

**Archivos Generados:**

* Generador/generador.exe (Cliente C++).  
* LibreriaServer/\_server\_module.pyd (Módulo binario C++ de Python).  
* LibreriaServer/server\_module.py (Wrapper de Python generado por SWIG).

### **3\. Ejecución (Dos Terminales Simultáneas)**

**TERMINAL 1: Servidor Python (GUI)**

cd Visualizador  
python visualizador.py

El servidor inicia en el puerto 8080 y la GUI comienza a escuchar.

**TERMINAL 2: Cliente C++ (Generador)**

cd Generador  
generador.exe

El cliente empieza a simular tráfico, enviando paquetes al servidor.

## **📊 Lógica de Negocio y Flujo de Datos**

El generador C++ envía mensajes estructurados que la aplicación Python procesa para determinar si se trata de una entrada o una salida.

### **Formato del Mensaje**

El mensaje enviado es una cadena de texto con el formato: PLACA;HORA;CELDA

**Ejemplo:** ABC-123;14:35:01;10

### **Lógica de Parqueadero (ParqueaderoApp.procesar\_logica)**

La aplicación Python usa el diccionario self.ocupacion ({ "CELDA": "PLACA" }) para mantener el estado:

| Condición del Mensaje Entrante | Tipo de Tráfico | Acción Lógica y GUI |
| :---- | :---- | :---- |
| **Placa Existente** (placa\_entrante está en self.ocupacion ) | **SALIDA** | Se elimina la entrada, la celda se actualiza a **LIBRE** (verde). |
| **Placa Nueva** y **Celda Sugerida LIBRE** | **ENTRADA** | Se añade la entrada al diccionario y la celda se actualiza a **OCUPADO** (rojo). |
| **Placa Nueva** y **Celda Sugerida OCUPADA** | **RECHAZO** | Se registra en el log, no hay cambios en el estado del parqueadero. |

