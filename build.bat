@echo off
REM Este script debe ejecutarse desde el 'x64 Native Tools Command Prompt for VS 2022'.

REM --- Definición de Rutas Clave (No modificar) ---
set PROJECT_ROOT=%~dp0

REM Rutas de Python 3.13 (Confirmadas en el paso anterior)
set PYTHON_INCLUDE="C:\Users\USUARIO\AppData\Local\Programs\Python\Python313\include"
set PYTHON_LIB="C:\Users\USUARIO\AppData\Local\Programs\Python\Python313\libs\python313.lib"

echo.
echo =========================================================
echo  INICIANDO COMPILACION COMPLETA DEL PROYECTO PARQUEADERO
echo  (MSVC, SWIG, Python 3.13)
echo =========================================================

REM ----------------------------------------------------------------------
REM 1. COMPILAR EL GENERADOR (CLIENTE C++)
REM ----------------------------------------------------------------------
echo.
echo [PASO 1/2] Compilando Generador (Client C++)...
cd "%PROJECT_ROOT%Generador"
REM cl /EHsc compila el codigo, /link ws2_32.lib enlaza la libreria de sockets
cl /EHsc generador_placas.cpp /link ws2_32.lib /out:generador.exe
if errorlevel 1 goto :error
echo Generador compilado exitosamente: generador.exe

REM ----------------------------------------------------------------------
REM 2. COMPILAR LIBRERIA SERVER (C++ -> SWIG -> PYTHON .PYD)
REM ----------------------------------------------------------------------
echo.
echo [PASO 2/2] Compilando Libreria Server (SWIG/Python)...
cd "%PROJECT_ROOT%LibreriaServer"

REM 2a. Generar el wrapper con SWIG
echo   > Ejecutando SWIG...
swig -c++ -python server_module.i
if errorlevel 1 goto :error

REM 2b. Compilar el código principal C++
echo   > Compilando server_module.cpp (Objeto)...
cl /c /EHsc server_module.cpp
if errorlevel 1 goto :error

REM 2c. Compilar el wrapper C++ (Usando include de Python)
echo   > Compilando wrapper de SWIG (Objeto)...
cl /c /EHsc /I%PYTHON_INCLUDE% server_module_wrap.cxx
if errorlevel 1 goto :error

REM 2d. Enlazar todo para crear la DLL de Python (_server_module.pyd)
echo   > Enlazando a _server_module.pyd...
link /DLL /OUT:_server_module.pyd server_module.obj server_module_wrap.obj ws2_32.lib %PYTHON_LIB%
if errorlevel 1 goto :error

echo Libreria Server compilada exitosamente: _server_module.pyd

REM ----------------------------------------------------------------------
REM 3. FINALIZACIÓN EXITOSA
REM ----------------------------------------------------------------------
echo.
echo =========================================================
echo  COMPILACION FINALIZADA CON EXITO!
echo =========================================================
echo Para ejecutar: 
echo 1. Abrir una terminal en Visualizador/ y correr: python visualizador.py
echo 2. Abrir otra terminal en Generador/ y correr: generador.exe
goto :eof

REM ----------------------------------------------------------------------
REM MANEJO DE ERRORES
REM ----------------------------------------------------------------------
:error
echo.
echo =========================================================
echo  [ERROR] - FALLO EN LA COMPILACION
echo  Revise los mensajes de error anteriores.
echo =========================================================
pause