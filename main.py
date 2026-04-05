
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pygame
import os
import yt_dlp
import threading
import json
import re
import random
from flask import Flask
import psutil

# ================= CONFIGURACIÓN INICIAL =================
pygame.mixer.init()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DOWNLOAD_FOLDER = "music_vault"
PLAYLIST_FOLDER = "playlists"
FAV_FILE = "favoritos.json"

for folder in [DOWNLOAD_FOLDER, PLAYLIST_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Variables Globales
playlist = []
indice_actual = 0
paused = False
modo_actual = "explorar" 

# ================= FUNCIONES DE LÓGICA =================

def limpiar_texto(texto):
    return re.sub(r'[^a-zA-Z0-9 ]', '', texto).lower()

def generar_color(nombre):
    random.seed(nombre) 
    r = random.randint(20, 50); g = random.randint(50, 100); b = random.randint(100, 180)
    return f"#{r:02x}{g:02x}{b:02x}"

def cambiar_fondo(nombre):
    color = generar_color(nombre)
    main.configure(fg_color=color)
    frame_cards.configure(fg_color=color)

# --- SPLASH SCREEN ---
def cerrar_splash(splash, root):
    splash.destroy()
    root.deiconify() # Muestra la ventana principal

def mostrar_splash(root):
    splash = tk.Toplevel()
    splash.overrideredirect(True) # Quita bordes de ventana

    try:
        # Intenta cargar la imagen axmusic.png
        img = tk.PhotoImage(file="axmusic.png")
        w, h = img.width(), img.height()
        x = (splash.winfo_screenwidth()//2)-(w//2)
        y = (splash.winfo_screenheight()//2)-(h//2)
        splash.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(splash, image=img, bg="#0b132b").pack()
        splash.image = img
    except:
        # Si no existe la imagen, crea un splash de texto rápido
        splash.geometry("400x200")
        splash.configure(bg="#0b132b")
        ctk.CTkLabel(splash, text="🎧 AXMUSIC PRO", font=("Segoe UI", 30, "bold")).pack(expand=True)

    root.withdraw() # Esconde la ventana principal mientras carga el splash
    splash.after(2500, lambda: cerrar_splash(splash, root))

# --- GESTIÓN DE FAVORITOS ---
def guardar_favorito():
    if not playlist: return
    ruta_act = playlist[indice_actual]
    favs = []
    if os.path.exists(FAV_FILE):
        with open(FAV_FILE, "r") as f: favs = json.load(f)
    
    if not any(f['ruta'] == ruta_act for f in favs):
        favs.append({"nombre": os.path.basename(ruta_act), "ruta": ruta_act})
        with open(FAV_FILE, "w") as f: json.dump(favs, f, indent=4)
        messagebox.showinfo("Éxito", "Añadido a favoritos ❤️")

def ver_favoritos():
    global modo_actual, playlist
    if not os.path.exists(FAV_FILE):
        messagebox.showinfo("Info", "No tienes favoritos aún")
        return
    with open(FAV_FILE, "r") as f: favs = json.load(f)
    playlist.clear()
    for item in favs: playlist.append(item["ruta"])
    modo_actual = "favoritos"
    render_cards()

# --- GESTIÓN DE PLAYLISTS ---
def guardar_playlist_nueva():
    nombre = entrada_playlist.get()
    if not nombre or nombre == "Nombre playlist...":
        messagebox.showwarning("Atención", "Escribe un nombre para la playlist")
        return
    data = [{"nombre": os.path.basename(p), "ruta": p} for p in playlist]
    with open(os.path.join(PLAYLIST_FOLDER, f"{nombre}.json"), "w") as f:
        json.dump(data, f, indent=4)
    messagebox.showinfo("OK", f"Playlist '{nombre}' creada")

def ver_todas_las_playlists():
    global modo_actual, playlist
    playlist.clear()
    archivos = [f for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]
    for arch in archivos:
        playlist.append(os.path.join(PLAYLIST_FOLDER, arch))
    modo_actual = "playlists_lista"
    render_cards()

def abrir_ventana_añadir():
    global playlist, indice_actual, modo_actual
    if not playlist or modo_actual == "playlists_lista":
        messagebox.showwarning("Atención", "Selecciona una canción primero")
        return

    ventana_add = ctk.CTkToplevel(ventana)
    ventana_add.title("Añadir a...")
    ventana_add.geometry("300x400")
    ventana_add.attributes("-topmost", True)

    ctk.CTkLabel(ventana_add, text="Selecciona Playlist", font=("Segoe UI", 14, "bold")).pack(pady=10)
    scroll = ctk.CTkScrollableFrame(ventana_add, width=250, height=250)
    scroll.pack(pady=10, padx=10)

    archivos = [f for f in os.listdir(PLAYLIST_FOLDER) if f.endswith(".json")]
    
    def guardar_en(archivo_json):
        ruta_p = os.path.join(PLAYLIST_FOLDER, archivo_json)
        cancion = {"nombre": os.path.basename(playlist[indice_actual]), "ruta": playlist[indice_actual]}
        try:
            with open(ruta_p, "r") as f: contenido = json.load(f)
        except: contenido = []
        if not any(c['ruta'] == cancion['ruta'] for c in contenido):
            contenido.append(cancion)
            with open(ruta_p, "w") as f: json.dump(contenido, f, indent=4)
            messagebox.showinfo("Hecho", f"Guardado en {archivo_json}")
            ventana_add.destroy()

    for arch in archivos:
        ctk.CTkButton(scroll, text=arch.replace(".json", ""), command=lambda a=arch: guardar_en(a)).pack(fill="x", pady=2)

# --- CONTROL DE REPRODUCCIÓN ---
def reproducir_indice(i):
    global indice_actual, paused, modo_actual, playlist
    if modo_actual == "playlists_lista":
        ruta_json = playlist[i]
        with open(ruta_json, "r") as f: data = json.load(f)
        playlist.clear()
        for item in data: playlist.append(item["ruta"])
        modo_actual = "explorar"; render_cards(); return

    indice_actual = i
    ruta = playlist[i]
    pygame.mixer.music.load(ruta)
    pygame.mixer.music.play()
    nombre = os.path.basename(ruta)
    titulo_actual.configure(text=nombre); label_cancion.configure(text=nombre)
    cambiar_fondo(nombre)
    paused = False; btn_pausa.configure(text="⏸")

def pausar_reanudar():
    global paused
    if paused: pygame.mixer.music.unpause(); paused = False; btn_pausa.configure(text="⏸")
    else: pygame.mixer.music.pause(); paused = True; btn_pausa.configure(text="▶")

def siguiente():
    global indice_actual, modo_actual
    if playlist and modo_actual != "playlists_lista":
        indice_actual = (indice_actual + 1) % len(playlist)
        reproducir_indice(indice_actual)

def actualizar_reproduccion():
    if pygame.mixer.music.get_busy():
        progreso.set(pygame.mixer.music.get_pos()/1000)
    elif playlist and not paused and modo_actual != "playlists_lista":
        siguiente()
    ventana.after(1000, actualizar_reproduccion)

# --- BÚSQUEDA ---
def buscar():
    global playlist
    nombre = entrada_busqueda.get()
    if not nombre: return
    for archivo in os.listdir(DOWNLOAD_FOLDER):
        if limpiar_texto(nombre) in limpiar_texto(archivo):
            playlist.append(os.path.join(DOWNLOAD_FOLDER, archivo))
            render_cards(); return
    descargar(nombre)

def descargar(nombre):
    def hilo():
        ydl_opts = {
            "format": "bestaudio/best", "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            "postprocessors": [{"key": "FFmpegExtractAudio","preferredcodec": "mp3"}],
            "default_search": "ytsearch", "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{nombre}", download=True)["entries"][0]
            archivo = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        playlist.append(archivo)
        ventana.after(0, render_cards)
    threading.Thread(target=hilo, daemon=True).start()

#================= Datos de la GPU Y CPU =================
def obtener_recursos():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    return cpu, ram

def actualizar_recursos():
    cpu, ram = obtener_recursos()
    label_recursos.config(text=f"CPU: {cpu}% | RAM: {ram}%")

    modo_inteligente()  # 👈 AÑADIR ESTO

    ventana.after(2000, actualizar_recursos)

def analizar_rendimiento():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    if cpu > 70:
        return "alto_cpu"
    elif ram > 75:
        return "alta_ram"
    else:
        return "normal"
def modo_inteligente():
    estado = analizar_rendimiento()

    if estado == "alto_cpu":
        label_estado.config(text="Estado: CPU alto ⚠️")

    elif estado == "alta_ram":
        label_estado.config(text="Estado: RAM alta ⚠️")

    else:
        label_estado.config(text="Estado: Normal ✅")


# ================= INTERFAZ GRÁFICA (UI) =================

ventana = ctk.CTk()
ventana.geometry("1100x750")
ventana.title("AxMusic Pro")

import tkinter as tk

label_recursos = tk.Label(ventana, text="CPU: 0% | RAM: 0%")
label_recursos.pack()

label_estado = tk.Label(ventana, text="Estado: Normal")
label_estado.pack()

sidebar = ctk.CTkFrame(ventana, width=200, fg_color="#0b132b")
sidebar.pack(side="left", fill="y")
ctk.CTkLabel(sidebar, text="🎧 AXMUSIC", font=("Segoe UI", 22, "bold")).pack(pady=20)

ctk.CTkButton(sidebar, text="🏠 Explorar", command=lambda: [globals().update(modo_actual="explorar"), render_cards()]).pack(fill="x", padx=10, pady=5)
ctk.CTkButton(sidebar, text="⭐ Favoritos", command=ver_favoritos).pack(fill="x", padx=10, pady=5)
ctk.CTkButton(sidebar, text="📂 Mis Playlists", command=ver_todas_las_playlists).pack(fill="x", padx=10, pady=5)

ctk.CTkLabel(sidebar, text="Nueva Playlist:", font=("Segoe UI", 12)).pack(pady=(20,0))
entrada_playlist = ctk.CTkEntry(sidebar, placeholder_text="Nombre...")
entrada_playlist.pack(pady=5, padx=10)
ctk.CTkButton(sidebar, text="💾 Guardar Lista", fg_color="#386641", command=guardar_playlist_nueva).pack(fill="x", padx=10, pady=5)

main = ctk.CTkFrame(ventana, fg_color="#0b132b")
main.pack(side="right", fill="both", expand=True)

top = ctk.CTkFrame(main, fg_color="transparent")
top.pack(fill="x", padx=20, pady=15)
entrada_busqueda = ctk.CTkEntry(top, placeholder_text="Buscar música...", width=350)
entrada_busqueda.pack(side="left", padx=10)
ctk.CTkButton(top, text="🔎 Buscar", width=100, command=buscar).pack(side="left")

content = ctk.CTkFrame(main, fg_color="transparent")
content.pack(fill="both", expand=True)

panel_visual = ctk.CTkFrame(content, width=250, fg_color="#1c2541", corner_radius=15)
panel_visual.pack(side="left", fill="y", padx=20, pady=10)
label_cancion = ctk.CTkLabel(panel_visual, text="Nada sonando", font=("Segoe UI", 14, "bold"), wraplength=200)
label_cancion.pack(pady=20)
ctk.CTkButton(panel_visual, text="❤️ Favorito", fg_color="#c1121f", command=guardar_favorito).pack(pady=5, padx=20, fill="x")
ctk.CTkButton(panel_visual, text="➕ Añadir a...", fg_color="#3a86ff", command=abrir_ventana_añadir).pack(pady=5, padx=20, fill="x")

frame_cards = ctk.CTkScrollableFrame(content, fg_color="#0b132b")
frame_cards.pack(side="right", fill="both", expand=True, padx=10)

def render_cards():
    for w in frame_cards.winfo_children(): w.destroy()
    for i, ruta in enumerate(playlist):
        nombre = os.path.basename(ruta)
        card = ctk.CTkFrame(frame_cards, width=150, height=200, fg_color="#1c2541")
        card.grid(row=i//4, column=i%4, padx=10, pady=10)
        icon = "📂" if modo_actual == "playlists_lista" else "🎼"
        ctk.CTkLabel(card, text=icon, font=("Arial", 40)).pack(pady=10)
        ctk.CTkLabel(card, text=nombre[:15], font=("Segoe UI", 11)).pack()
        txt_btn = "Abrir" if modo_actual == "playlists_lista" else "▶"
        ctk.CTkButton(card, text=txt_btn, width=60, command=lambda idx=i: reproducir_indice(idx)).pack(pady=10)

player = ctk.CTkFrame(ventana, height=100, fg_color="#1c2541")
player.pack(side="bottom", fill="x")
titulo_actual = ctk.CTkLabel(player, text="---", font=("Segoe UI", 12))
titulo_actual.pack()
progreso = ctk.CTkSlider(player, from_=0, to=100)
progreso.pack(fill="x", padx=50)

btns = ctk.CTkFrame(player, fg_color="transparent")
btns.pack(pady=5)
btn_pausa = ctk.CTkButton(btns, text="⏸", width=50, command=pausar_reanudar)
btn_pausa.pack(side="left", padx=10)
ctk.CTkButton(btns, text="⏭", width=50, command=siguiente).pack(side="left", padx=10)

# Flask Server
app = Flask(__name__)
@app.route('/')
def home(): return "Servidor Activo"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()

# ================= INICIO =================
mostrar_splash(ventana)
actualizar_reproduccion()
actualizar_recursos()
ventana.mainloop()
