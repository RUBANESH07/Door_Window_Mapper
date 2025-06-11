import cv2
import numpy as np
import os
from ultralytics import YOLO
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk

class DetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Door/Window Detection Tool")
        
        self.house_image = None
        self.detected_boxes = []
        self.scale_factor = 1.0
        
        self.setup_styles()
        self.create_layout()
        
        weight_path = r"C:\Users\ruban\Documents\tommy\Project\model\Own_trained_model\door_window_training\yolov8_custom1\weights\best.pt"
        assert os.path.exists(weight_path), f"Weight file not found at {weight_path}"
        self.model = YOLO(weight_path)
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TButton', font=('Helvetica', 10), padding=6, relief='flat',
                        background='#4CAF50', foreground='white')
        style.map('TButton', background=[('active', '#45a049')])
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', font=('Helvetica', 10), background='#f0f0f0')
        
    def create_layout(self):
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.left_panel = ttk.Frame(self.main_frame, width=250)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        self.right_panel = ttk.Frame(self.main_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_input_controls()
        self.create_display_area()
        
    def create_input_controls(self):
        title = ttk.Label(self.left_panel, text="Door/Window Detection", font=('Helvetica', 12, 'bold'))
        title.pack(pady=(0, 20))
        
        house_frame = ttk.LabelFrame(self.left_panel, text="1. Upload House Image", padding=10)
        house_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Button(house_frame, text="Browse...", command=self.load_house_image).pack(fill=tk.X)
        
        settings_frame = ttk.LabelFrame(self.left_panel, text="Settings", padding=10)
        settings_frame.pack(fill=tk.X)
        ttk.Button(settings_frame, text="Save Results", command=self.save_results).pack(fill=tk.X, pady=(10, 0))
        
    def create_display_area(self):
        self.canvas_frame = ttk.Frame(self.right_panel)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='#e0e0e0')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scrollbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar = ttk.Scrollbar(self.right_panel, orient=tk.HORIZONTAL, command=self.canvas.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        
        self.status_label = ttk.Label(self.right_panel, text="Upload a house image to begin", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=(10, 0))
        
    def load_house_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            self.house_image = cv2.imread(file_path)
            self.detected_boxes = self.detect_objects(file_path)
            self.display_image(self.house_image)
            self.update_status(f"Loaded house image: {os.path.basename(file_path)}")
            
    def detect_objects(self, image_path):
        detected_boxes = []
        conf_thresholds = [0.3, 0.5, 0.7]
        for conf in conf_thresholds:
            results = self.model.predict(image_path, conf=conf)
            if len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    cls_name = "door" if cls == 0 else "window"
                    detected_boxes.append({
                        'x1': int(x1), 'y1': int(y1), 'x2': int(x2), 'y2': int(y2),
                        'conf': conf, 'cls': cls, 'cls_name': cls_name
                    })
        return detected_boxes
    
    def display_image(self, image):
        if image is None:
            return
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        h, w = image_rgb.shape[:2]
        self.scale_factor = min(canvas_width/w, canvas_height/h) if canvas_width > 0 and canvas_height > 0 else 1.0
        new_size = (int(w*self.scale_factor), int(h*self.scale_factor))
        image_resized = cv2.resize(image_rgb, new_size)
        self.current_image = Image.fromarray(image_resized)
        self.photo = ImageTk.PhotoImage(image=self.current_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        for box in self.detected_boxes:
            x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
            x1, x2 = int(x1*self.scale_factor), int(x2*self.scale_factor)
            y1, y2 = int(y1*self.scale_factor), int(y2*self.scale_factor)
            color = "#4285F4" if box['cls_name'] == "door" else "#EA4335"
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2, dash=(5, 5))
            label = f"{box['cls_name']} ({box['conf']:.2f})"
            self.canvas.create_text(x1+5, y1+5, text=label, anchor=tk.NW, fill=color, font=('Helvetica', 8, 'bold'))
            
    def on_mousewheel(self, event):
        if event.state & 0x4:
            if event.num == 5 or event.delta < 0:
                self.scale_factor *= 0.9
            elif event.num == 4 or event.delta > 0:
                self.scale_factor *= 1.1
            self.display_image(self.house_image)

    def save_results(self):
        if self.house_image is not None and self.detected_boxes:
            # Create detection_results directory if it doesn't exist
            results_dir = "detection_results"
            os.makedirs(results_dir, exist_ok=True)

            # Save the image with detected boxes
            image_path = os.path.join(results_dir, "detected_hou3.jpg")
            coords_path = os.path.join(results_dir, "coordinates_hou3.txt")

            # Create a copy of the image to draw on
            result_img = self.house_image.copy()
            
            # Draw boxes and labels on the image
            for box in self.detected_boxes:
                x1, y1, x2, y2 = box['x1'], box['y1'], box['x2'], box['y2']
                # Use blue for doors and green for windows
                color = (255, 0, 0) if box['cls_name'] == "door" else (0, 255, 0)
                cv2.rectangle(result_img, (x1, y1), (x2, y2), color, 2)
                
                # Add label with confidence score
                label = f"{box['cls_name']} {box['conf']:.2f}"
                cv2.putText(result_img, label, (x1, y1-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Save the image
            cv2.imwrite(image_path, result_img)

            # Save coordinates to text file
            with open(coords_path, "w") as f:
                for box in self.detected_boxes:
                    # Format: x1:123 y1:456 x2:789 y2:012 door/window
                    f.write(f"x1:{box['x1']} y1:{box['y1']} x2:{box['x2']} y2:{box['y2']} {box['cls_name']}\n")

            self.update_status(f"Saved detection results:\nImage: {image_path}\nCoordinates: {coords_path}")
        else:
            self.update_status("No detection results to save")
            
    def update_status(self, message):
        self.status_label.config(text=message)

def main():
    root = tk.Tk()
    app = DetectionApp(root)
    root.minsize(800, 600)
    window_width, window_height = 1000, 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    root.mainloop()

if __name__ == "__main__":
    main()