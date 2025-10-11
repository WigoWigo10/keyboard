import directkeys
import time
import subprocess
import sys

def read_next_keydown(suppress=True):
    """
    Função auxiliar que lê eventos em loop até encontrar um KEY_DOWN,
    ignorando os eventos KEY_UP.
    """
    while True:
        event = directkeys.read_event(suppress=suppress)
        if event.event_type == directkeys.KEY_DOWN:
            return event

def test_raw_event_capture():
    """
    Testa a captura de eventos brutos, desabilitando a abstração do AltGr.
    Verifica se a biblioteca captura corretamente o nome, scan code e flags.
    """
    print("\n--- INICIANDO TESTE 1: Captura de Eventos Brutos ---")
    print("!!! ABSTRAÇÃO DE ALTGR DESLIGADA !!!")
    print("Siga as instruções abaixo.")
    print("-" * 50)

    directkeys.set_alt_gr_abstraction(False)
    
    print("1. Pressione e solte 'AltGr'...")
    alt_gr_event = read_next_keydown()
    print(f"   -> Recebido: Tecla='{alt_gr_event.name}', Scan={alt_gr_event.scan_code:#04x}, Flags={alt_gr_event.flags}")
    
    print("\n2. Pressione e solte a tecla '/'...")
    slash_event = read_next_keydown()
    print(f"   -> Recebido: Tecla='{slash_event.name}', Scan={slash_event.scan_code:#04x}, Flags={slash_event.flags}")

    print("\n3. Pressione e solte 'Esc' para validar...")
    esc_event = read_next_keydown()
    print(f"   -> Recebido: Tecla='{esc_event.name}', Scan={esc_event.scan_code:#04x}, Flags={esc_event.flags}")

    print("\nValidando resultados...")
    assert alt_gr_event.name == 'alt gr' and alt_gr_event.scan_code == 0x38 and alt_gr_event.flags == 1, "Falha no teste do AltGr!"
    assert slash_event.name == '/' and slash_event.scan_code == 0x73 and slash_event.flags == 0, "Falha no teste da tecla '/'!"
    assert esc_event.name == 'esc'

    print("✅ Teste 1: SUCESSO!")
    
    directkeys.set_alt_gr_abstraction(True)

def test_stuck_key_fix():
    """
    Testa a funcionalidade de recuperação de teclas presas, com verificação.
    """
    print("\n--- INICIANDO TESTE 2: Correção de Tecla Presa ---")

    print("--> Passo 2a: Simulando script que trava com 'Ctrl' pressionado...")
    crash_script_path = "run_test_2a_crash.py"
    process = subprocess.Popen([sys.executable, crash_script_path])
    process.wait()
    time.sleep(1)
    print("--> Script travado. A tecla 'Ctrl' deve estar 'presa' no sistema.")
    
    # Verificação inicial (opcional, mas bom para confirmar o problema)
    stuck_before = directkeys.get_stuck_keys()
    if 'ctrl' in stuck_before or 'left ctrl' in stuck_before:
        print(f"   [CONFIRMADO] Teclas presas detectadas: {stuck_before}")
    else:
        print(f"   [AVISO] Não foi possível detectar a tecla 'Ctrl' como presa. O teste continua.")
    
    input("--> Pressione Enter para executar a correção...")

    print("\n--> Passo 2b: Executando a função de correção 'force_reset_keyboard()'...")
    directkeys.force_reset_keyboard()
    print("--> Função executada.")
    
    # Verificação de ressalva
    print("--> Verificando se ainda há teclas presas...")
    stuck_after = directkeys.get_stuck_keys()
    if stuck_after:
        print(f"   [FALHA] As seguintes teclas ainda estão presas: {stuck_after}")
        assert False, f"A função force_reset_keyboard não limpou as seguintes teclas: {stuck_after}"
    else:
        print("   [SUCESSO] Nenhuma tecla modificadora presa foi detectada.")
    
    print("\n✅ Teste 2: SUCESSO!")

if __name__ == "__main__":
    required_script = "run_test_2a_crash.py"
    try:
        with open(required_script, "r") as f: pass
    except FileNotFoundError:
        print(f"\nERRO: O script auxiliar '{required_script}' não foi encontrado.")
        sys.exit(1)

    try:
        test_raw_event_capture()
        test_stuck_key_fix()
    finally:
        print("\n--- Limpeza Final ---")
        directkeys.set_alt_gr_abstraction(True)
        directkeys.force_reset_keyboard()
        directkeys.reset_internal_state()
        directkeys.unhook_all()
        
        # Verificação final de ressalva
        final_stuck_keys = directkeys.get_stuck_keys()
        if final_stuck_keys:
            print(f"   [AVISO FINAL] Após limpeza completa, as seguintes teclas ainda estão presas: {final_stuck_keys}")
        else:
            print("   [SUCESSO FINAL] O teclado foi limpo com sucesso.")
        print("Estado da biblioteca restaurado.")
