import cv2
import numpy as np
import mediapipe as mp
import pyautogui

# Virtual Keyboard Button Class
class Button:
    def __init__(self, pos, text, size=[60, 60]):
        self.pos = pos
        self.text = text
        self.size = size

    def draw(self, img, hover=False):
        x, y = self.pos
        w, h = self.size
        color = (0, 255, 0) if hover else (255, 0, 0)
        cv2.rectangle(img, (x, y), (x + w, y + h), color, cv2.FILLED)

        # Center the text
        (text_w, text_h), _ = cv2.getTextSize(self.text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
        text_x = x + (w - text_w) // 2
        text_y = y + (h + text_h) // 2
        cv2.putText(img, self.text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255) if not hover else (0, 0, 0), 2)

    def is_hover(self, x, y):
        btn_x, btn_y = self.pos
        w, h = self.size
        return btn_x < x < btn_x + w and btn_y < y < btn_y + h

# Setup
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

screen_width, screen_height = pyautogui.size()

# Create keyboard layout
keys = list("QWERTYUIOPASDFGHJKLZXCVBNM")
buttons = []
start_x, start_y = 100, 350
gap = 10

# Add alphabet keys
for i, key in enumerate(keys):
    x = start_x + (i % 10) * (60 + gap)
    y = start_y + (i // 10) * (60 + gap)
    buttons.append(Button([x, y], key))

# Add control keys
buttons += [
    Button([start_x, start_y + 3 * (60 + gap)], "Shift", [100, 60]),
    Button([start_x + 110, start_y + 3 * (60 + gap)], "Space", [240, 60]),
    Button([start_x + 360, start_y + 3 * (60 + gap)], "Backspace", [160, 60]),
    Button([start_x + 530, start_y + 3 * (60 + gap)], "Enter", [100, 60])
]

# MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=0  
)
mp_draw = mp.solutions.drawing_utils

# States
click_cooldown = 0
keyboard_cooldown = 0
is_shift = False

# ------------------------------
# Main Loop
# ------------------------------
while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    # Draw keyboard
    for button in buttons:
        button.draw(img)

    # Process Hand
    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            lm = handLms.landmark

            x1, y1 = int(lm[8].x * w), int(lm[8].y * h)    
            x2, y2 = int(lm[4].x * w), int(lm[4].y * h)    
            x3, y3 = int(lm[12].x * w), int(lm[12].y * h)  

            cv2.circle(img, (x1, y1), 10, (255, 0, 255), cv2.FILLED)
            pyautogui.moveTo(screen_width * lm[8].x, screen_height * lm[8].y)

            dist_click = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            key_hovered = None

            for button in buttons:
                if button.is_hover(x1, y1):
                    key_hovered = button
                    button.draw(img, hover=True)

            # Pinch over button
            if dist_click < 30 and keyboard_cooldown == 0 and key_hovered:
                key = key_hovered.text
                if key == "Shift":
                    is_shift = not is_shift
                elif key == "Space":
                    pyautogui.write(' ')
                elif key == "Backspace":
                    pyautogui.press('backspace')
                elif key == "Enter":
                    pyautogui.press('enter')
                else:
                    char = key.upper() if is_shift else key.lower()
                    pyautogui.write(char)

                keyboard_cooldown = 20
                cv2.putText(img, f"Typed: {key}", (50, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Click gesture
            elif dist_click < 30 and click_cooldown == 0 and not key_hovered:
                pyautogui.click()
                click_cooldown = 20
                cv2.putText(img, "Click", (50, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Scroll gestures
            if key_hovered is None:
                if lm[8].y < lm[6].y and lm[12].y < lm[10].y:
                    pyautogui.scroll(20)
                    cv2.putText(img, "Scroll Up", (50, 130),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    
                # Thumbs Up Gesture for Scroll Down (using thumb extended)
                if lm[4].y < lm[3].y and lm[8].y > lm[6].y and lm[12].y > lm[10].y and lm[16].y > lm[14].y:
                    pyautogui.scroll(-20)
                    cv2.putText(img, "Scroll Down (Thumbs Up)", (50, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    # Reduce cooldowns
    if click_cooldown > 0:
        click_cooldown -= 1
    if keyboard_cooldown > 0:
        keyboard_cooldown -= 1

    # Display
    cv2.imshow("Virtual Combo Controller", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
