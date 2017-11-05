import discord
import asyncio

import sqlite3, copy, random, traceback, collections
con = sqlite3.connect("markov.db")
con.execute("CREATE TABLE IF NOT EXISTS main (key TEXT, value TEXT, count INTEGER);")
con.execute("CREATE TABLE IF NOT EXISTS emotes (key TEXT, value TEXT);")

client = discord.Client()

def allowed(x):
  if x == "🛑": return False
  if x == ":octagonal_sign:": return False
  if x[0] == "<" and x[1] == "@": return False
  if x == "!markov": return False
  return True

def make_ok(x):
  return [x for x in x if allowed(x)]

def markov_add(m):
  words = m.split()
  words = make_ok(words)
  for i in range(len(words) - 1):
    exists = con.execute("SELECT count FROM main WHERE key = ? AND value = ?", [words[i], words[i + 1]]).fetchall()
    if len(exists) == 0:
      #db.Insert("main", key = words[i], value = [words[i + 1]])
      con.execute("INSERT INTO main (key, value, count) VALUES (?, ?, ?)", [words[i], words[i + 1], 1])
    else:
      con.execute("UPDATE main SET value = value + 1 WHERE key = ? AND value = ?", [words[i], words[i + 1]])
      #new_value = copy.deepcopy(exists[0]["value"])
      #new_value.append(words[i + 1])
      #db.Update("main", exists, value = new_value)
  con.commit()

def random_word():
  #return random.choice(db.Dump("main"))["key"]

  #total = int(con.execute("SELECT COUNT(*) FROM main").fetchall()[0][0])
  #where = random.randint(1, total)
  #return con.execute("SELECT key FROM main LIMIT 1 OFFSET " + str(where)).fetchone()[0]

  return con.execute("SELECT key FROM main ORDER BY RANDOM() LIMIT 1;").fetchone()[0]

def make_message(arg = False):
  message = []
  debug = arg == "debug"
  #debug = True
  word = False;
  length = 20
  if arg:
    try:
      arg = int(arg)
      length = min(arg, 300)
      print("Set length to arg " + str(length))
    except:
      word = arg
      print("Set initial word to arg " + word)
  if not word: word = random_word()
  for x in range(length):
    message.append(word)
    try:
      #word = random.choice(db.Select("main", key = word)[0]["value"])
      words = con.execute("SELECT value, count FROM main WHERE key = ?", [word]).fetchall()
      words = [[x[0]] * int(x[1]) for x in words]
      flattened = []
      for x in words: flattened += x;
      word = random.choice(flattened)
    except:
      print(traceback.format_exc())
      print("failed to find next word for " + word)
      if debug: message.append(":octagonal_sign:")
      word = random_word();
  message = make_ok(message)
  return " ".join(message)

def get_percents(word):
  #raw = db.Select("main", key = word)
  words = con.execute("SELECT value, count FROM main WHERE key = ?", [word]).fetchall()
  if len(words) == 0: return "Never seen that word before"
  words = [[x[0], int(x[1])] for x in words]
  total = sum([x[1] for x in words])
  words.sort(key = lambda x: x[1], reverse = True)
  print(words[:10])
  message = []
  for block in words:
    if len(message) > 10: break
    message.append(block[0] + ": " + str(float(block[1] * 100)/total)[:4] + "%")
  return ", ".join(message) + "\nWord seen " + str(total) + " time" + ("s" if total != 1 else "")

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(client.user.id)
  print('------')

def parse_emotes(msg):
  msg = msg.split();
  for word in msg:
    if word.startswith("<:"):
      #if len(db.Select("emotes", value = word)) == 0:
      if len(con.execute("SELECT * FROM emotes WHERE value = ?", [word]).fetchall()) == 0:
        print("found BRAND NEW EMOTE!!! " + word)
        con.execute("INSERT INTO emotes (key, value) VALUES (?, ?)", [word.split(":")[1], word])
        con.commit()
        #db.Insert("emotes", key = word.split(":")[1], value = word)

@client.event
async def on_message(message):
  print("Got message on channel ", message.channel, "from author", message.author, ":", message.content)
  #print("Author: ", message.author, type(message.author))
  #print("Channel: ", message.channel, type(message.channel))
  if type(message.channel) == discord.channel.PrivateChannel:
    print("DISCARDING PRIVATE MESSAGE FROM", message.author)
    return
  if "markov-bot" in str(message.author) or "MikuBot" in str(message.author):
    print("Discarding self message")
    return
  split = message.content.split()
  if len(split) == 0: return
  if split[0] == "!help":
    await client.send_message(message.channel, "Commands: `!markov` - Generates random text based on collected probabilities\n`!markov <starting word>` - Generates starting from a particular word\n`!markov <limit>` - Generates random text with the given length\n`!percents <word>` - Shows statistics on the given word")
  elif split[0] == "!markov":
    args = message.content.split()
    arg = False
    if len(args) > 1:
      arg = args[1]
    print("Sending")
    await client.send_message(message.channel, make_message(arg))
  elif split[0] == "!percents" and len(split) > 1:
    percents = get_percents(split[1])
    await client.send_message(message.channel, percents)
  elif split[0] == "!emotes":
    await client.send_message(message.channel, " ".join([x[0] for x in con.execute("SELECT value FROM emotes;").fetchall()]))
  elif len(split) == 1:
    if split[0] in ["no", "yes"]: return;
    #res = db.Select("emotes", key = split[0])
    res = con.execute("SELECT value FROM emotes WHERE key = ?", [split[0]]).fetchall()
    if len(res) != 0:
      #await client.send_message(message.channel, res[0]["value"])
      await client.send_message(message.channel, res[0][0])
  else:
    markov_add(message.content);
  parse_emotes(message.content);

