"""
Given text files or text from stdin, simulates keyboard events that type the
text character-by-character.
"""
import sys

sys.path.append('../')
import fileinput

import directkeys

for line in fileinput.input():
	directkeys.write(line)
