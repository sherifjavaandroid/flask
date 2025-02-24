from flask import Flask, render_template, Response
import cv2
import mediapipe as mp
import numpy as np
import time
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# إعداد مكتبة MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# فتح الكاميرا (ستستخدم كاميرا الجهاز الذي يُشغّل عليه التطبيق)
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # عرض الإطار
cap.set(4, 480)  # ارتفاع الإطار

# متغيرات لحساب التكرارات
counter = 0
stage = None
ptime = 0

def calculate_angle(a, b, c):
    a = np.array(a)  # النقطة الأولى
    b = np.array(b)  # النقطة الوسطى
    c = np.array(c)  # النقطة النهائية

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180:
        angle = 360 - angle
    return angle

def gen_frames():
    global counter, stage, ptime
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # تحويل الإطار إلى RGB لمعالجة MediaPipe ثم العودة إلى BGR للعرض
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                # استخراج مواقع الكتف، المرفق والمعصم (الذراع اليسرى في هذا المثال)
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                # حساب الزاوية بين النقاط الثلاث
                angle = calculate_angle(shoulder, elbow, wrist)
                cv2.putText(image, str(angle),
                            tuple(np.multiply(elbow, [640, 480]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                # تحديث المرحلة وحساب التكرارات
                if angle > 160:
                    stage = "Down"
                if angle < 45 and stage == "Down":
                    stage = "Up"
                    counter += 1

            except Exception as e:
                # في حال عدم اكتشاف نقاط الجسم
                pass

            # عرض عدد التكرارات والحالة على الإطار
            cv2.rectangle(image, (0, 0), (235, 73), (245, 117, 16), -1)
            cv2.putText(image, "REPS", (15, 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter), (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(image, "STAGE", (75, 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(image, stage if stage is not None else "", (80, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

            # رسم نقاط الجسم والاتصالات باستخدام MediaPipe
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=4, circle_radius=4),
                                          mp_drawing.DrawingSpec(color=(0, 0, 0), thickness=4, circle_radius=3))

            # حساب وعرض معدل الإطارات (FPS)
            ctime = time.time()
            fps = 1 / (ctime - ptime) if (ctime - ptime) > 0 else 0
            ptime = ctime
            cv2.putText(image, f"FPS: {int(fps)}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # ترميز الإطار بصيغة JPEG وإرساله
            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    # هذه الدالة تبث الإطارات المُعالجة باستخدام MJPEG
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
