import BTEdb, collections, sqlite3
def get_vals(raw):
  words = collections.defaultdict(lambda: 0)
  for x in raw["value"]:
    words[x] += 1
  as_list = list(words.items())
  return as_list
db = BTEdb.Database("markov.json")
con = sqlite3.connect("markov.db")
for row in db.Dump("main"):
  word = row["key"]
  for newrow in get_vals(row):
    print(word, *newrow)
    con.execute("INSERT INTO main (key, value, count) VALUES (?, ?, ?)", [word, *newrow])
con.commit()
