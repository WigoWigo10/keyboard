# run_test_2a_crash.py
import keyboard
import sys
import time

print("--- INICIANDO TESTE 2A: Simulação de Falha ---")
print("Pressionando e segurando 'Left Ctrl' por 1 segundo...")

# Pressiona a tecla 'left ctrl' mas NUNCA a solta.
keyboard.press('left ctrl')
time.sleep(1)

print("!!! SCRIPT ENCERRADO ABRUPTAMENTE !!!")
# O sys.exit() simula um crash. O bloco 'finally' não será executado.
sys.exit(0)