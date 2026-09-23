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
