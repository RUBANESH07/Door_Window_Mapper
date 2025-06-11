from ultralytics import YOLO
import os
import yaml

# Path to your dataset YAML file
data_yaml_path = r"C:/Users/ruban/Documents/tommy/model/data.yaml"

# Load YOLOv8 base model (nano version, change to yolov8s.pt for better accuracy)
model = YOLO("yolov8n.pt")

# Train the model
results = model.train(
    data=data_yaml_path,
    epochs=50,
    imgsz=640,
    batch=8,
    project="door_window_training1",
    name="yolov8_custom1",
    save=True
)

# Print final metrics
metrics = results.metrics  # Dictionary containing final training metrics
print("\nTraining Complete. Final Metrics:")
print(f"mAP50: {metrics['metrics/mAP_0.5']:.4f}")
print(f"mAP50-95: {metrics['metrics/mAP_0.5:0.95']:.4f}")
print(f"Precision: {metrics['metrics/precision']:.4f}")
print(f"Recall: {metrics['metrics/recall']:.4f}")

# Save the trained model weights explicitly (optional)
save_path = "door_window_training/yolov8_custom/weights/custom_model1.pt"
model.save(save_path)




# # Load the best trained model for inference
# best_model_path = "door_window_training/yolov8_custom/weights/best.pt"
# trained_model = YOLO(best_model_path)

# # Run inference on an example image (replace with your image path)
# image_path = r"C:/Users/ruban/Documents/tommy/house.jpg"
# results = trained_model.predict(image_path)

# # Print detected objects info
# results.print()

# # Optional: show or save the image with predictions
# results.show()  # Opens a window with the image (requires GUI)
# # results.save()  # Saves the image with predictions to 'runs/detect/predict'
