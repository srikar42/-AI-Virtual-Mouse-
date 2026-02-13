import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
import pyautogui

# ---------------- SETTINGS ----------------
wCam, hCam = 640, 480
displayW, displayH = 590, 512
frameR = 40
smoothening = 7


pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0
dragging = False

lastScreenshotTime = 0
showScreenshotMsg = 0
screenshotHoldStart = 0   

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()

while True:

    success, img = cap.read()
    if not success or img is None:
        continue

    actionText = "READY"

    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    if len(lmList) != 0:

        x1, y1 = lmList[8][1:]   # Index
        fingers = detector.fingersUp()
        # fingers = [Thumb, Index, Middle, Ring, Pinky]

        # CONTROL FRAME
        cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),(255, 0, 255), 2)
        
        # -------- MOVE --------
        if fingers == [0, 1, 0, 0, 0]:
            actionText = "MOVE"
            x3 = np.interp(x1, (frameR, wCam-frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam-frameR), (0, hScr))

            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            autopy.mouse.move(wScr - clocX, clocY)
            plocX, plocY = clocX, clocY

        # -------- LEFT CLICK --------
        elif fingers == [0, 1, 1, 0, 0]:
            length, img, _ = detector.findDistance(8, 12, img)
            if length < 40:
                autopy.mouse.click()
                actionText = "LEFT CLICK"

        # -------- RIGHT CLICK --------
        elif fingers == [1, 1, 0, 0, 0]:
            length, img, _ = detector.findDistance(4, 8, img)
            if length < 40:
                autopy.mouse.click(button=autopy.mouse.Button.RIGHT)
                actionText = "RIGHT CLICK"
                time.sleep(0.2)

        # -------- DOUBLE CLICK --------
        elif fingers == [0, 1, 1, 1, 0]:
            autopy.mouse.click()
            autopy.mouse.click()
            actionText = "DOUBLE CLICK"
            time.sleep(0.2)

        # -------- SCROLL UP --------
        elif fingers == [0, 1, 1, 0, 1]:
            pyautogui.scroll(50)
            actionText = "SCROLL UP"

        # -------- SCROLL DOWN --------
        elif fingers == [0, 1, 0, 0, 1]:
            pyautogui.scroll(-50)
            actionText = "SCROLL DOWN"

        # -------- DRAG & DROP --------
        else:
            length, img, _ = detector.findDistance(4, 8, img)
            if length < 35 and not dragging:
                dragging = True
                autopy.mouse.toggle(down=True)
                actionText = "DRAGGING"
            elif length > 50 and dragging:
                dragging = False
                autopy.mouse.toggle(down=False)
                actionText = "DROP"

        # -------- SCREENSHOT --------
        
        if fingers[0] == 1 and fingers[2] == 1 and fingers[1] == 0:
            length2, img, _ = detector.findDistance(4, 12, img)

            if length2 < 40:
                if screenshotHoldStart == 0:
                    screenshotHoldStart = time.time()

                elif time.time() - screenshotHoldStart > 0.3:
                    filename = f"screenshot_{int(time.time())}.png"
                    pyautogui.screenshot(filename)
                    actionText = "SCREENSHOT SAVED"
                    showScreenshotMsg = 15
                    lastScreenshotTime = time.time()
                    screenshotHoldStart = 0
            else:
                screenshotHoldStart = 0
        else:
            screenshotHoldStart = 0

    # FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    # TEXT INSIDE PINK BOX
    cv2.putText(img, f"FPS: {int(fps)}",
                (frameR + 5, frameR + 25),
                cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 0, 0), 2)

    cv2.putText(img, f"ACTION: {actionText}",
                (frameR + 5, frameR + 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # SCREENSHOT CONFIRMATION
    if showScreenshotMsg > 0:
        cv2.putText(img, "SCREENSHOT SAVED",
                    (frameR + 5, frameR + 85),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        showScreenshotMsg -= 1

    img_resized = cv2.resize(img, (displayW, displayH))
    cv2.imshow("AI Virtual Mouse", img_resized)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
