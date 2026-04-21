import math
import threading
import time
import cv2

from constants import GESTURE_PROFILES

try:
    import mediapipe as mp
    HAS_GESTURE_STACK = True
except Exception:
    HAS_GESTURE_STACK = False

try:
    import speech_recognition as sr
    HAS_VOICE_STACK = True
except Exception:
    HAS_VOICE_STACK = False


class GestureController:
    def __init__(self):
        self.left = False
        self.right = False
        self.jump = False
        self.attack = False
        self.active = False
        self.hand_side = "none"
        self.camera_ready = False
        self.camera_error = ""
        self._thread = None
        self._stop = False
        self._cap = None
        self._last_pinch = False
        self._last_index_y = None
        self._last_jump_at = 0.0
        self._last_attack_at = 0.0
        self.stump_x = 0.5
        self.stump_y = 0.5
        self._smooth_x = None
        self._smooth_y = None
        self.profile = GESTURE_PROFILES[1]

    def set_profile(self, profile):
        self.profile = profile

    def start(self):
        if not HAS_GESTURE_STACK:
            self.camera_error = "opencv/mediapipe manquants"
            return False
        self._cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self.camera_error = "camera non ouverte"
            return False
        self.camera_ready = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._stop = True
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def consume_jump(self):
        if self.jump:
            self.jump = False
            return True
        return False

    def consume_attack(self):
        if self.attack:
            self.attack = False
            return True
        return False

    def _run(self):
        mp_hands = mp.solutions.hands
        with mp_hands.Hands(
            static_image_mode=False,
            model_complexity=0,
            max_num_hands=1,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.45,
        ) as hands:
            while not self._stop:
                ok, frame = self._cap.read() if self._cap is not None else (False, None)
                if not ok:
                    time.sleep(0.03)
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = hands.process(rgb)

                self.left = False
                self.right = False
                self.active = False
                self.hand_side = "none"

                if res.multi_hand_landmarks and res.multi_handedness:
                    handed = res.multi_handedness[0].classification[0].label
                    self.hand_side = handed
                    lm = res.multi_hand_landmarks[0].landmark
                    now = time.time()

                    if handed == "Right":
                        self.active = True
                        index_tip = lm[8]
                        thumb_tip = lm[4]
                        
                        alpha = 0.35
                        if self._smooth_x is None:
                            self._smooth_x = index_tip.x
                        else:
                            self._smooth_x = alpha * index_tip.x + (1 - alpha) * self._smooth_x
                        
                        if self._smooth_y is None:
                            self._smooth_y = index_tip.y
                        else:
                            self._smooth_y = alpha * index_tip.y + (1 - alpha) * self._smooth_y

                        self.stump_x = self._smooth_x
                        self.stump_y = self._smooth_y

                        if self.profile.get("is_spatial"):
                            if self._smooth_x < self.profile["move_left"]:
                                self.left = True
                            if self._smooth_x > self.profile["move_right"]:
                                self.right = True
                            
                            if self._smooth_y < self.profile["jump_y"] and now - self._last_jump_at > self.profile["jump_cd"]:
                                self.jump = True
                                self._last_jump_at = now
                            
                            if self._smooth_y > self.profile["attack_y"] and now - self._last_attack_at > self.profile["attack_cd"]:
                                self.attack = True
                                self._last_attack_at = now
                        else:
                            if self._smooth_x < self.profile["move_left"]:
                                self.left = True
                            if self._smooth_x > self.profile["move_right"]:
                                self.right = True
    
                            pinch = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y) < self.profile["pinch"]
                            if pinch and not self._last_pinch and now - self._last_jump_at > self.profile["jump_cd"]:
                                self.jump = True
                                self._last_jump_at = now
                            self._last_pinch = pinch
    
                            if self._last_index_y is not None:
                                dy = index_tip.y - self._last_index_y
                                strong_swipe_up = dy < self.profile["swipe"]
                                if strong_swipe_up and not pinch and now - self._last_attack_at > self.profile["attack_cd"]:
                                    self.attack = True
                                    self._last_attack_at = now
                            self._last_index_y = index_tip.y
                    else:
                        self._last_pinch = False
                        self._last_index_y = None
                else:
                    self._last_pinch = False
                    self._last_index_y = None

                cv2.waitKey(1)


class VoiceController:
    def __init__(self):
        self.active = False
        self.error = ""
        self._thread = None
        self._stop = False
        self._lock = threading.Lock()
        self._commands = []

    def start(self):
        if not HAS_VOICE_STACK:
            self.error = "speech_recognition manquant"
            return False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._stop = True

    def pop_commands(self):
        with self._lock:
            cmds = self._commands[:]
            self._commands.clear()
        return cmds

    def _push(self, txt):
        with self._lock:
            self._commands.append(txt)

    def _run(self):
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone(sample_rate=44100) as source:
                self.active = True
                try:
                    recognizer.adjust_for_ambient_noise(source, duration=0.8)
                except Exception:
                    pass
                while not self._stop:
                    try:
                        audio = recognizer.listen(source, timeout=0.8, phrase_time_limit=3.0)
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as exc:
                        self.error = f"listen: {exc}"
                        continue

                    try:
                        text = recognizer.recognize_google(audio, language="fr-FR").lower().strip()
                        if text:
                            print(f"[Vocal] Commande reconnue : '{text}'")
                            self._push(text)
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        self.error = f"Service Google indisponible; {e}"
                        continue
                    except Exception:
                        continue
        except Exception as exc:
            self.error = f"micro indisponible: {exc}"
            print(f"[Vocal] Erreur critique micro : {exc}")
            self.active = False
