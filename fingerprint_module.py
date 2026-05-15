import serial
import time


class FingerprintModule:
    def __init__(self, port="COM16", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.arduino = None

    def connect(self):
        try:
            if self.arduino and self.arduino.is_open:
                return True
        except:
            pass

        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            print("[FINGERPRINT] Arduino connected")
            return True
        except Exception as e:
            print("[FINGERPRINT] Connection error:", e)
            return False

    def read_fingerprint_id(self):
        if not self.connect():
            return None

        try:
            data = self.arduino.readline().decode(errors="ignore").strip()

            if data:
                print("[FINGERPRINT]", data)

                if data.startswith("ID:"):
                    return int(data.split(":")[1])

        except Exception as e:
            print("[FINGERPRINT] Read error:", e)

        return None
    #enroll fingerprint
    
    def enroll_fingerprint(self, fingerprint_id, callback=None):
        if not self.connect():
            return False

        try:
            self.arduino.write(f"ENROLL:{fingerprint_id}\n".encode())

            while True:
                data = self.arduino.readline().decode(errors="ignore").strip()

                if data:
                    print("[FINGERPRINT]", data)

                    if callback:
                        callback(data)

                    if data == "ENROLL_SUCCESS":
                        return True

                    if data == "ENROLL_FAILED":
                        return False

        except Exception as e:
            print("[FINGERPRINT] Enroll error:", e)
            return False

    def close(self):
        try:
            if self.arduino and self.arduino.is_open:
                self.arduino.close()
        except:
            pass


fingerprint_module = FingerprintModule()