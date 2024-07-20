import multiprocessing as mp
import threading
import time
import random
import logging
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configuration
NUM_PRODUCTION_LINES = 3
NUM_QUALITY_CONTROL = 2
NUM_PACKAGING = 2
NUM_SHIPPING = 1
RAW_MATERIAL_CAPACITY = 100
FINISHED_PRODUCT_CAPACITY = 6
NUM_POINTS = 100  # Number of data points to keep for plotting

# Logging Configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')

# Shared Values
raw_material_count = mp.Value('i', 0)
finished_product_count = mp.Value('i', 0)
approved_product_count = mp.Value('i', 0)
packaged_product_count = mp.Value('i', 0)
shipped_product_count = mp.Value('i', 0)
simulation_active = mp.Value('b', True)

# Stop Simulation Function
def stop_simulation():
    global simulation_active
    simulation_active.value = False

def raw_material_supplier():
    while simulation_active.value:
        try:
            time.sleep(random.uniform(1, 3))
            with raw_material_count.get_lock():
                if (RAW_MATERIAL_CAPACITY - raw_material_count.value >= 10):
                    raw_material_count.value += 10
                    logging.info(f"Supplied 10 units of raw materials. Total raw materials: {raw_material_count.value}")
        except Exception as e:
            logging.error(f"Error in raw_material_supplier: {e}")

def production_line(line_id):
    while simulation_active.value:
        try:
            time.sleep(random.uniform(1, 2))
            with raw_material_count.get_lock():
                if raw_material_count.value > 0:
                    raw_material_count.value -= 1

            logging.info(f"Production Line {line_id} is processing raw material. Raw materials left: {raw_material_count.value}")

            with finished_product_count.get_lock():
                if finished_product_count.value < FINISHED_PRODUCT_CAPACITY:
                    finished_product_count.value += 1
                    logging.info(f"Production Line {line_id} produced a finished product. Total finished products: {finished_product_count.value}")
        except Exception as e:
            logging.error(f"Error in production_line {line_id}: {e}")

def quality_control(control_id):
    while simulation_active.value:
        try:
            time.sleep(random.uniform(0.5, 1.5))
            with finished_product_count.get_lock():
                if finished_product_count.value > 0:
                    finished_product_count.value -= 1
                    with approved_product_count.get_lock():
                        approved_product_count.value += 1
                    logging.info(f"Quality Control {control_id} approved a product. Total approved products: {approved_product_count.value}")
        except Exception as e:
            logging.error(f"Error in quality_control {control_id}: {e}")

def packaging_worker(worker_id):
    while simulation_active.value:
        try:
            time.sleep(random.uniform(1, 2))
            with approved_product_count.get_lock():
                if approved_product_count.value > 0:
                    approved_product_count.value -= 1
                    with packaged_product_count.get_lock():
                        packaged_product_count.value += 1
                    logging.info(f"Packaging Worker {worker_id} finished packaging a product. Total packaged products: {packaged_product_count.value}")
        except Exception as e:
            logging.error(f"Error in packaging_worker {worker_id}: {e}")

def shipping_worker():
    while simulation_active.value:
        try:
            time.sleep(random.uniform(2, 4))
            with packaged_product_count.get_lock():
                if packaged_product_count.value > 0:
                    packaged_product_count.value -= 1
                    with shipped_product_count.get_lock():
                        shipped_product_count.value += 1
                    logging.info(f"Shipping Worker shipped products. Total shipped products: {shipped_product_count.value}")
        except Exception as e:
            logging.error(f"Error in shipping_worker: {e}")

def maintenance_worker():
    while simulation_active.value:
        try:
            if shipped_product_count.value >= FINISHED_PRODUCT_CAPACITY:
                logging.info(f"Maintenance Worker is performing maintenance.")
                stop_simulation()
                time.sleep(random.uniform(1, 2))
                logging.info(f"Maintenance Worker finished maintenance.")
                break
        except Exception as e:
            logging.error(f"Error in maintenance_worker: {e}")

def start_simulation():
    # Start threads for simulation components
    threads = []

    # Thread for raw material supplier
    supplier_thread = threading.Thread(target=raw_material_supplier)
    threads.append(supplier_thread)
    supplier_thread.start()

    # Threads for production lines
    for i in range(NUM_PRODUCTION_LINES):
        t = threading.Thread(target=production_line, args=(i,))
        threads.append(t)
        t.start()

    # Threads for quality control
    for i in range(NUM_QUALITY_CONTROL):
        t = threading.Thread(target=quality_control, args=(i,))
        threads.append(t)
        t.start()

    # Threads for packaging workers
    for i in range(NUM_PACKAGING):
        t = threading.Thread(target=packaging_worker, args=(i,))
        threads.append(t)
        t.start()

    # Thread for shipping worker
    shipping_thread = threading.Thread(target=shipping_worker)
    threads.append(shipping_thread)
    shipping_thread.start()

    # Thread for maintenance worker
    maintenance_thread = threading.Thread(target=maintenance_worker)
    threads.append(maintenance_thread)
    maintenance_thread.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

def update_data(timestamps, raw_materials, finished_products, approved_products, packaged_products, shipped_products):
    """Updates the data from shared variables."""
    current_time = time.time()
    timestamps.append(current_time)

    # Update data lists
    raw_materials.append(raw_material_count.value)
    finished_products.append(finished_product_count.value)
    approved_products.append(approved_product_count.value)
    packaged_products.append(packaged_product_count.value)
    shipped_products.append(shipped_product_count.value)

    # Keep the data length consistent
    if len(raw_materials) > NUM_POINTS:
        raw_materials.pop(0)
        finished_products.pop(0)
        approved_products.pop(0)
        packaged_products.pop(0)
        shipped_products.pop(0)
        timestamps.pop(0)

def update_plot(ax, canvas, raw_material_line, finished_product_line, approved_product_line, packaged_product_line, shipped_product_line, timestamps, raw_materials, finished_products, approved_products, packaged_products, shipped_products):
    """Updates the matplotlib line charts with new data."""
    update_data(timestamps, raw_materials, finished_products, approved_products, packaged_products, shipped_products)

    # Update line data
    raw_material_line.set_data(timestamps, raw_materials)
    finished_product_line.set_data(timestamps, finished_products)
    approved_product_line.set_data(timestamps, approved_products)
    packaged_product_line.set_data(timestamps, packaged_products)
    shipped_product_line.set_data(timestamps, shipped_products)

    # Adjust x-axis limits
    ax.set_xlim([min(timestamps), max(timestamps)])
    ax.relim()
    ax.autoscale_view()

    canvas.draw()

    if simulation_active.value:
        canvas.get_tk_widget().after(1000, lambda: update_plot(ax, canvas, raw_material_line, finished_product_line, approved_product_line, packaged_product_line, shipped_product_line, timestamps, raw_materials, finished_products, approved_products, packaged_products, shipped_products))  # Update plot every second

def create_simulation_app(root):
    global simulation_active

    root.title("Simulation Dashboard")

    # Create a frame for the matplotlib figure
    figure_frame = ttk.Frame(root)
    figure_frame.pack(fill=tk.BOTH, expand=True)

    # Create matplotlib figures and axes
    figure, ax = plt.subplots(figsize=(10, 6))

    # Initialize empty lists for storing plot data
    timestamps = []
    raw_materials = []
    finished_products = []
    approved_products = []
    packaged_products = []
    shipped_products = []

    # Line plot for each data category
    raw_material_line, = ax.plot([], [], label='Raw Materials', color='b')
    finished_product_line, = ax.plot([], [], label='Finished Products', color='g')
    approved_product_line, = ax.plot([], [], label='Approved Products', color='r')
    packaged_product_line, = ax.plot([], [], label='Packaged Products', color='c')
    shipped_product_line, = ax.plot([], [], label='Shipped Products', color='m')

    ax.set_title('Simulation Data')
    ax.set_xlabel('Time')
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True)

    # Create a canvas to display the matplotlib figure
    canvas = FigureCanvasTkAgg(figure, master=figure_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Button to stop the simulation
    stop_button = ttk.Button(root, text="Stop Simulation", command=stop_simulation)
    stop_button.pack()

    # Start the simulation process
    simulation_thread = threading.Thread(target=start_simulation)
    simulation_thread.start()

    # Update the plot periodically
    update_plot(ax, canvas, raw_material_line, finished_product_line, approved_product_line, packaged_product_line, shipped_product_line, timestamps, raw_materials, finished_products, approved_products, packaged_products, shipped_products)

if __name__ == "__main__":
    # Start Tkinter application
    root = tk.Tk()
    create_simulation_app(root)
    root.mainloop()
