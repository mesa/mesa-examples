"""
Tank game visualization and entry point.
Uses tkinter to create an interactive UI.
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import math
from model import TankGameModel
from agents import Tank, Shell, Target, Cloud


class TankGameVisualization:
    """Tank game visualization UI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Tank Projectile Attack Game")
        
        # Default parameters (used to reset consistently)
        self.default_params = {
            "angle": 45.0,
            "power": 70.0,
            "wind": 0.0,
            "wall_position": 17,
            "wall_height": 10,
            "wall_block_wind": False,
            "target_movable": False
        }
        
        # Create model with default parameters
        self.model = TankGameModel(**self.default_params)
        # Precompute pixel offsets for the "cloud" word
        self.cloud_word_cells = []  # relative offsets
        self.cloud_word_width = 0
        self._build_cloud_word_cells()
        
        # Running flag
        self.running = False
        self.simulation_thread = None
        
        # Auto-reset controls
        self.auto_reset_scheduled = False  # whether auto-reset is scheduled
        self.auto_reset_after_id = None    # after callback ID for cancellation
        
        # Build UI
        self._create_ui()
        
        # Initial render
        self.update_display()
    
    def _create_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left: control panel
        control_frame = ttk.LabelFrame(main_frame, text="Control Panel", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Right: game grid
        grid_frame = ttk.Frame(main_frame, padding="10")
        grid_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Build controls
        self._create_controls(control_frame)
        
        # Build grid canvas
        self._create_grid(grid_frame)
    
    def _create_controls(self, parent):
        """Create control widgets"""
        # Angle slider
        angle_frame = ttk.Frame(parent)
        angle_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(angle_frame, text="Angle (deg):").grid(row=0, column=0, sticky=tk.W)
        self.angle_var = tk.DoubleVar(value=self.default_params["angle"])
        angle_scale = ttk.Scale(
            angle_frame,
            from_=0,
            to=90,
            variable=self.angle_var,
            orient=tk.HORIZONTAL,
            command=self._on_angle_change
        )
        angle_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        angle_frame.columnconfigure(1, weight=1)
        self.angle_label = ttk.Label(angle_frame, text=f"{self.default_params['angle']:.1f}")
        self.angle_label.grid(row=0, column=2, sticky=tk.W)
        
        # Power slider
        power_frame = ttk.Frame(parent)
        power_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(power_frame, text="Power:").grid(row=0, column=0, sticky=tk.W)
        self.power_var = tk.DoubleVar(value=self.default_params["power"])
        power_scale = ttk.Scale(
            power_frame,
            from_=0,
            to=100,
            variable=self.power_var,
            orient=tk.HORIZONTAL,
            command=self._on_power_change
        )
        power_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        power_frame.columnconfigure(1, weight=1)
        self.power_label = ttk.Label(power_frame, text=f"{self.default_params['power']:.1f}")
        self.power_label.grid(row=0, column=2, sticky=tk.W)
        
        # Wind slider
        wind_frame = ttk.Frame(parent)
        wind_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(wind_frame, text="Wind:").grid(row=0, column=0, sticky=tk.W)
        self.wind_var = tk.DoubleVar(value=self.default_params["wind"])
        wind_scale = ttk.Scale(
            wind_frame,
            from_=-100,
            to=100,
            variable=self.wind_var,
            orient=tk.HORIZONTAL,
            command=self._on_wind_change
        )
        wind_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        wind_frame.columnconfigure(1, weight=1)
        self.wind_label = ttk.Label(wind_frame, text=f"{self.default_params['wind']:.1f}")
        self.wind_label.grid(row=0, column=2, sticky=tk.W)
        
        # Wall position slider
        wall_pos_frame = ttk.Frame(parent)
        wall_pos_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(wall_pos_frame, text="Wall Position:").grid(row=0, column=0, sticky=tk.W)
        self.wall_pos_var = tk.IntVar(value=self.default_params["wall_position"])
        wall_pos_scale = ttk.Scale(
            wall_pos_frame,
            from_=0,
            to=34,
            variable=self.wall_pos_var,
            orient=tk.HORIZONTAL,
            command=self._on_wall_pos_change
        )
        wall_pos_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        wall_pos_frame.columnconfigure(1, weight=1)
        self.wall_pos_label = ttk.Label(wall_pos_frame, text=str(self.default_params["wall_position"]))
        self.wall_pos_label.grid(row=0, column=2, sticky=tk.W)
        
        # Wall height slider
        wall_height_frame = ttk.Frame(parent)
        wall_height_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(wall_height_frame, text="Wall Height:").grid(row=0, column=0, sticky=tk.W)
        self.wall_height_var = tk.IntVar(value=self.default_params["wall_height"])
        wall_height_scale = ttk.Scale(
            wall_height_frame,
            from_=0,
            to=20,
            variable=self.wall_height_var,
            orient=tk.HORIZONTAL,
            command=self._on_wall_height_change
        )
        wall_height_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        wall_height_frame.columnconfigure(1, weight=1)
        self.wall_height_label = ttk.Label(wall_height_frame, text=str(self.default_params["wall_height"]))
        self.wall_height_label.grid(row=0, column=2, sticky=tk.W)
        
        # Wall blocks wind checkbox
        self.wall_block_wind_var = tk.BooleanVar(value=self.default_params["wall_block_wind"])
        wall_block_check = ttk.Checkbutton(
            parent,
            text="Wall Blocks Wind",
            variable=self.wall_block_wind_var,
            command=self._on_wall_block_wind_change
        )
        wall_block_check.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        # Target movable checkbox
        self.target_movable_var = tk.BooleanVar(value=self.default_params["target_movable"])
        target_move_check = ttk.Checkbutton(
            parent,
            text="Target Moves Up/Down",
            variable=self.target_movable_var,
            command=self._on_target_movable_change
        )
        target_move_check.grid(row=6, column=0, sticky=tk.W, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Fire button
        fire_button = ttk.Button(
            button_frame,
            text="Fire",
            command=self._on_fire
        )
        fire_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        
        # Reset button
        reset_button = ttk.Button(
            button_frame,
            text="Reset",
            command=self._on_reset
        )
        reset_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
    
    def _create_grid(self, parent):
        """Create the game grid canvas"""
        # Canvas frame
        canvas_frame = ttk.Frame(parent)
        canvas_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        
        # Canvas
        self.canvas_size = 600  # canvas size in pixels
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="white"
        )
        self.canvas.grid(row=0, column=0)
        
        # Compute cell size
        self.cell_size = self.canvas_size / self.model.grid.width

    def _build_cloud_word_cells(self):
        """Generate relative pixel offsets for the word 'cloud'"""
        # 5x5 pixel-style lowercase letters, width=4, spacing=1
        pattern = [
            " ###  #     ###   #  #  ###",
            "#     #    #   #  #  #  #  #",
            "#     #    #   #  #  #  #   #",
            "#     #    #   #  #  #  #  #",
            " ###  ####  ###   ####  ###"
        ]
        self.cloud_word_width = len(pattern[0])
        cells = []
        for row_idx, row in enumerate(pattern):
            for col_idx, ch in enumerate(row):
                if ch != " ":
                    # Use negative y offset so increasing row_idx moves downward
                    cells.append((col_idx, -row_idx))
        self.cloud_word_cells = cells
    
    def _apply_default_params_to_ui(self):
        """Reset controls and model params to defaults"""
        defaults = self.default_params
        
        # Update UI variables
        self.angle_var.set(defaults["angle"])
        self.power_var.set(defaults["power"])
        self.wind_var.set(defaults["wind"])
        self.wall_pos_var.set(defaults["wall_position"])
        self.wall_height_var.set(defaults["wall_height"])
        self.wall_block_wind_var.set(defaults["wall_block_wind"])
        self.target_movable_var.set(defaults["target_movable"])
        
        # Update labels
        self.angle_label.config(text=f"{defaults['angle']:.1f}")
        self.power_label.config(text=f"{defaults['power']:.1f}")
        self.wind_label.config(text=f"{defaults['wind']:.1f}")
        self.wall_pos_label.config(text=str(defaults["wall_position"]))
        self.wall_height_label.config(text=str(defaults["wall_height"]))
        
        # Sync model parameters
        self.model.angle = defaults["angle"]
        self.model.power = defaults["power"]
        self.model.wind = defaults["wind"]
        self.model.wall_position = defaults["wall_position"]
        self.model.wall_height = defaults["wall_height"]
        self.model.wall_block_wind = defaults["wall_block_wind"]
        self.model.target_movable = defaults["target_movable"]
    
    def _on_angle_change(self, value):
        """Angle change callback"""
        ui_angle = float(value)
        model_angle = 90.0 - ui_angle
        #angle = float(value)
        #self.model.angle = angle
        #self.angle_label.config(text=f"{angle:.1f}")
        self.model.angle = model_angle   # model receives complementary angle
        self.angle_label.config(text=f"{ui_angle:.1f}") # label shows slider value
        
    
    def _on_power_change(self, value):
        """Power change callback"""
        power = float(value)
        self.model.power = power
        self.power_label.config(text=f"{power:.1f}")
    
    def _on_wind_change(self, value):
        """Wind change callback"""
        wind = float(value)
        self.model.wind = wind
        self.wind_label.config(text=f"{wind:.1f}")
    
    def _on_wall_pos_change(self, value):
        """Wall position change callback"""
        wall_pos = int(float(value))
        self.model.wall_position = wall_pos
        self.wall_pos_label.config(text=str(wall_pos))
    
    def _on_wall_height_change(self, value):
        """Wall height change callback"""
        wall_height = int(float(value))
        self.model.wall_height = wall_height
        self.wall_height_label.config(text=str(wall_height))
    
    def _on_wall_block_wind_change(self):
        """Wall blocks wind checkbox change"""
        self.model.wall_block_wind = self.wall_block_wind_var.get()
    
    def _on_target_movable_change(self):
        """Target movable checkbox change"""
        movable = self.target_movable_var.get()
        self.model.target_movable = movable
        # When enabling movement, reset direction upward to avoid sticking at edges
        if self.model.target is not None:
            self.model.target.direction = 1
            self.model.target.move_tick = 0
    
    def _on_fire(self):
        """Fire button callback"""
        self.model.fire()
        if not self.running:
            self.start_simulation()
    
    def _auto_reset_after_hit(self):
        """Auto reset after target hit"""
        # Clear after callback ID so future scheduling works
        self.auto_reset_after_id = None
        self._do_reset()
    
    def _cancel_auto_reset(self):
        """Cancel any scheduled auto-reset"""
        if self.auto_reset_after_id is not None:
            self.root.after_cancel(self.auto_reset_after_id)
            self.auto_reset_after_id = None
        self.auto_reset_scheduled = False
    
    def _do_reset(self):
        """Internal reset implementation"""
        # Stop current simulation loop
        self.running = False
        if hasattr(self.model, "running"):
            self.model.running = False
        
        # Wait for simulation loop to finish if running
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=0.1)
        self.simulation_thread = None
        
        # Force-cancel any scheduled auto-reset
        self._cancel_auto_reset()
        
        # Recreate model and restore defaults
        self.model = TankGameModel(**self.default_params)
        
        # Update grid scaling for new model
        self.cell_size = self.canvas_size / self.model.grid.width
        # Rebuild cloud word coordinates to match new grid
        self._build_cloud_word_cells()
        
        # Sync UI controls to defaults
        self._apply_default_params_to_ui()
        
        # Update display immediately
        self.update_display()
        
        # Restart simulation loop to keep game running (cloud keeps moving)
        self.start_simulation()
    
    def _on_reset(self):
        """Reset button callback - restart game"""
        self._do_reset()
    
    def start_simulation(self):
        """Start simulation loop"""
        if self.running:
            return
        self.running = True
        self.model.running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
    
    def _simulation_loop(self):
        """Simulation loop running in background thread"""
        while self.running:
            # Keep updating while model runs or explosions remain
            if self.model.running or self.model.explosion_cells:
                self.model.step()
                self.root.after(0, self.update_display)
                time.sleep(0.05)  # control simulation speed
            else:
                # Model stopped and no explosions, break loop
                break
        self.running = False
    
    def update_display(self):
        """Render current state to canvas"""
        self.canvas.delete("all")
        
        # Draw grid background
        cell_size = self.cell_size
        width = self.model.grid.width
        height = self.model.grid.height
        
        # Draw grass (bottom row in green)
        grass_color = "#b6e388"
        y_ground = 0
        for x in range(width):
            x1 = x * cell_size
            y1 = (height - 1 - y_ground) * cell_size
            x2 = (x + 1) * cell_size
            y2 = (height - y_ground) * cell_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=grass_color, outline="")
        
        # Draw optional grid lines
        for i in range(width + 1):
            x = i * cell_size
            self.canvas.create_line(x, 0, x, height * cell_size, fill="lightgray", width=1)
        for i in range(height + 1):
            y = i * cell_size
            self.canvas.create_line(0, y, width * cell_size, y, fill="lightgray", width=1)
        
        # Draw "cloud" word (light gray pixels moving with cloud, wrapping horizontally)
        cloud_agent = self.model.cloud
        if cloud_agent is not None:
            anchor_x = int(cloud_agent.pos_f[0]) - self.cloud_word_width // 2
            anchor_y = int(cloud_agent.pos_f[1])
            for dx, dy in self.cloud_word_cells:
                x = (anchor_x + dx) % width  # horizontal wrap
                y = anchor_y + dy
                if 0 <= y < height:
                    x1 = x * cell_size
                    y1 = (height - 1 - y) * cell_size
                    x2 = (x + 1) * cell_size
                    y2 = (height - y) * cell_size
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#dcdcdc", outline="")
        
        # Draw shell trajectory (light red, stipple for semi-transparency, above background)
        for (x, y) in self.model.trajectory_cells:
            x1 = x * cell_size
            y1 = (height - 1 - y) * cell_size
            x2 = (x + 1) * cell_size
            y2 = (height - y) * cell_size
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#ff9e9e",
                outline="",
                stipple="gray50"
            )
        
        # Draw wall (gray blocks)
        for (x, y) in self.model.wall_cells:
            x1 = x * cell_size
            y1 = (height - 1 - y) * cell_size  # flip Y-axis (grid Y is up)
            x2 = (x + 1) * cell_size
            y2 = (height - y) * cell_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="gray", outline="darkgray")
        
        # Draw explosion effects (overlay others)
        if self.model.explosion_centers:  # only draw when explosion centers exist
            for (x, y), ttl in self.model.explosion_cells.items():
                x1 = x * cell_size
                y1 = (height - 1 - y) * cell_size
                x2 = (x + 1) * cell_size
                y2 = (height - y) * cell_size
                
                # Determine color by Manhattan distance to closest explosion center
                min_dist = float('inf')
                for center_x, center_y in self.model.explosion_centers:
                    manhattan_dist = abs(x - center_x) + abs(y - center_y)
                    min_dist = min(min_dist, manhattan_dist)
                
                # Radius 1 (distance ≤1): red
                # Radius 2 (distance ≤2 and >1): yellow
                if min_dist <= 1:
                    color = "red"
                elif min_dist <= 2:
                    color = "yellow"
                else:
                    color = "orange"  # shouldn't happen but keep fallback
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="darkorange")
        
        # Draw agents
        # Iterate all cells
        for x in range(width):
            for y in range(height):
                cell_agents = self.model.grid.get_cell_list_contents([(x, y)])
                if not cell_agents:
                    continue
                
                # Compute draw position (flip Y-axis)
                x1 = x * cell_size
                y1 = (height - 1 - y) * cell_size
                x2 = (x + 1) * cell_size
                y2 = (height - y) * cell_size
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                # Priority: explosion > Shell > Target > Tank > Cloud > Wall
                # Wall and explosions already drawn above
                for agent in cell_agents:
                    if isinstance(agent, Tank):
                        # Tank: rectangle hull + round turret + barrel line
                        hull_margin = cell_size * 0.12
                        hull_height = cell_size * 0.45
                        hull_x1 = x1 + hull_margin
                        hull_x2 = x2 - hull_margin
                        hull_y2 = y2 - hull_margin
                        hull_y1 = hull_y2 - hull_height
                        hull_fill = "#6ca965"
                        hull_outline = "#3f6b3d"
                        self.canvas.create_rectangle(
                            hull_x1, hull_y1, hull_x2, hull_y2,
                            fill=hull_fill, outline=hull_outline, width=2
                        )
                        
                        # Turret
                        turret_r = cell_size * 0.18
                        turret_cx = center_x
                        turret_cy = hull_y1 - cell_size * 0.05
                        self.canvas.create_oval(
                            turret_cx - turret_r, turret_cy - turret_r,
                            turret_cx + turret_r, turret_cy + turret_r,
                            fill=hull_fill, outline=hull_outline, width=2
                        )
                        
                        # Barrel (direction follows current UI angle)
                        ui_angle = self.angle_var.get()
                        angle_rad = math.radians(ui_angle)
                        barrel_len = cell_size * 0.6
                        # Canvas y-axis is down, so invert y direction
                        barrel_dx = math.cos(angle_rad) * barrel_len
                        barrel_dy = -math.sin(angle_rad) * barrel_len
                        barrel_end_x = turret_cx + barrel_dx
                        barrel_end_y = turret_cy + barrel_dy
                        self.canvas.create_line(
                            turret_cx, turret_cy, barrel_end_x, barrel_end_y,
                            fill=hull_outline, width=4, capstyle=tk.ROUND
                        )
                    elif isinstance(agent, Shell):
                        # Shell: black
                        self.canvas.create_oval(
                            x1 + 1, y1 + 1, x2 - 1, y2 - 1,
                            fill="black", outline="black"
                        )
                    elif isinstance(agent, Target):
                        # Target: blue
                        self.canvas.create_rectangle(
                            x1 + 2, y1 + 2, x2 - 2, y2 - 2,
                            fill="blue", outline="darkblue", width=2
                        )
                    elif isinstance(agent, Cloud):
                        # Cloud is drawn via pixel font; skip separate dots
                        continue
        
        # Show victory text when target destroyed, before reset
        if not self.model.target_exists:
            self.canvas.create_text(
                self.canvas_size / 2,
                self.canvas_size / 2,
                text="YOU WIN",
                font=("Helvetica", 48, "bold"),
                fill="darkgreen"
            )
        
        # Check whether to auto-reset (after hit and explosions vanish)
        if not self.model.running and not self.model.target_exists:
            # If explosions are gone, schedule auto-reset
            if not self.model.explosion_cells and not self.auto_reset_scheduled:
                self.auto_reset_scheduled = True
                # Delay 0.5s so player sees explosions fade
                self.auto_reset_after_id = self.root.after(500, self._auto_reset_after_hit)
        elif self.model.running:
            # If model running, cancel scheduled auto-reset
            self._cancel_auto_reset()


def main():
    """Main function"""
    root = tk.Tk()
    # Keep reference on root to avoid unused-var lint and allow future access
    root.app = TankGameVisualization(root)
    root.mainloop()


if __name__ == "__main__":
    main()

