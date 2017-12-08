import random, string
keyboard = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
bit = lambda: random.randint(0, 1)
def near(letter):
	if letter not in string.ascii_letters: return letter
	upper = letter.upper() == letter
	letter = letter.lower()
	outer = 0
	inner = 0;
	for row in keyboard:
		if letter in row:
			inner = row.index(letter)
			break;
		outer += 1
	assert(keyboard[outer][inner] == letter)
	r = bit()
	r2 = bit() * 2 - 1
	if r == 0:
		outer += r2
	else:
		inner += r2
	if outer < 0 or outer >= len(keyboard): return near(letter)
	if inner < 0 or inner >= len(keyboard[outer]): return near(letter)
	result = keyboard[outer][inner]
	if upper: result = result.upper()
	return result
def maybe(letter):
	if bit() + bit() + bit() == 0:
		return near(letter)
	return ""
def mask(thing):
	result = ""
	for letter in thing:
		result += maybe(letter)
		result += letter
		result += maybe(letter)
	return result
print(mask("mom's spaghetti"))
