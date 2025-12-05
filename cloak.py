import cv2
import numpy as np
import time

print("""
-----------------------------------------
      MAGIC CLOAK - VERSION 5.0 
-----------------------------------------
Controls:
G → Ghost Mode
T → Transparent Glass Mode
N → Normal Invisibility
ESC → Exit

Use ANY cloth color. Tune HSV sliders.
-----------------------------------------
""")

# -------------------------------
# STEP 1: Capture Background Frame
# -------------------------------
cam = cv2.VideoCapture(0)
time.sleep(2)

print("Capturing high-quality background, do not move...")

bg_frames = []
for _ in range(80):  # more frames → cleaner background
    ret, frame = cam.read()
    if ret:
        frame = np.flip(frame, axis=1)
        bg_frames.append(frame)

# More stable background using mean & denoise
background = np.median(bg_frames, axis=0).astype(np.uint8)
background = cv2.GaussianBlur(background, (21, 21), 0)

print("Background captured successfully!")

# -----------------------------------
# STEP 2: Create Color Range Controls
# -----------------------------------
def nothing(x):
    pass

cv2.namedWindow("Cloak Controls")

cv2.createTrackbar("LH", "Cloak Controls", 0,   180, nothing)
cv2.createTrackbar("LS", "Cloak Controls", 50,  255, nothing)
cv2.createTrackbar("LV", "Cloak Controls", 40,  255, nothing)

cv2.createTrackbar("UH", "Cloak Controls", 180, 180, nothing)
cv2.createTrackbar("US", "Cloak Controls", 255, 255, nothing)
cv2.createTrackbar("UV", "Cloak Controls", 255, 255, nothing)

mode = "normal"  # normal / ghost / transparent

# For FPS counter
prev_time = time.time()

# -----------------------------------
# STEP 3: Real-Time Cloak Effect
# -----------------------------------
while cam.isOpened():

    ret, frame = cam.read()
    if not ret:
        break

    frame = np.flip(frame, axis=1)

    # Normalize lighting → smoother detection
    frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Read slider values
    lh = cv2.getTrackbarPos("LH", "Cloak Controls")
    ls = cv2.getTrackbarPos("LS", "Cloak Controls")
    lv = cv2.getTrackbarPos("LV", "Cloak Controls")

    uh = cv2.getTrackbarPos("UH", "Cloak Controls")
    us = cv2.getTrackbarPos("US", "Cloak Controls")
    uv = cv2.getTrackbarPos("UV", "Cloak Controls")

    lower = np.array([lh, ls, lv])
    upper = np.array([uh, us, uv])

    # Primary mask
    mask = cv2.inRange(hsv, lower, upper)

    # ---------------- SMOOTHER MASK ----------------
    kernel_small = np.ones((5, 5), np.uint8)
    kernel_large = np.ones((9, 9), np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_small)
    mask = cv2.dilate(mask, kernel_large, iterations=1)
    mask = cv2.GaussianBlur(mask, (31, 31), 0)

    mask_inv = cv2.bitwise_not(mask)

    # Cloak background fill
    cloak_bg = cv2.bitwise_and(background, background, mask=mask)
    normal = cv2.bitwise_and(frame, frame, mask=mask_inv)

    # ---------------- MODE EFFECTS ----------------
    if mode == "ghost":
        # Semi-transparent cloak effect
        alpha = 0.55
        cloak_effect = cv2.addWeighted(cloak_bg, alpha, frame, 1 - alpha, 0)

    elif mode == "transparent":
        # Glass-like effect → more frame visibility
        alpha = 0.75
        cloak_effect = cv2.addWeighted(cloak_bg, alpha, frame, 1 - alpha, 0)

        # Add soft bloom on edges
        edges = cv2.Canny(mask, 50, 150)
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        cloak_effect = cv2.addWeighted(cloak_effect, 1, edges_colored, 0.20, 0)

    else:  
        # Normal invisibility
        cloak_effect = cloak_bg

    # Combine everything
    final_output = cv2.add(cloak_effect, normal)

    # ---------- FPS CALCULATION ----------
    current_time = time.time()
    fps = int(1 / (current_time - prev_time))
    prev_time = current_time

    # Display text
    cv2.putText(final_output, f"MODE: {mode.upper()}", (20, 40),
                cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)

    cv2.putText(final_output, f"FPS: {fps}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 200), 2)

    cv2.imshow("Invisibility Cloak 5.0", final_output)

    # Key handling
    key = cv2.waitKey(1)

    if key == 27:   # ESC
        break

    if key == ord('g'):
        mode = "ghost"
        print("Ghost Mode Activated!")

    if key == ord('t'):
        mode = "transparent"
        print("Transparent Cloak Activated!")

    if key == ord('n'):
        mode = "normal"
        print("Normal Mode Activated!")

cam.release()
cv2.destroyAllWindows()
