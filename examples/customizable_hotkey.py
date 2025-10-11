import directkeys

print('Press and release your desired shortcut: ')
shortcut = directkeys.read_hotkey()
print('Shortcut selected:', shortcut)

def on_triggered():
	print("Triggered!")
directkeys.add_hotkey(shortcut, on_triggered)

print("Press ESC to stop.")
directkeys.wait('esc')
