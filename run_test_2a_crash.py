# run_test_2a_crash.py
import directkeys
import sys
import time

print("--- INICIANDO TESTE 2A: Simulação de Falha ---")
print("Pressionando e segurando 'Left Ctrl' por 1 segundo...")

# Pressiona a tecla 'left ctrl' mas NUNCA a solta.
directkeys.press('left ctrl')
time.sleep(1)

print("!!! SCRIPT ENCERRADO ABRUPTAMENTE !!!")
# O sys.exit() simula um crash. O bloco 'finally' não será executado.
sys.exit(0)