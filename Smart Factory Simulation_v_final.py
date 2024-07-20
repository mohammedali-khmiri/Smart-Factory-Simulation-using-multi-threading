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


# Shared Value Manager
class SharedValueManager:
    def __init__(self):
        self.raw_material_count = mp.Value('i', 0)
        self.finished_product_count = mp.Value('i', 0)
        self.approved_product_count = mp.Value('i', 0)
        self.packaged_product_count = mp.Value('i', 0)
        self.shipped_product_count = mp.Value('i', 0)
        self.simulation_active = mp.Value('b', True)

    def stop_simulation(self):
        self.simulation_active.value = False


def raw_material_supplier(shared_values):
    while shared_values.simulation_active.value:
        try:
            time.sleep(random.uniform(1, 3))
            with shared_values.raw_material_count.get_lock():
                if (RAW_MATERIAL_CAPACITY - shared_values.raw_material_count.value >= 10):
                    shared_values.raw_material_count.value += 10
                    logging.info(
                        f"Supplied 10 units of raw materials. Total raw materials: {shared_values.raw_material_count.value}")
        except Exception as e:
            logging.error(f"Error in raw_material_supplier: {e}")


def production_line(shared_values, line_id):
    while shared_values.simulation_active.value:
        try:
            time.sleep(random.uniform(1, 2))

            with shared_values.raw_material_count.get_lock():
                if shared_values.raw_material_count.value > 0:
                    shared_values.raw_material_count.value -= 1

            logging.info(
                f"Production Line {line_id} is processing raw material. Raw materials left: {shared_values.raw_material_count.value}")

            with shared_values.finished_product_count.get_lock():
                if shared_values.finished_product_count.value < FINISHED_PRODUCT_CAPACITY:
                    shared_values.finished_product_count.value += 1
                    logging.info(
                        f"Production Line {line_id} produced a finished product. Total finished products: {shared_values.finished_product_count.value}")
        except Exception as e:
            logging.error(f"Error in production_line {line_id}: {e}")


def quality_control(shared_values, control_id):
    while shared_values.simulation_active.value:
        try:
            time.sleep(random.uniform(0.5, 1.5))

            with shared_values.finished_product_count.get_lock():
                if shared_values.finished_product_count.value > 0:
                    shared_values.finished_product_count.value -= 1
                    with shared_values.approved_product_count.get_lock():
                        shared_values.approved_product_count.value += 1
                    logging.info(
                        f"Quality Control {control_id} approved a product. Total approved products: {shared_values.approved_product_count.value}")
        except Exception as e:
            logging.error(f"Error in quality_control {control_id}: {e}")


def packaging_worker(shared_values, worker_id):
    while shared_values.simulation_active.value:
        try:
            time.sleep(random.uniform(1, 2))

            with shared_values.approved_product_count.get_lock():
                if shared_values.approved_product_count.value > 0:
                    shared_values.approved_product_count.value -= 1
                    with shared_values.packaged_product_count.get_lock():
                        shared_values.packaged_product_count.value += 1
                    logging.info(
                        f"Packaging Worker {worker_id} finished packaging a product. Total packaged products: {shared_values.packaged_product_count.value}")
        except Exception as e:
            logging.error(f"Error in packaging_worker {worker_id}: {e}")


def shipping_worker(shared_values):
    while shared_values.simulation_active.value:
        try:
            time.sleep(random.uniform(2, 4))

            with shared_values.packaged_product_count.get_lock():
                if shared_values.packaged_product_count.value > 0:
                    shared_values.packaged_product_count.value -= 1
                    with shared_values.shipped_product_count.get_lock():
                        shared_values.shipped_product_count.value += 1
                    logging.info(
                        f"Shipping Worker shipped products. Total shipped products: {shared_values.shipped_product_count.value}")
        except Exception as e:
            logging.error(f"Error in shipping_worker: {e}")


def maintenance_worker(shared_values):
    while shared_values.simulation_active.value:
        try:
            if shared_values.shipped_product_count.value >= FINISHED_PRODUCT_CAPACITY:
                logging.info(f"Maintenance Worker is performing maintenance.")
                shared_values.stop_simulation()
                time.sleep(random.uniform(1, 2))
                logging.info(f"Maintenance Worker finished maintenance.")
                break
        except Exception as e:
            logging.error(f"Error in maintenance_worker: {e}")


def start_simulation(shared_values):
    # Start threads for simulation components
    threads = []

    # Thread for raw material supplier
    supplier_thread = threading.Thread(target=raw_material_supplier, args=(shared_values,))
    threads.append(supplier_thread)
    supplier_thread.start()

    # Threads for production lines
    for i in range(NUM_PRODUCTION_LINES):
        t = threading.Thread(target=production_line, args=(shared_values, i))
        threads.append(t)
        t.start()

    # Threads for quality control
    for i in range(NUM_QUALITY_CONTROL):
        t = threading.Thread(target=quality_control, args=(shared_values, i))
        threads.append(t)
        t.start()

    # Threads for packaging workers
    for i in range(NUM_PACKAGING):
        t = threading.Thread(target=packaging_worker, args=(shared_values, i))
        threads.append(t)
        t.start()

    # Thread for shipping worker
    shipping_thread = threading.Thread(target=shipping_worker, args=(shared_values,))
    threads.append(shipping_thread)
    shipping_thread.start()

    # Thread for maintenance worker
    maintenance_thread = threading.Thread(target=maintenance_worker, args=(shared_values,))
    threads.append(maintenance_thread)
    maintenance_thread.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()


class SimulationApp:
    def __init__(self, root, shared_values):
        self.root = root
        self.shared_values = shared_values
        self.root.title("Simulation Dashboard")

        # Create a frame for the matplotlib figure
        self.figure_frame = ttk.Frame(root)
        self.figure_frame.pack(fill=tk.BOTH, expand=True)

        # Create matplotlib figures and axes
        self.figure, self.ax = plt.subplots(figsize=(10, 6))

        # Initialize empty lists for storing plot data
        self.timestamps = []
        self.raw_materials = []
        self.finished_products = []
        self.approved_products = []
        self.packaged_products = []
        self.shipped_products = []

        # Line plot for each data category
        self.raw_material_line, = self.ax.plot([], [], label='Raw Materials', color='b')
        self.finished_product_line, = self.ax.plot([], [], label='Finished Products', color='g')
        self.approved_product_line, = self.ax.plot([], [], label='Approved Products', color='r')
        self.packaged_product_line, = self.ax.plot([], [], label='Packaged Products', color='c')
        self.shipped_product_line, = self.ax.plot([], [], label='Shipped Products', color='m')

        self.ax.set_title('Simulation Data')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Count')
        self.ax.legend()
        self.ax.grid(True)

        # Create a canvas to display the matplotlib figure
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.figure_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Button to stop the simulation
        self.stop_button = ttk.Button(root, text="Stop Simulation", command=self.stop_simulation)
        self.stop_button.pack()

        # Start the simulation process
        self.simulation_thread = threading.Thread(target=start_simulation, args=(self.shared_values,))
        self.simulation_thread.start()

        # Update the plot periodically
        self.update_plot()

    def update_data(self):
        """Updates the data from shared variables."""
        current_time = time.time()
        self.timestamps.append(current_time)

        # Update data lists
        self.raw_materials.append(self.shared_values.raw_material_count.value)
        self.finished_products.append(self.shared_values.finished_product_count.value)
        self.approved_products.append(self.shared_values.approved_product_count.value)
        self.packaged_products.append(self.shared_values.packaged_product_count.value)
        self.shipped_products.append(self.shared_values.shipped_product_count.value)

        # Keep the data length consistent
        if len(self.raw_materials) > NUM_POINTS:
            self.raw_materials.pop(0)
            self.finished_products.pop(0)
            self.approved_products.pop(0)
            self.packaged_products.pop(0)
            self.shipped_products.pop(0)
            self.timestamps.pop(0)

    def update_plot(self):
        """Updates the matplotlib line charts with new data."""
        self.update_data()

        # Update line data
        self.raw_material_line.set_data(self.timestamps, self.raw_materials)
        self.finished_product_line.set_data(self.timestamps, self.finished_products)
        self.approved_product_line.set_data(self.timestamps, self.approved_products)
        self.packaged_product_line.set_data(self.timestamps, self.packaged_products)
        self.shipped_product_line.set_data(self.timestamps, self.shipped_products)

        # Adjust x-axis limits
        self.ax.set_xlim([min(self.timestamps), max(self.timestamps)])
        self.ax.relim()
        self.ax.autoscale_view()

        self.canvas.draw()

        if self.shared_values.simulation_active.value:
            self.root.after(1000, self.update_plot)  # Update plot every second

    def stop_simulation(self):
        """Stops the simulation and updates the plot."""
        self.shared_values.stop_simulation()
        self.simulation_thread.join()  # Wait for simulation thread to terminate
        logging.info("Simulation stopped.")
        self.update_plot()  # Ensure the final state is shown


if __name__ == "__main__":
    # Create shared value manager
    shared_values = SharedValueManager()

    # Start Tkinter application
    root = tk.Tk()
    app = SimulationApp(root, shared_values)
    root.mainloop()