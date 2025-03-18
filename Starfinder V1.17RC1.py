#!/usr/bin/env python3
"""
Starfinder_V1.17.py

A tool for Elite Dangerous that searches for a star and displays all surrounding star systems within a user‐defined range.
Features:
  • Uses the EDSM API only (retrieving system coordinates then nearby systems)
  • Caching (valid for 86400 seconds) and operation & error logging
  • 3D plotting via Plotly with configurable dimensions and star color mappings
  • Import/Export of search results
  • A modernized Tkinter GUI with:
      - A toggle “More Details” button (to show/hide extra info)
      - A scrollable radius dropdown (values 4 to 40, 6 items visible)
      - A custom animated loading indicator (ship traveling toward a star)
      - An About section showing creator, contributors, and version

EDSM API endpoints used:
  1. System details:
     GET https://www.edsm.net/api-v1/system?systemName={systemName}&showCoordinates=1
  2. Sphere systems (by coordinates):
     GET https://www.edsm.net/api-v1/sphere-systems?x={x}&y={y}&z={z}&radius={radius}&showCoordinates=1&showId=1&showDistance=1&showPrimaryStar=1
"""

import os
import time
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import plotly.graph_objs as go
import plotly.io as pio
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -------------------- Directories & Global Constants --------------------
BASE_DIR = os.getcwd()
MAIN_FOLDER = os.path.join(BASE_DIR, "EDStarFinderData")
CACHE_FOLDER = os.path.join(MAIN_FOLDER, "cache")
LOGS_FOLDER = os.path.join(MAIN_FOLDER, "logs")
RESULTS_FOLDER = os.path.join(MAIN_FOLDER, "results")
for folder in (MAIN_FOLDER, CACHE_FOLDER, LOGS_FOLDER, RESULTS_FOLDER):
    os.makedirs(folder, exist_ok=True)

# Global Variables
sphere_radius = 16  # This will be updated from the dropdown. Initially set to 16.
system_data = []    # holds star system data from API

# 3D plot configuration
plot_width = 1000
plot_height = 800

# Star type to color mapping
star_type_colors = {
    "O": "blue",
    "B": "lightblue",
    "A": "white",
    "F": "lightyellow",
    "G": "yellow",
    "K": "orange",
    "M": "red",
    "Unknown": "grey"
}

# Theme Colors
LIGHT_THEME = {"bg": "white", "fg": "black", "widget_bg": "lightgrey", "text_bg": "white", "text_fg": "black"}
DARK_THEME = {"bg": "#1a1a2e", "fg": "white", "widget_bg": "#16213e", "text_bg": "#1a1a2e", "text_fg": "white"}

# -------------------- Global State for Toggles & Animation --------------------
more_details_shown = False
loading_animation_running = False
loading_animation_job = None
ship_img = None
star_img = None
ship_item = None
star_item = None

# -------------------- Function Definitions --------------------
def update_theme():
    """Apply light or dark theme to all main UI elements."""
    theme = DARK_THEME if dark_mode_enabled.get() else LIGHT_THEME
    root.config(bg=theme["bg"])
    input_frame.config(bg=theme["bg"])
    menu_frame.config(bg=theme["bg"])
    extra_buttons_frame.config(bg=theme["bg"])
    result_text.config(bg=theme["text_bg"], fg=theme["text_fg"], insertbackground=theme["text_fg"])
    star_label.config(bg=theme["bg"], fg=theme["fg"])
    radius_label.config(bg=theme["bg"], fg=theme["fg"])
    total_label.config(bg=theme["bg"], fg=theme["fg"])
    star_entry.config(bg=theme["widget_bg"], fg=theme["fg"], insertbackground=theme["text_fg"])
    log_operation("toggle_dark_mode", {"mode": "Dark" if dark_mode_enabled.get() else "Light"})

def open_3d_settings():
    """Open a dialog to configure 3D plot settings and star colors."""
    config_win = tk.Toplevel(root)
    config_win.title("3D Settings")
    config_win.grab_set()
    ttk.Label(config_win, text="Window Width:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    width_entry = ttk.Entry(config_win)
    width_entry.insert(0, str(plot_width))
    width_entry.grid(row=0, column=1, padx=5, pady=5)
    ttk.Label(config_win, text="Window Height:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    height_entry = ttk.Entry(config_win)
    height_entry.insert(0, str(plot_height))
    height_entry.grid(row=1, column=1, padx=5, pady=5)
    row_index = 2
    ttk.Label(config_win, text="Star Type Colors:").grid(row=row_index, column=0, columnspan=2, pady=(10, 0))
    row_index += 1
    color_entries = {}
    for stype, color in star_type_colors.items():
        ttk.Label(config_win, text=f"Color for {stype}:").grid(row=row_index, column=0, sticky="w", padx=5, pady=2)
        entry = ttk.Entry(config_win)
        entry.insert(0, color)
        entry.grid(row=row_index, column=1, padx=5, pady=2)
        color_entries[stype] = entry
        row_index += 1
    def save_config():
        global plot_width, plot_height
        try:
            new_width = int(width_entry.get())
            new_height = int(height_entry.get())
            plot_width = new_width
            plot_height = new_height
        except ValueError:
            messagebox.showerror("Error", "Width and Height must be integers.")
            return
        for stype, entry in color_entries.items():
            star_type_colors[stype] = entry.get().strip()
        config_win.destroy()
        log_operation("configure_3d_settings", {"plot_width": plot_width, "plot_height": plot_height, "star_type_colors": star_type_colors})
    ttk.Button(config_win, text="Save", command=save_config).grid(row=row_index, column=0, columnspan=2, pady=10)

def log_operation(operation, details):
    log_data = {"timestamp": datetime.now().isoformat(), "operation": operation, "details": details}
    op_log_file = os.path.join(LOGS_FOLDER, "operations.log")
    try:
        with open(op_log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data) + "\n")
    except Exception as e:
        print("Operation logging error:", e)

def log_error(error_message):
    now = datetime.now()
    date_str = now.strftime("%m-%d-%Y")
    log_filename = os.path.join(LOGS_FOLDER, f"{date_str}.txt")
    with open(log_filename, "a", encoding="utf-8") as f:
        log_entry = f"{now.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}\n\n"
        f.write(log_entry)
    log_operation("error_logged", {"error": error_message})

def get_request_with_retries(url, timeout, retries=3, backoff_factor=0.5):
    session = requests.Session()
    retry_strategy = Retry(total=retries, status_forcelist=[429, 500, 502, 503, 504],
                           allowed_methods=["GET"], backoff_factor=backoff_factor, raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    log_operation("request_start", {"url": url, "timeout": timeout, "retries": retries})
    response = session.get(url, timeout=timeout)
    log_operation("request_end", {"url": url, "status_code": response.status_code})
    return response

def fetch_system_data(star, radius):
    errors = []
    # Retrieve system details to get coordinates.
    system_url = f"https://www.edsm.net/api-v1/system?systemName={star}&showCoordinates=1"
    log_operation("edsm_system_request_start", {"url": system_url})
    try:
        response = get_request_with_retries(system_url, timeout=10)
        response.raise_for_status()
        system_info = response.json()
        if isinstance(system_info, list):
            if not system_info:
                raise ValueError(f"EDSM system endpoint returned empty result for '{star}'")
            system_info = system_info[0]
        elif not isinstance(system_info, dict) or "name" not in system_info:
            raise ValueError("EDSM system endpoint returned unexpected result.")
        coords = system_info.get("coords")
        if not coords:
            raise ValueError("Coordinates not available for system.")
        x = coords.get("x")
        y = coords.get("y")
        z = coords.get("z")
    except Exception as e:
        errors.append(f"EDSM system API error: {e}")
        log_operation("edsm_system_request_error", {"error": str(e)})
        return None, "\n".join(errors)
    
    # Query sphere-systems using coordinates with the provided radius.
    sphere_url = (f"https://www.edsm.net/api-v1/sphere-systems?"
                  f"x={x}&y={y}&z={z}&radius={radius}"
                  f"&showCoordinates=1&showId=1&showDistance=1&showPrimaryStar=1")
    log_operation("edsm_sphere_request_start", {"url": sphere_url})
    try:
        response = get_request_with_retries(sphere_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and not data:
            data = []
        if not isinstance(data, list):
            raise ValueError("EDSM sphere-systems API returned unexpected result.")
        star_sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in star.strip())
        cache_filename = f"{star_sanitized}_{radius}.json"
        cache_filepath = os.path.join(CACHE_FOLDER, cache_filename)
        with open(cache_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
        log_operation("edsm_sphere_request_success", {"status_code": response.status_code, "result_count": len(data)})
        return data, None
    except Exception as e:
        errors.append(f"EDSM sphere-systems API error: {e}")
        log_operation("edsm_sphere_request_error", {"error": str(e)})
        return None, "\n".join(errors)

def start_loading_animation():
    global loading_animation_running
    loading_animation_running = True
    loading_canvas.pack(pady=5)
    animate_loading()

def animate_loading():
    global loading_animation_job, loading_animation_running
    if not loading_animation_running:
        return
    current_coords = loading_canvas.coords(ship_item)
    if current_coords:
        x, y = current_coords[0], current_coords[1]
        if x < 360:
            loading_canvas.move(ship_item, 2, 0)
        else:
            loading_canvas.coords(ship_item, 20, 50)
    loading_animation_job = root.after(50, animate_loading)

def stop_loading_animation():
    global loading_animation_running, loading_animation_job
    loading_animation_running = False
    if loading_animation_job is not None:
        root.after_cancel(loading_animation_job)
        loading_animation_job = None
    loading_canvas.pack_forget()

def show_brief_view():
    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, f"Star systems within {sphere_radius} ly of '{star_entry.get().strip()}':\n\n")
    for system in system_data:
        system_name = system.get("name", "Unknown")
        distance = system.get("distance", "N/A")
        coords = system.get("coords", {})
        x = coords.get("x", "N/A")
        y = coords.get("y", "N/A")
        z = coords.get("z", "N/A")
        result_text.insert(tk.END, f"Name: {system_name}\n", "star")
        result_text.insert(tk.END, f"Distance: {distance} ly\n")
        result_text.insert(tk.END, f"Coordinates: x={x}, y={y}, z={z}\n\n")

def show_more_details_expanded():
    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, "Star systems with more details:\n\n")
    for system in system_data:
        system_name = system.get("name", "Unknown")
        result_text.insert(tk.END, f"Name: {system_name}\n", "star")
        for key, value in system.items():
            if value:
                result_text.insert(tk.END, f"{key}: {value}\n")
        result_text.insert(tk.END, "-" * 40 + "\n")

def toggle_more_details():
    global more_details_shown
    if not system_data:
        messagebox.showwarning("No Data", "Please perform a search first.")
        return
    if more_details_shown:
        show_brief_view()
        more_details_shown = False
        more_details_button.config(text="More Details")
    else:
        show_more_details_expanded()
        more_details_shown = True
        more_details_button.config(text="Hide Details")

def clear_results():
    result_text.delete('1.0', tk.END)
    total_label.config(text="0")
    log_operation("clear_results", {"action": "Cleared displayed results"})

def clear_cache_current():
    """Clear cache files for the current searched system."""
    current_star = star_entry.get().strip()
    if not current_star:
        messagebox.showwarning("Clear Cache", "No current system to clear cache for.")
        return
    star_sanitized = "".join(c if c.isalnum() or c == "_" else "_" for c in current_star)
    cleared = 0
    for filename in os.listdir(CACHE_FOLDER):
        if filename.startswith(star_sanitized + "_"):
            try:
                os.remove(os.path.join(CACHE_FOLDER, filename))
                cleared += 1
            except Exception as e:
                log_operation("cache_clear_error", {"file": filename, "error": str(e)})
    messagebox.showinfo("Clear Cache", f"Cleared {cleared} cache file(s) for '{current_star}'.")

def clear_cache_all():
    """Clear all cache files."""
    cleared = 0
    for filename in os.listdir(CACHE_FOLDER):
        try:
            os.remove(os.path.join(CACHE_FOLDER, filename))
            cleared += 1
        except Exception as e:
            log_operation("cache_clear_error", {"file": filename, "error": str(e)})
    messagebox.showinfo("Clear Cache", f"Cleared all cache files ({cleared} file(s) removed).")

def start_search():
    start_loading_animation()
    query_button.config(state=tk.DISABLED)
    log_operation("search_started", {"star": star_entry.get().strip(), "radius": sphere_radius})
    threading.Thread(target=threaded_query, daemon=True).start()

def threaded_query():
    star = star_entry.get().strip()
    data, error_log = fetch_system_data(star, sphere_radius)
    root.after(0, update_ui, star, data, error_log)

def update_ui(star, data, error_log):
    stop_loading_animation()
    query_button.config(state=tk.NORMAL)
    result_text.delete('1.0', tk.END)

    # Get the user-selected radius from the dropdown.
    user_radius = int(radius_var.get())
    # Update the global sphere_radius to match the user-selected value.
    global sphere_radius
    sphere_radius = user_radius

    if data:
        # Filter the results to only include systems within the user-requested radius.
        filtered_data = [s for s in data if float(s.get("distance", 0)) <= user_radius]
    else:
        filtered_data = []

    # If no systems are found within the user-selected radius, perform a fallback request with 16 ly.
    if not filtered_data and user_radius != 16:
        messagebox.showinfo("No Stars Found", 
            "No stars found within given radius, try searching a larger area?\nNow showing default 16 ly radius.")
        radius_var.set("16")
        sphere_radius = 16
        start_search()
        return

    if error_log:
        result_text.insert(tk.END, f"Some errors occurred:\n{error_log}\n\n")
        log_error(error_log)
        messagebox.showinfo("Search Issue", f"An issue occurred during search:\n{error_log}\n\n"
                                              "Please check the spelling or try increasing the search radius.")

    if filtered_data:
        global system_data
        try:
            system_data = sorted(filtered_data, key=lambda s: float(s.get("distance", 0)))
        except Exception:
            system_data = filtered_data
        show_brief_view()
        # Update the result count label color based on number of systems found.
        result_count = len(system_data)
        if result_count <= 20:
            color = "green"
        elif result_count <= 35:
            color = "yellow"
        else:
            color = "red"
        total_label.config(text=str(result_count), fg=color)
        more_details_button.config(state=tk.NORMAL, text="More Details")
        log_operation("search_completed", {"star": star, "results": len(system_data)})
    else:
        result_text.insert(tk.END, f"No systems found within {user_radius} ly of '{star}'.\n")
        total_label.config(text="0")
        log_operation("search_failed", {"star": star})

def plot_3d_model():
    if not system_data:
        messagebox.showwarning("No Data", "No star systems found to display in 3D.")
        return
    traces = {}
    for system in system_data:
        primary_info = system.get("primaryStar")
        if primary_info and isinstance(primary_info, dict):
            stype = primary_info.get("type", "Unknown")
        else:
            stype = system.get("starType", "Unknown")
        type_letter = stype.strip()[0].upper() if stype and stype.strip() else "Unknown"
        color = star_type_colors.get(type_letter, star_type_colors.get("Unknown", "grey"))
        if type_letter not in traces:
            traces[type_letter] = {"x": [], "y": [], "z": [], "names": [], "distances": [], "color": color, "starType": stype}
        coords = system.get("coords", {})
        if not coords:
            continue
        traces[type_letter]["x"].append(coords.get("x", 0))
        traces[type_letter]["y"].append(coords.get("y", 0))
        traces[type_letter]["z"].append(coords.get("z", 0))
        traces[type_letter]["names"].append(system.get("name", "Unknown"))
        try:
            traces[type_letter]["distances"].append(float(system.get("distance", 0)))
        except (ValueError, TypeError):
            traces[type_letter]["distances"].append(0)
    data_traces = []
    for key, group in traces.items():
        custom_data = [[d] for d in group["distances"]]
        trace = go.Scatter3d(
            x=group["x"],
            y=group["y"],
            z=group["z"],
            mode="markers+text",
            text=group["names"],
            hovertemplate="Name: %{text}<br>Distance: %{customdata[0]} ly<br>Type: " + group["starType"],
            customdata=custom_data,
            marker=dict(size=5, color=group["color"], opacity=0.8),
            name=f"Type {key}"
        )
        data_traces.append(trace)
    layout = go.Layout(
        title="3D View of Star Systems",
        scene=dict(xaxis_title="X Coordinate", yaxis_title="Y Coordinate", zaxis_title="Z Coordinate", bgcolor="rgb(10,10,10)"),
        paper_bgcolor="rgb(10,10,10)",
        plot_bgcolor="rgb(10,10,10)",
        font=dict(color="white"),
        width=plot_width,
        height=plot_height,
    )
    fig = go.Figure(data=data_traces, layout=layout)
    pio.show(fig)
    log_operation("plot_3d_model", {"results": len(system_data)})

def export_results():
    global system_data
    if not system_data:
        messagebox.showwarning("Export Error", "No system data available to export.")
        return
    filename = os.path.join(RESULTS_FOLDER, f"{star_entry.get().strip() or 'ExportedData'}.json")
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(system_data, f, indent=2)
        messagebox.showinfo("Export Successful", f"Results exported to {filename}")
        log_operation("export_results", {"filename": filename, "result_count": len(system_data)})
    except Exception as e:
        messagebox.showerror("Export Error", f"Error exporting results: {e}")
        log_operation("export_results_error", {"error": str(e)})

def import_results():
    global system_data
    file_path = filedialog.askopenfilename(
        title="Select Data File to Import",
        filetypes=[("JSON Files", "*.json"), ("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not file_path:
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            imported_data = json.load(f)
        system_data = imported_data
        result_text.delete('1.0', tk.END)
        star_name = os.path.splitext(os.path.basename(file_path))[0]
        result_text.insert(tk.END, f"(Imported) Star systems within {sphere_radius} light years of '{star_name}':\n\n")
        for system in system_data:
            system_name = system.get("name", "Unknown")
            distance = system.get("distance", "N/A")
            coords = system.get("coords", {})
            x = coords.get("x", "N/A")
            y = coords.get("y", "N/A")
            z = coords.get("z", "N/A")
            result_text.insert(tk.END, f"Name: {system_name}\n", "star")
            result_text.insert(tk.END, f"Distance: {distance} ly\n")
            result_text.insert(tk.END, f"Coordinates: x={x}, y={y}, z={z}\n\n")
        total_label.config(text=str(len(system_data)))
        more_details_button.config(state=tk.NORMAL)
        log_operation("import_results", {"file_path": file_path, "result_count": len(system_data)})
    except Exception as e:
        messagebox.showerror("Import Error", f"Error importing results: {e}")
        log_operation("import_results_error", {"error": str(e)})

def clear_cache_current_and_all_menu():
    # This function is a placeholder if needed to bind both cache clearing actions.
    pass

def update_radius(*args):
    global sphere_radius
    try:
        sphere_radius = int(radius_var.get())
    except ValueError:
        sphere_radius = 4
    radius_label.config(text=f"Radius: {sphere_radius} ly")
    log_operation("update_radius", {"new_radius": sphere_radius})

def show_about():
    messagebox.showinfo("About", "Created by The Omega Colonization Project\nContributors: HiiJustin, HadominusX\nVersion 1.17b1")

# -------------------- GUI Setup --------------------
root = tk.Tk()
root.title("Elite Dangerous Star Finder")
root.geometry("900x700")
root.resizable(False, False)

dark_mode_enabled = tk.BooleanVar(master=root, value=False)

# Loading Animation Canvas (managed by pack)
loading_canvas = tk.Canvas(root, width=400, height=100, bg=DARK_THEME["bg"], highlightthickness=0)
try:
    ship_img = tk.PhotoImage(file="ship.png")
    # Changed star image to planet art
    star_img = tk.PhotoImage(file="planet.png")
except Exception as e:
    messagebox.showerror("Image Load Error", f"Error loading sprites: {e}")
    ship_img = None
    star_img = None
if star_img:
    star_item = loading_canvas.create_image(380, 50, image=star_img)
if ship_img:
    ship_item = loading_canvas.create_image(20, 50, image=ship_img)
loading_canvas.create_text(200, 80, text="Jump in progress...", fill=DARK_THEME["fg"], font=("Helvetica", 12))
loading_canvas.pack_forget()

# Input Frame and Widgets (using grid)
input_frame = tk.Frame(root, bg=DARK_THEME["bg"])
input_frame.pack(padx=10, pady=(10, 5), fill=tk.X)
menu_frame = tk.Frame(root, bg=DARK_THEME["bg"])
menu_frame.pack(padx=10, pady=(5, 0), fill=tk.X)

star_label = tk.Label(input_frame, text="Enter Star Name:", bg=DARK_THEME["bg"], fg=DARK_THEME["fg"], font=("Helvetica", 10))
star_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
star_entry = tk.Entry(input_frame, width=40, bg=DARK_THEME["widget_bg"], fg=DARK_THEME["fg"], insertbackground=DARK_THEME["text_fg"])
star_entry.grid(row=0, column=1, padx=5, pady=5)
star_entry.focus()

query_button = tk.Button(input_frame, text="Search", command=start_search, bg=DARK_THEME["widget_bg"], fg=DARK_THEME["fg"], font=("Helvetica", 10))
query_button.grid(row=0, column=2, padx=5, pady=5)

radius_label = tk.Label(input_frame, text="Radius: 4 ly", bg=DARK_THEME["bg"], fg=DARK_THEME["fg"], font=("Helvetica", 10))
radius_label.grid(row=0, column=3, padx=5, pady=5)
radius_values = list(map(str, range(4, 41)))
radius_var = tk.StringVar(value="4")
radius_menu = ttk.Combobox(input_frame, values=radius_values, textvariable=radius_var, state="readonly", height=6)
radius_menu.grid(row=0, column=4, padx=5, pady=5)
radius_var.trace_add("write", update_radius)

# Extra Buttons Frame
extra_buttons_frame = tk.Frame(root, bg=DARK_THEME["bg"])
extra_buttons_frame.pack(padx=10, pady=5, fill=tk.X)
more_details_button = tk.Button(extra_buttons_frame, text="More Details", command=toggle_more_details, state=tk.DISABLED,
                                bg=DARK_THEME["widget_bg"], fg=DARK_THEME["fg"], font=("Helvetica", 10))
more_details_button.grid(row=0, column=0, padx=5, pady=5)
three_d_button = tk.Button(extra_buttons_frame, text="Open 3D Model", command=plot_3d_model,
                           bg=DARK_THEME["widget_bg"], fg=DARK_THEME["fg"], font=("Helvetica", 10))
three_d_button.grid(row=0, column=1, padx=5, pady=5)
# New "Clear Results" button in the extra buttons frame
clear_results_button = tk.Button(extra_buttons_frame, text="Clear Results", command=clear_results,
                                 bg=DARK_THEME["widget_bg"], fg=DARK_THEME["fg"], font=("Helvetica", 10))
clear_results_button.grid(row=0, column=2, padx=5, pady=5)

# Results Text and Total Label
result_text = scrolledtext.ScrolledText(root, width=80, height=20, bg=DARK_THEME["text_bg"], fg=DARK_THEME["text_fg"],
                                        insertbackground=DARK_THEME["text_fg"], font=("Helvetica", 10))
result_text.pack(padx=10, pady=5)
result_text.tag_configure("star", font=("Helvetica", 12, "bold"))

total_label = tk.Label(root, text="0", font=("Helvetica", 24, "bold"), bg=DARK_THEME["bg"], fg=DARK_THEME["fg"])
total_label.pack(side=tk.RIGHT, padx=20, pady=10)

# Menu Bar
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Export Results", command=export_results)
file_menu.add_command(label="Import Results", command=import_results)
# Add new cache clearing options to the File menu
file_menu.add_separator()
file_menu.add_command(label="Clear cache for current searched system", command=clear_cache_current)
file_menu.add_command(label="Clear all cache", command=clear_cache_all)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Configure 3D Settings", command=open_3d_settings)
settings_menu.add_checkbutton(label="Dark Mode", variable=dark_mode_enabled, command=update_theme)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)
root.config(menu=menu_bar)

# Bindings
root.bind('<Return>', lambda event: start_search())

update_theme()
root.mainloop()
