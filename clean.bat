@echo off
set PROJECT_ROOT=%~dp0
echo.
echo =========================================================
echo  INICIANDO LIMPIEZA TOTAL DEL PROYECTO PARQUEADERO
echo  Borrando archivos compilados, objetos y wrappers de SWIG.
echo =========================================================

REM --- LIMPIEZA DEL GENERADOR (CLIENTE C++) ---
echo.
echo [1] Limpiando carpeta Generador...
del "%PROJECT_ROOT%Generador\generador.exe" 2>nul
del "%PROJECT_ROOT%Generador\*.obj" 2>nul
del "%PROJECT_ROOT%Generador\*.pdb" 2>nul
del "%PROJECT_ROOT%Generador\*.ilk" 2>nul

REM --- LIMPIEZA DE LA LIBRERÍA (SERVER/SWIG) ---
echo.
echo [2] Limpiando carpeta LibreriaServer (SWIG, PYD, Objetos)...
del "%PROJECT_ROOT%LibreriaServer\_server_module.pyd" 2>nul
del "%PROJECT_ROOT%LibreriaServer\server_module.py" 2>nul
del "%PROJECT_ROOT%LibreriaServer\server_module_wrap.cxx" 2>nul
del "%PROJECT_ROOT%LibreriaServer\*.obj" 2>nul
del "%PROJECT_ROOT%LibreriaServer\*.pdb" 2>nul
del "%PROJECT_ROOT%LibreriaServer\*.ilk" 2>nul

REM --- LIMPIEZA DE CACHÉ DE PYTHON ---
echo.
echo [3] Eliminando cache de Python (si existe)...
RD /S /Q "%PROJECT_ROOT%Visualizador\__pycache__" 2>nul
RD /S /Q "%PROJECT_ROOT%LibreriaServer\__pycache__" 2>nul

echo.
echo =========================================================
echo  LIMPIEZA FINALIZADA!
echo  El proyecto está listo para una nueva compilacion.
echo =========================================================
pause