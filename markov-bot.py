import discord
import asyncio

import BTEdb, copy, random, traceback, collections
db = BTEdb.Database("markov.json")
if not db.TableExists("main"): db.CreateTable("main")
if not db.TableExists("emotes"):
  db.CreateTable("emotes")
  thing = [x["key"] for x in db.Dump("main") if x["key"].startswith("<:")]
  for emote in thing:
    print("Found emote " + emote.split(":")[1] + " - " + emote)
    db.Insert("emotes", key = emote.split(":")[1], value = emote)

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
  db.BeginTransaction(False)
  for i in range(len(words) - 1):
    exists = db.Select("main", key = words[i])
    if len(exists) == 0:
      db.Insert("main", key = words[i], value = [words[i + 1]])
    else:
      new_value = copy.deepcopy(exists[0]["value"])
      new_value.append(words[i + 1])
      db.Update("main", exists, value = new_value)
    pass
  db.CommitTransaction();

def random_word():
  return random.choice(db.Dump("main"))["key"]

def make_message(arg = False):
  message = []
  debug = arg == "debug"
  #debug = True
  word = random_word();
  length = 20
  if arg:
    try:
      arg = int(arg)
      length = min(arg, 300)
      print("Set length to arg " + str(length))
    except:
      word = arg
      print("Set initial word to arg " + word)
  for x in range(length):
    message.append(word)
    try:
      word = random.choice(db.Select("main", key = word)[0]["value"])
    except:
      print(traceback.format_exc())
      print("failed to find next word for " + word)
      if debug: message.append(":octagonal_sign:")
      word = random_word();
  message = make_ok(message)
  return " ".join(message)

def get_percents(word):
  raw = db.Select("main", key = word)
  if len(raw) == 0: return "Never seen that word before"
  words = collections.defaultdict(lambda: 0)
  total = len(raw[0]["value"])
  for x in raw[0]["value"]:
    words[x] += 1
  as_list = list(words.items())
  as_list.sort(key = lambda x: x[1], reverse = True)
  print(as_list[:10])
  message = []
  for block in as_list:
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
      if len(db.Select("emotes", value = word)) == 0:
        print("found BRAND NEW EMOTE!!! " + word)
        db.Insert("emotes", key = word.split(":")[1], value = word)

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
  if split[0] == "!markov":
    args = message.content.split()
    arg = False
    if len(args) > 1:
      arg = args[1]
    print("Sending")
    await client.send_message(message.channel, make_message(arg))
  elif split[0] == "!percents" and len(split) > 1:
    percents = get_percents(split[1])
    await client.send_message(message.channel, percents)
  elif len(split) == 1:
    if split[0] in ["no"]: return;
    res = db.Select("emotes", key = split[0])
    if len(res) != 0:
      await client.send_message(message.channel, res[0]["value"])
  else:
    markov_add(message.content);
  parse_emotes(message.content);

client.run("yoursecrethereyoursecret.hereyo.ursecrethereyoursecretherey")
