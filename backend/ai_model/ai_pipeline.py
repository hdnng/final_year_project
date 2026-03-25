import torch
import cv2

from torchvision import transforms
from ultralytics import YOLO

from ai_model.cnn_model import BehaviorCNN

# ===== LOAD YOLO =====
yolo_model = YOLO("yolov8n.pt")  # nhẹ, realtime tốt

# ===== LOAD CNN =====
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

cnn_model = BehaviorCNN(num_labels=2)
cnn_model.load_state_dict(torch.load("ai_model/best_model.pth", map_location=device))
cnn_model.to(device)
cnn_model.eval()

# ===== TRANSFORM =====
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

# ===== LABEL MAP =====
LABELS = ["Normal", "Sleeping"]


def process_frame(frame):
    results = yolo_model(frame)[0]

    for box in results.boxes:
        cls = int(box.cls[0])

        # 🔥 chỉ lấy người (class 0 = person)
        if cls != 0:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # ===== CROP NGƯỜI =====
        person_crop = frame[y1:y2, x1:x2]

        if person_crop.size == 0:
            continue

        # ===== PREPROCESS =====
        input_tensor = transform(person_crop).unsqueeze(0).to(device)

        # ===== CNN PREDICT =====
        with torch.no_grad():
            output = cnn_model(input_tensor)
            pred = torch.argmax(output, dim=1).item()

        label = LABELS[pred]

        # ===== VẼ BOX =====
        color = (0, 255, 0) if pred == 0 else (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    return frame