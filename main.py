import tkinter as tk
from tkinter import filedialog, messagebox
import pygame
import os
import yt_dlp
import threading
import json
import re
from flask import Flask, render_template, send_file
# Los demás (tkinter, os, pygame, etc.) se quedan igual

# ================= CONFIG =================
pygame.mixer.init()

DOWNLOAD_FOLDER = "music_vault"
PLAYLIST_FOLDER = "playlists"
FAV_FILE = "favoritos.json"
RECENT_FILE = "recientes.json"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(PLAYLIST_FOLDER, exist_ok=True)

playlist = []
indice_actual = 0

# ================= COLORES =================
BG = "#03045e"
CARD = "#0077b6"
HOVER = "#00b4d8"
TEXT = "#caf0f8"

# ================= FUNCIONES =================
def limpiar_texto(texto):
    return re.sub(r'[^a-zA-Z0-9 ]', '', texto).lower()
def guardar_reciente(nombre, ruta):
    data = {"nombre": nombre, "ruta": ruta}

    recientes = []

    if os.path.exists(RECENT_FILE):
        with open(RECENT_FILE) as f:
            recientes = json.load(f)

    # evitar duplicados
    recientes = [r for r in recientes if r["ruta"] != ruta]

    recientes.insert(0, data)  # lo pone arriba

    # limitar a 20 canciones
    recientes = recientes[:20]

    with open(RECENT_FILE, "w") as f:
        json.dump(recientes, f, indent=4)
def ver_recientes():
    if not os.path.exists(RECENT_FILE):
        messagebox.showinfo("Info", "No hay historial aún")
        return

    with open(RECENT_FILE) as f:
        recientes = json.load(f)

    lista.delete(0, tk.END)
    playlist.clear()

    for item in recientes:
        lista.insert(tk.END, f"🕒 {item['nombre']}")
        playlist.append(item["ruta"])

def mostrar_guia_ffmpeg():
    guia = tk.Toplevel()
    guia.title("Guía de instalación - FFmpeg")
    guia.geometry("600x400")
    guia.config(bg="#03045e")

    pasos = [
        "Paso 1:\n\nDescarga FFmpeg desde:\nhttps://ffmpeg.org/download.html",
        
        "Paso 2:\n\nDescomprime el archivo ZIP descargado.",
        
        "Paso 3:\n\nEntra a la carpeta 'bin'\nEjemplo:\nC:\\ffmpeg\\bin",
        
        "Paso 4:\n\nCopia esa ruta (la barra de dirección).",
        
        "Paso 5:\n\nAgrega esa ruta al PATH:\n\n- Busca 'Variables de entorno'\n- Edita PATH\n- Añade la ruta",
        
        "Paso 6:\n\nReinicia tu computadora\n\nLuego prueba en consola:\nffmpeg -version",
        
        "✅ Listo!\n\nTu programa AxMusic funcionará correctamente 🎵"
    ]

    indice = [0]

    texto = tk.Label(
        guia,
        text=pasos[indice[0]],
        bg="#03045e",
        fg="#caf0f8",
        font=("Arial", 12),
        wraplength=500,
        justify="left"
    )
    texto.pack(pady=40)

    def siguiente():
        if indice[0] < len(pasos) - 1:
            indice[0] += 1
            texto.config(text=pasos[indice[0]])

    def anterior():
        if indice[0] > 0:
            indice[0] -= 1
            texto.config(text=pasos[indice[0]])

    frame_botones = tk.Frame(guia, bg="#03045e")
    frame_botones.pack()

    tk.Button(frame_botones, text="⬅ Anterior", command=anterior).grid(row=0, column=0, padx=10)
    tk.Button(frame_botones, text="➡ Siguiente", command=siguiente).grid(row=0, column=1, padx=10)

# ================= UI =================
ventana = tk.Tk()
ventana.title("AxMusic 🎵")
ventana.geometry("1000x700")
ventana.config(bg=BG)

# Marca
marca = tk.Label(
    ventana,
    text="AXMUSIC",
    bg=BG,
    fg="#00b4d8",
    font=("Arial", 32, "bold")
)
marca.place(x=30, y=600)  # ajusta si quieres más arriba/abajo

# ================= SPLASH =================
def mostrar_splash(root):
    splash = tk.Toplevel()
    splash.overrideredirect(True)

    try:
        foto = tk.PhotoImage(file="axmusic.png")

        ancho, alto = 800, 500
        x = (splash.winfo_screenwidth() // 2) - (ancho // 2)
        y = (splash.winfo_screenheight() // 2) - (alto // 2)

        splash.geometry(f"{ancho}x{alto}+{x}+{y}")

        label = tk.Label(splash, image=foto)
        label.image = foto
        label.pack()

    except:
        splash.destroy()
        root.deiconify()
        return

    root.withdraw()
    splash.after(3000, lambda: cerrar_splash(splash, root))


def cerrar_splash(splash, root):
    splash.destroy()
    root.deiconify()

# ================= LAYOUT =================
sidebar = tk.Frame(ventana, bg=CARD, width=200)
sidebar.pack(side="left", fill="y")

main = tk.Frame(ventana, bg=BG)
main.pack(side="right", fill="both", expand=True)

# ================= LISTA =================
lista = tk.Listbox(
    main,
    bg=CARD,
    fg="white",
    selectbackground=HOVER,
    font=("Arial", 12),
    bd=0
)
lista.pack(pady=10, padx=10, fill="both", expand=True)

# ================= PLAYER =================
player = tk.Frame(main, bg=BG)
player.pack(fill="x")

titulo_actual = tk.Label(
    player,
    text="Nada reproduciendo",
    bg=BG,
    fg=TEXT,
    font=("Arial", 14, "bold")
)
titulo_actual.pack()

progreso = tk.DoubleVar()

barra = tk.Scale(
    player,
    from_=0,
    to=100,
    orient="horizontal",
    variable=progreso,
    length=500,
    bg=BG,
    fg=TEXT,
    troughcolor=CARD
)
barra.pack()

nombre_playlist_label = tk.Label(
    main,
    text="Sin playlist activa",
    bg=BG,
    fg="#90e0ef",
    font=("Arial", 12, "italic")
)
nombre_playlist_label.pack()

panel_playlist = tk.Frame(main, bg=CARD)
panel_playlist.pack(fill="x", pady=10, padx=20)
# ================= CONTROL =================
def reproducir():
    global indice_actual

    if lista.curselection():
        indice_actual = lista.curselection()[0]

    if playlist:
        ruta = playlist[indice_actual]
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.play()
        guardar_reciente(os.path.basename(ruta), ruta)
        titulo_actual.config(text=os.path.basename(ruta))


def siguiente():
    global indice_actual
    if playlist:
        indice_actual = (indice_actual + 1) % len(playlist)
        reproducir()


def actualizar_reproduccion():
    if pygame.mixer.music.get_busy():
        pos = pygame.mixer.music.get_pos() / 1000
        progreso.set(pos)
    else:
        if playlist:
            siguiente()

    ventana.after(1000, actualizar_reproduccion)

# ================= DESCARGA =================
def descargar(nombre):
    def hilo():
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3"
            }],
            "default_search": "ytsearch",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{nombre}", download=True)["entries"][0]
            archivo = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"

        playlist.append(archivo)
        guardar_reciente(os.path.basename(archivo), archivo)
        lista.insert(tk.END, os.path.basename(archivo))

    threading.Thread(target=hilo, daemon=True).start()

# ================= BUSCAR =================
# 🔎 BUSCADOR
entrada_busqueda = tk.Entry(main, font=("Arial", 12))
entrada_busqueda.pack(pady=5)

# 📂 NOMBRE PLAYLIST
entrada_playlist = tk.Entry(main, font=("Arial", 12))
entrada_playlist.insert(0, "Nombre playlist...")
entrada_playlist.pack(pady=5)

def buscar():
    nombre = entrada_busqueda.get()

    for archivo in os.listdir(DOWNLOAD_FOLDER):
        if limpiar_texto(nombre) in limpiar_texto(archivo):
            ruta = os.path.join(DOWNLOAD_FOLDER, archivo)
            playlist.append(ruta)
            lista.insert(tk.END, archivo)
            return

    descargar(nombre)

# ================= FAVORITOS =================
def guardar_favorito():
    if not lista.curselection():
        messagebox.showwarning("Atención", "Selecciona una canción")
        return

    i = lista.curselection()[0]
    data = {"nombre": lista.get(i), "ruta": playlist[i]}

    favs = []
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE) as f:
            favs = json.load(f)

    if data not in favs:
        favs.append(data)

    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=4)

    messagebox.showinfo("OK", "Guardado en favoritos ❤️")


def ver_favoritos():
    if not os.path.exists(FAV_FILE):
        return

    with open(FAV_FILE) as f:
        favs = json.load(f)

    lista.delete(0, tk.END)
    playlist.clear()

    for item in favs:
        lista.insert(tk.END, item["nombre"])
        playlist.append(item["ruta"])
def eliminar_favorito():
    if not lista.curselection():
        messagebox.showwarning("Atención", "Selecciona una canción")
        return

    index = lista.curselection()[0]

    if not os.path.exists(FAV_FILE):
        return

    with open(FAV_FILE) as f:
        favs = json.load(f)

    favs.pop(index)

    with open(FAV_FILE, "w") as f:
        json.dump(favs, f, indent=4)

    lista.delete(index)
    playlist.pop(index)

    messagebox.showinfo("OK", "Eliminado de favoritos 💔")

# ================= PLAYLISTS =================
def guardar_playlist():
    nombre = entrada_playlist.get()

    if not nombre or nombre == "Nombre playlist...":
        messagebox.showerror("Error", "Escribe nombre de la playlist")
        return

    data = []
    for i in range(len(playlist)):
        data.append({
            "nombre": lista.get(i),
            "ruta": playlist[i]
        })

    ruta = os.path.join(PLAYLIST_FOLDER, f"{nombre}.json")

    with open(ruta, "w") as f:
        json.dump(data, f, indent=4)
  
    messagebox.showinfo("OK", f"Playlist '{nombre}' guardada 🎧")

def ver_playlists():
    lista.delete(0, tk.END)
    playlist.clear()

    for archivo in os.listdir(PLAYLIST_FOLDER):
        if archivo.endswith(".json"):
            lista.insert(tk.END, f"📂 {archivo}")


def ver_contenido_playlist():
    if not lista.curselection():
        return

    nombre_archivo = lista.get(lista.curselection()[0]).replace("📂 ", "")
    ruta = os.path.join(PLAYLIST_FOLDER, nombre_archivo)

    try:
        with open(ruta) as f:
            data = json.load(f)

        lista.delete(0, tk.END)

        for item in data:
            lista.insert(tk.END, f"🎵 {item['nombre']}")

    except Exception as e:
        messagebox.showerror("Error", str(e))


def cargar_playlist():
    if not lista.curselection():
        messagebox.showwarning("Atención", "Selecciona una playlist")
        return

    nombre_archivo = lista.get(lista.curselection()[0]).replace("📂 ", "")
    ruta = os.path.join(PLAYLIST_FOLDER, nombre_archivo)
    ventana.playlist_actual = ruta
    try:
        with open(ruta) as f:
            data = json.load(f)

        lista.delete(0, tk.END)
        playlist.clear()

        for item in data:
            lista.insert(tk.END, item["nombre"])
            playlist.append(item["ruta"])
        nombre_playlist_label.config(text=f"Playlist: {nombre_archivo}")
        messagebox.showinfo("OK", f"Playlist '{nombre_archivo}' cargada 🎧")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def agregar_a_playlist():
    if not lista.curselection():
        messagebox.showwarning("Atención", "Selecciona una canción")
        return

    # Obtener canción seleccionada
    i = lista.curselection()[0]
    data = {"nombre": lista.get(i), "ruta": playlist[i]}

    # Ver playlists disponibles
    archivos = [f for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]

    if not archivos:
        messagebox.showerror("Error", "No hay playlists creadas")
        return

    # Ventana para elegir playlist
    ventana_select = tk.Toplevel(ventana)
    ventana_select.title("Seleccionar Playlist")
    ventana_select.geometry("300x300")

    listbox = tk.Listbox(ventana_select)
    listbox.pack(fill="both", expand=True, padx=10, pady=10)

    for f in archivos:
        listbox.insert(tk.END, f)

    def guardar_en_playlist():
        if not listbox.curselection():
            return

        nombre_archivo = listbox.get(listbox.curselection()[0])
        ruta = os.path.join(PLAYLIST_FOLDER, nombre_archivo)

        try:
            with open(ruta) as f:
                contenido = json.load(f)
        except:
            contenido = []

        if data not in contenido:
            contenido.append(data)

        with open(ruta, "w") as f:
            json.dump(contenido, f, indent=4)

        messagebox.showinfo("OK", f"Agregado a {nombre_archivo} 🎧")
        ventana_select.destroy()

    tk.Button(
        ventana_select,
        text="Guardar aquí",
        command=guardar_en_playlist
    ).pack(pady=10)

def eliminar_playlist():
    if not lista.curselection():
        messagebox.showwarning("Atención", "Selecciona una playlist")
        return

    nombre = lista.get(lista.curselection()[0]).replace("📂 ", "")
    ruta = os.path.join(PLAYLIST_FOLDER, nombre)

    confirmar = messagebox.askyesno("Confirmar", f"¿Eliminar {nombre}?")

    if confirmar:
        os.remove(ruta)
        messagebox.showinfo("OK", "Playlist eliminada 🗑️")
        ver_playlists()
def eliminar_cancion_playlist():
    if not lista.curselection():
        messagebox.showwarning("Atención", "Selecciona una canción")
        return

    if not hasattr(ventana, "playlist_actual"):
        messagebox.showerror("Error", "Primero carga una playlist")
        return

    index = lista.curselection()[0]

    with open(ventana.playlist_actual) as f:
        data = json.load(f)

    data.pop(index)

    with open(ventana.playlist_actual, "w") as f:
        json.dump(data, f, indent=4)

    lista.delete(index)
    playlist.pop(index)

    messagebox.showinfo("OK", "Canción eliminada 🗑️")

# ================= BOTONES =================
def btn(parent, txt, cmd):
    return tk.Button(
        parent,
        text=txt,
        command=cmd,
        bg=CARD,
        fg="white",
        activebackground=HOVER,
        bd=0,
        pady=5
    )

btn(main, "🔎 Buscar", buscar).pack()
btn(main, "▶ Play", reproducir).pack()
btn(main, "⏭ Siguiente", siguiente).pack()
btn(main, "➕ Añadir a Playlist", agregar_a_playlist).pack(fill="x", pady=5)
btn(main, "❤️ Guardar favorito", guardar_favorito).pack(fill="x", pady=5)

btn(sidebar, "⚙ Configuración", mostrar_guia_ffmpeg).pack(fill="x", pady=5)
btn(sidebar, "⭐ Ver favoritos", ver_favoritos).pack(fill="x", pady=5)
btn(sidebar, "💔 Quitar favorito", eliminar_favorito).pack(fill="x", pady=5)
btn(sidebar, "🕒 Recientes", ver_recientes).pack(fill="x", pady=5)

btn(panel_playlist, "📂 Ver Playlists", ver_playlists).pack(fill="x", pady=5)
btn(panel_playlist, "💾 Guardar Playlist", guardar_playlist).pack(fill="x", pady=5)
btn(panel_playlist, "🗑️ Eliminar Playlist", eliminar_playlist).pack(fill="x", pady=5)
btn(panel_playlist, "👀 Ver contenido", ver_contenido_playlist).pack(fill="x", pady=5)
btn(panel_playlist, "❌ Quitar canción", eliminar_cancion_playlist).pack(fill="x", pady=5)
btn(panel_playlist, "▶ Reproducir Playlist", cargar_playlist).pack(fill="x", pady=5)


# ... (aquí terminan tus botones) ...

# ================= START =================
mostrar_splash(ventana)
actualizar_reproduccion()

# --- PEGA EL BLOQUE DE FLASK AQUÍ ---
app = Flask(__name__)

@app.route('/')
def home():
    # Listamos solo archivos que terminen en .mp3 para evitar errores
    canciones = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith('.mp3')]
    return render_template('index.html', canciones=canciones)

@app.route('/play/<nombre>')
def play_web(nombre):
    # Usamos path join para que busque en la carpeta de descargas
    ruta = os.path.abspath(os.path.join(DOWNLOAD_FOLDER, nombre))
    return send_file(ruta)

def iniciar_servidor():
    # debug=False es vital para que no choque con Tkinter
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

threading.Thread(target=iniciar_servidor, daemon=True).start()
# ------------------------------------

ventana.mainloop()
# ================= START =================
mostrar_splash(ventana)
actualizar_reproduccion()
ventana.mainloop()