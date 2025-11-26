import sys
import os
import threading
import queue # Importante para la comunicación segura entre hilos
import tkinter as tk
from tkinter import ttk

# --- Importación de la librería C++ ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'LibreriaServer')))
try:
    import server_module
except ImportError:
    print("Error crítico: No se encuentra 'server_module'. Asegúrate de compilar con SWIG.")
    sys.exit(1)

class ParqueaderoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestión de Parqueadero - Arquitectura Cliente/Servidor")
        self.root.geometry("900x650")
        self.root.configure(bg="#f0f0f0")

        # Cola de mensajes para desacoplar Red de GUI
        self.cola_mensajes = queue.Queue()

        # Diccionario lógico: { "CELDA": "PLACA" }
        self.ocupacion = {} 

        # Interfaz Gráfica
        self.crear_interfaz()
        
        # 1. Inicializar servidor C++
        self.servidor = server_module.ServerSocket()
        
        # 2. Hilo de escucha (Daemon para que cierre al cerrar la ventana)
        self.hilo_escucha = threading.Thread(target=self.escuchar_datos_loop, daemon=True)
        self.hilo_escucha.start()

        # 3. Iniciar el loop de lectura de la cola en el hilo principal
        self.verificar_cola()

    def crear_interfaz(self):
        # Título
        lbl_titulo = tk.Label(self.root, text="Monitor de Parqueadero (20 Celdas)", 
                              font=("Segoe UI", 18, "bold"), bg="#f0f0f0", fg="#333")
        lbl_titulo.pack(pady=15)

        # Contenedor principal centrado
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(expand=True, fill="both", padx=20)

        # Frame para la cuadrícula
        frame_grid = tk.Frame(main_frame, bg="#d9d9d9", padx=5, pady=5, relief="sunken", bd=1)
        frame_grid.pack()

        self.celdas_gui = {}

        # Crear matriz 4x5 (20 celdas)
        celda_num = 1
        for fila in range(4):
            for col in range(5):
                # Marco de cada celda
                f = tk.Frame(frame_grid, borderwidth=1, relief="raised", width=140, height=90, bg="white")
                f.grid(row=fila, column=col, padx=4, pady=4)
                f.pack_propagate(False)

                # Cabecera celda
                header_frame = tk.Frame(f, bg="#e0e0e0", height=20)
                header_frame.pack(fill="x", side="top")
                lbl_num = tk.Label(header_frame, text=f"Celda {celda_num}", font=("Arial", 8, "bold"), bg="#e0e0e0", fg="#555")
                lbl_num.pack()

                # Estado/Placa
                lbl_estado = tk.Label(f, text="LIBRE", font=("Arial", 12, "bold"), bg="#90ee90", fg="#004d00")
                lbl_estado.pack(expand=True, fill="both")
                
                self.celdas_gui[str(celda_num)] = lbl_estado
                celda_num += 1

        # Log de eventos
        lbl_log = tk.Label(main_frame, text="Registro de Eventos:", bg="#f0f0f0", font=("Arial", 10, "bold"), anchor="w")
        lbl_log.pack(fill="x", pady=(15, 5))

        self.log_text = tk.Text(main_frame, height=8, state="disabled", font=("Consolas", 9))
        self.log_text.pack(fill="x")
        
        # Scrollbar para el log
        scrollbar = tk.Scrollbar(self.log_text, command=self.log_text.yview)
        self.log_text['yscrollcommand'] = scrollbar.set

    def log(self, mensaje):
        self.log_text.config(state="normal")
        self.log_text.insert("1.0", mensaje + "\n")
        self.log_text.config(state="disabled")

    def actualizar_gui_celda(self, celda, placa, estado):
        """ Actualiza visualmente una celda """
        if celda not in self.celdas_gui:
            return

        lbl = self.celdas_gui[celda]
        if estado == "OCUPADO":
            lbl.config(text=f"{placa}\nOcupado", bg="#ff6b6b", fg="white") # Rojo
        elif estado == "LIBRE":
            lbl.config(text="LIBRE", bg="#90ee90", fg="#004d00") # Verde

    def procesar_logica(self, datos):
        """ Procesa los datos recibidos (Lógica de Negocio) """
        try:
            if ";" not in datos: return
            
            partes = datos.split(';')
            if len(partes) < 3: return

            placa_entrante = partes[0]
            hora = partes[1]
            celda_sugerida = partes[2] 

            # Verificar si la placa ya está en alguna celda (Salida)
            celda_ocupada_por_placa = None
            for c, p in self.ocupacion.items():
                if p == placa_entrante:
                    celda_ocupada_por_placa = c
                    break
            
            if celda_ocupada_por_placa:
                # --- LÓGICA DE SALIDA ---
                del self.ocupacion[celda_ocupada_por_placa]
                self.actualizar_gui_celda(celda_ocupada_por_placa, "", "LIBRE")
                self.log(f"⬅ [{hora}] SALIDA: {placa_entrante} salió de Celda {celda_ocupada_por_placa}.")
            else:
                # --- LÓGICA DE ENTRADA ---
                if celda_sugerida in self.ocupacion:
                    placa_existente = self.ocupacion[celda_sugerida]
                    self.log(f"⚠ [{hora}] RECHAZADO: {placa_entrante} intentó Celda {celda_sugerida} (Ocupada por {placa_existente}).")
                else:
                    self.ocupacion[celda_sugerida] = placa_entrante
                    self.actualizar_gui_celda(celda_sugerida, placa_entrante, "OCUPADO")
                    self.log(f"➡ [{hora}] ENTRADA: {placa_entrante} ocupó Celda {celda_sugerida}.")

        except Exception as e:
            print(f"Error procesando lógica: {e}")

    def escuchar_datos_loop(self):
        """ Este bucle corre en segundo plano y NO toca la GUI directamente """
        while True:
            # Esta llamada a C++ bloquearía la GUI si no tuvieramos threads="1" en SWIG
            datos = self.servidor.esperarMensaje() 
            
            if datos and "ERROR" not in datos:
                # En lugar de procesar, ponemos en la cola
                self.cola_mensajes.put(datos)

    def verificar_cola(self):
        """ El hilo principal revisa la cola cada 100ms """
        try:
            # Procesamos todos los mensajes pendientes (batch processing)
            while True:
                datos = self.cola_mensajes.get_nowait()
                self.procesar_logica(datos)
        except queue.Empty:
            pass
        
        # Volver a programar la revisión
        self.root.after(100, self.verificar_cola)

if __name__ == "__main__":
    root = tk.Tk()
    app = ParqueaderoApp(root)
    root.mainloop()