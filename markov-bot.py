print('------')
print("Logging in now...")
import discord
import asyncio

import sqlite3, copy, random, traceback, collections, urllib.request, urllib, json, sys, time
sys.path.append(".")
import mask
con = sqlite3.connect("markov.db")
con.execute("CREATE TABLE IF NOT EXISTS main (key TEXT, value TEXT, count INTEGER);")
con.execute("CREATE TABLE IF NOT EXISTS emotes (key TEXT, value TEXT);")
con.execute("CREATE INDEX IF NOT EXISTS the_index ON main (key, value)")
con.execute("CREATE INDEX IF NOT EXISTS the_other_index ON emotes (key)")

client = discord.Client()
keys = []

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
      con.execute("INSERT INTO main (key, value, count) VALUES (?, ?, ?)", [words[i], words[i + 1], 1])
    else:
      con.execute("UPDATE main SET count = count + 1 WHERE key = ? AND value = ?", [words[i], words[i + 1]])
  con.commit()

def random_word():
  #return con.execute("SELECT key FROM main ORDER BY RANDOM() LIMIT 1;").fetchone()[0]
  count = con.execute("SELECT COUNT(*) FROM main").fetchone()[0]
  index = random.randint(0, count)
  return con.execute("SELECT key FROM main LIMIT 1 OFFSET " + str(index)).fetchone()[0]

async def react(message, success):
  emoji = "✅" if success else "❎"
  if message.channel.permissions_for(message.server.me).add_reactions:
    print("Permission to react, reacting")
    try:
      await client.add_reaction(message, emoji)
    except:
      await client.send_message(message.channel, "Failed to react with " + emoji)
      await client.send_message(message.channel, "```" + traceback.format_exc() + "```")
  else:
    print("No permission to react, sending message")
    client.send_message(message.channel, "No permission to react with " + emoji);
async def notify_pref(message, split):
  try:
    print("Sending request...")
    urllib.request.urlopen("http://api.nanoshinono.me:6405/status_recv", data = urllib.parse.urlencode({"message": json.dumps(split)}).encode("utf-8"));
    await react(message, True)
  except:
    if "prefetcher" in str(message.author).lower() or "helvetica toast" in str(message.author).lower():
      await client.send_message(message.channel, "```" + traceback.format_exc() + "```");
    await react(message, False)

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
  msg = msg.replace("><", "> <")
  msg = msg.split();
  for word in msg:
    if word.startswith("<:"):
      word = word.split(">")[0] + ">"
      if len(con.execute("SELECT 1 FROM emotes WHERE value = ?", [word]).fetchall()) == 0:
        print("found BRAND NEW EMOTE!!! " + word)
        con.execute("INSERT INTO emotes (key, value) VALUES (?, ?)", [word.split(":")[1], word])
        con.commit()

async def send_emotes(message, s):
  res = con.execute("SELECT DISTINCT value FROM emotes WHERE key LIKE ?", ["%" + s + "%"]).fetchall()
  res = [x[0] for x in res]
  while len(res) > 0:
    emotes = "".join(res[:20])
    res = res[20:]
    print(emotes)
    await client.send_message(message.channel, ":`:" + emotes + ":`:")

@client.event
async def on_message(message):
  start = time.time()
  #print("Author: ", message.author, type(message.author))
  #print("Channel: ", message.channel, type(message.channel))
  if (message.author.bot):
    print("DISCARDING BOT MESSAGE FROM ", message.author)
    return
  if type(message.channel) == discord.channel.PrivateChannel:
    print("DISCARDING PRIVATE MESSAGE FROM", message.author)
    return
  if "markov-bot" in str(message.author) or "MikuBot" in str(message.author):
    print("Discarding self message")
    return
  print("Got message on channel ", message.channel, "from author", message.author, ":", message.content)
  split = message.content.split()
  if len(split) == 0: return
  if split[0] in ["?femboy", "?tomboy"]:
    if "welcome-center" in str(message.channel):
      await client.send_message(message.server.get_channel('308342435430400012'), "Welcome <@" +str(message.author.id) + ">!");
  elif split[0] == "!down":
    await notify_pref(message, split)
    pass
  elif split[0] == "!help":
    await client.send_message(message.channel, "Commands: `!markov` - Generates random text based on collected probabilities\n`!markov <starting word>` - Generates starting from a particular word\n`!markov <limit>` - Generates random text with the given length\n`!percents <word>` - Shows statistics on the given word\n`!emote` - Picks a random emote and sends it\n`!emotes` - Dumps all emotes\n`!mask <message>` - Misspells some text\n`!mask10 <message>` - Misspells some text 10 times")
  elif split[0] == "!markov":
    await client.send_typing(message.channel)
    args = message.content.split()
    arg = False
    if len(args) > 1:
      arg = args[1]
    print("Sending")
    await client.send_message(message.channel, make_message(arg))
  elif split[0] == "!percents" and len(split) > 1:
    percents = get_percents(split[1])
    await client.send_message(message.channel, percents)
  elif split[0] == "!mask":
    await client.send_message(message.channel, mask.mask(" ".join(split[1:])))
  elif split[0] == "!mask10":
    msg = []
    curr = mask.mask(" ".join(split[1:]))
    for i in range(10):
      msg.append(curr)
      curr = mask.mask(curr)
    await client.send_message(message.channel, "\n".join(msg))
  elif split[0] == "!emotes":
    s = ""
    if len(split) != 1: s = split[1]
    count = con.execute("SELECT COUNT(*) FROM emotes WHERE key LIKE ?", ["%" + s + "%"]).fetchall()[0][0]
    if count == 0:
      await client.send_message(message.channel, "No results");
    elif count > 30:
      key = str(random.randint(0, 9999)).rjust(4, "0")
      keys.append([key, lambda m: send_emotes(m, s)])
      await client.send_message(message.channel, "There are " + str(count) + " emotes. Type " + key + " to confirm");
    else:
      await send_emotes(message, s)
  elif split[0] == "!emote":
    count = con.execute("SELECT COUNT(*) FROM emotes", []).fetchall()[0][0]
    index = random.randint(0, count)
    emote = con.execute("SELECT DISTINCT value FROM emotes LIMIT 1 OFFSET " + str(index), []).fetchall()[0][0]
    await client.send_message(message.channel, ":`:" + emote + ":`:");
  elif len(split) == 1:
    for key in keys:
      if key[0] == split[0]:
        keys.remove(key)
        await key[1](message)
        return;
    #if split[0] in ["no", "yes", "yeah", "rip", "oh", "hehe", "xd", "xD", "ayy", "lol", "what", "y", "n", "s", "waitwhat", "oof", "ok", "lmao", "Yes", "Nice"]: return;
    if split[0][0] == ":" and split[0][-1] == ":":
      split[0] = split[0][1:-1] # :xd: => xd
      res = con.execute("SELECT value FROM emotes WHERE key = ?", [split[0]]).fetchall()
      if len(res) != 0:
        await client.send_message(message.channel, ":`:"+res[0][0]+":`:")
  else:
    markov_add(message.content);
  parse_emotes(message.content);
  print("Took " + str(time.time() - start) + " seconds to process message of " + str(len(split)) + " words");

