"""
Given text files or text from stdin, simulates keyboard events that type the
text character-by-character.
"""
import sys
sys.path.append('../')
import directkeys
import fileinput

for line in fileinput.input():
	directkeys.write(line)