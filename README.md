# 🎵 AxMusic - Sistema Distribuido de Gestión Multimedia

Este proyecto es una solución integral de software desarrollada para las cátedras de **Redes de Computadoras**, **Programacion orientada a objetos** y **Arquitectura y Mantenimiento de Equipos**. AxMusic combina una aplicación de escritorio para la gestión de música con un servidor de streaming en la red local (LAN).

---

## 🚀 Características Principales

* **Interfaz de Escritorio (GUI):** Desarrollada en Python con `Tkinter`, permitiendo búsquedas, descargas y gestión de favoritos.
* **Servidor de Streaming (Capa 7):** Implementación de un servidor web con `Flask` para servir contenido multimedia vía HTTP a otros dispositivos.
* **Procesamiento de Señales:** Transcodificación automática de flujos de audio a formato MP3 mediante el uso de binarios de bajo nivel.
* **Persistencia de Datos:** Gestión de listas de reproducción y favoritos mediante archivos estructurados en formato `JSON`.

---

## 🛠️ Requisitos de Arquitectura y Sistema

Para el correcto funcionamiento del software en una estación de trabajo, se deben cumplir las siguientes dependencias:

1. **Python 3.10+** instalado en el sistema.
2. **Bibliotecas de Python:** ```bash
   pip install yt-dlp flask pygame requests

**Configuración de Red y Conectividad**
El sistema opera bajo una arquitectura Cliente-Servidor:
Direccionamiento: El servidor realiza el bind en el host 0.0.0.0, escuchando peticiones en todas las interfaces de red del host.
Puerto: El servicio está configurado en el puerto lógico 5000.
Acceso LAN: Para acceder desde otros dispositivos (celulares/tablets), utilice la dirección IP del host: http://[IP_DEL_HOST]:5000.
Simulación DNS: Se recomienda editar el archivo hosts del sistema operativo para mapear la IP a un dominio local (ej. www.axmusic.local).
Este proyecto demuestra el uso de procesamiento asíncrono (Threading) para no bloquear la CPU, la gestión de caché local para optimizar el ancho de banda, y el despliegue de servicios web en la capa de aplicación del modelo OSI.

**Estructura del Proyecto**
main.py: Lógica principal y orquestación de hilos (Multithreading).
/templates: Contiene el archivo index.html para la interfaz de streaming web.
/music_vault: Directorio de almacenamiento temporal y caché de red.
/playlists: Almacenamiento persistente de datos del usuario.
axmusic.png: Recurso gráfico para el Splash Screen de inicio.
