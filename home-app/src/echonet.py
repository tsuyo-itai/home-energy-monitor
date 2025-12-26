import socket
import threading
import time
import binascii
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ECHONET_PORT = 3610
TARGET_IP = "192.168.11.10" # As per user example

# Commands from user
CMD_SMART_METER = bytes.fromhex("10810BDB0287010287016201C600")
CMD_SOLAR = bytes.fromhex("10810BDA0279010279016201E000")

class EchonetClient:
    def __init__(self, target_ip=TARGET_IP, mock=False):
        self.target_ip = target_ip
        self.mock = mock
        self.consumption = 0
        self.generation = 0
        self.last_updated = 0
        self.running = False
        self.lock = threading.Lock()
        
        # Mock data state
        self._mock_cons_dir = 1
        self._mock_gen_dir = 1

    def parse_smart_meter_response(self, data):
        try:
            # Expecting response to Get(62) -> Get_Res(72).
            # Structure: 10 81 TID(2) SEOJ(3) DEOJ(3) ESV(1) OPC(1) EPC(1) PDC(1) EDT(PDC)
            # Fixed header size before data is 14 bytes.
            # EPC C6 is 4 bytes. Total length should be 18 bytes.
            if len(data) >= 18:
                val = int.from_bytes(data[14:18], 'big', signed=True)
                return val
        except Exception as e:
            logger.error(f"Error parsing smart meter response: {e}")
        return None

    def parse_solar_response(self, data):
        try:
            # EPC E0 is 2 bytes (PDC=02) based on logs. Total length should be 16 bytes.
            if len(data) >= 16:
                val = int.from_bytes(data[14:16], 'big')
                return val
        except Exception as e:
            logger.error(f"Error parsing solar response: {e}")
        return None

    def loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', 3610))
        
        logger.info(f"Started Echonet polling loop. Target: {self.target_ip}")
        
        while self.running:
            if self.mock:
                self._update_mock_data()
                time.sleep(5)
                continue

            # ----- Smart Meter Request -----
            try:
                logger.debug(f">> SEND SmartMeter: {CMD_SMART_METER.hex()}")
                # Also log at INFO level as requested "per communication"
                logger.info(f"TX [SmartMeter] -> {self.target_ip}: {CMD_SMART_METER.hex()}")
                
                sock.sendto(CMD_SMART_METER, (self.target_ip, ECHONET_PORT))
                try:
                    data, addr = sock.recvfrom(1024)
                    logger.info(f"RX [SmartMeter] <- {addr[0]}: {data.hex()}")
                    
                    val = self.parse_smart_meter_response(data)
                    if val is not None:
                        with self.lock:
                            self.consumption = val
                            self.last_updated = time.time()
                except socket.timeout:
                    logger.warning("RX [SmartMeter]: Timed out waiting for response.")
                except Exception as e:
                     logger.error(f"RX [SmartMeter]: Error receiving data: {e}")

            except Exception as e:
                logger.error(f"TX [SmartMeter]: Socket error: {e}")
                # Backoff slightly on error
                time.sleep(1)

            time.sleep(0.5) 

            # ----- Solar Request -----
            try:
                logger.info(f"TX [Solar] -> {self.target_ip}: {CMD_SOLAR.hex()}")
                sock.sendto(CMD_SOLAR, (self.target_ip, ECHONET_PORT))
                try:
                    data, addr = sock.recvfrom(1024)
                    logger.info(f"RX [Solar] <- {addr[0]}: {data.hex()}")
                    
                    val = self.parse_solar_response(data)
                    if val is not None:
                        with self.lock:
                            self.generation = val
                            self.last_updated = time.time()
                except socket.timeout:
                    logger.warning("RX [Solar]: Timed out waiting for response.")
                except Exception as e:
                    logger.error(f"RX [Solar]: Error receiving data: {e}")

            except Exception as e:
                 logger.error(f"TX [Solar]: Socket error: {e}")

            
            time.sleep(5)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False


    def _update_mock_data(self):
        with self.lock:
            # Random walk for demo
            change_cons = 100 * self._mock_cons_dir
            self.consumption += change_cons
            if self.consumption > 3000: self._mock_cons_dir = -1
            if self.consumption < -2000: self._mock_cons_dir = 1
            
            change_gen = 150 * self._mock_gen_dir
            self.generation += change_gen
            if self.generation > 4500: self._mock_gen_dir = -1
            if self.generation < 0: 
                self.generation = 0
                self._mock_gen_dir = 1
            
            self.last_updated = time.time()
            logger.info(f"MOCK DATA: Cons={self.consumption}, Gen={self.generation}")

    def get_data(self):
        with self.lock:
            return {
                "consumption": self.consumption,
                "generation": self.generation,
                "last_updated": self.last_updated
            }
