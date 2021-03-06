#As of 09-14-2016, twitch API now requires Client-ID with all requests.  You will need to create one from here: 
# https://www.twitch.tv/settings/connections
# complete twitch.py rewrite coming soon™
import requests
import sopel
import re
from sopel.tools import SopelMemory
import datetime

# TODO: Make these config options c:
twitchclientid = "clientIDgoeshere" 
announce_chan = "#pancakes"
logchannel = "#whateverchannelyouwant" #used for live logging certain issues that plague this module
streamers = [
"coalll",
"chouxe",
"kwlpp",
"dasusp",
"esicra",
"agriks",
"repppie",
"squidgay",
"supersocks",
"sc00ty",
"kaask",
"mole_star",
"twoiis",
"sasserr",
"mogra" #untz untz
]

hstreamers = [
'kwlpp',
'agriks',
'coal',
'chouxe',
'socks',
'dasusp',
'agriks'
]
#end config

twitchregex = re.compile('(?!.*\/v\/).*https?:\/\/(?:www\.)?twitch.tv\/(.*?)\/?(?:(?=[\s])|$)')
mixerregex = re.compile('(?!.*\/v\/).*https?:\/\/(?:www\.)?mixer.com\/(.*?)\/?(?:(?=[\s])|$)')

def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = SopelMemory()
    bot.memory['url_callbacks'][twitchregex] = twitchirc
    bot.memory['url_callbacks'][mixerregex] = mixerirc

def shutdown(bot):
    del bot.memory['url_callbacks'][twitchregex]
    del bot.memory['url_callbacks'][mixerregex]

currently_streaming = {}
currently_hstreaming = {}
currently_ystreaming = {}

def twitch_api(stream_list):
  """ Returns the result of the http request from Twitch's api """
  return requests.get('https://api.twitch.tv/kraken/streams', params={"channel": ",".join(stream_list)}, headers={"Client-ID": twitchclientid}).json()


def twitch_generator(streaming):
  for streamer in streaming["streams"]:
    streamer_dict = {}
    streamer_dict["name"] = streamer["channel"]["name"]
    streamer_dict["game"] = streamer["channel"]["game"]
    streamer_dict["status"] = streamer["channel"]["status"]
    streamer_dict["url"] = streamer["channel"]["url"]
    streamer_dict["starttime"] = datetime.datetime.strptime(streamer['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    streamer_dict["viewers"] = streamer["viewers"]
    yield streamer_dict

def smash_generator(hstreaming):
  for streamer in hstreaming["livestream"]:
    if streamer["media_is_live"] is "1":
      streamer_dict = {}
      streamer_dict["name"] = streamer["media_user_name"]
      streamer_dict["game"] = streamer["category_name"]
      streamer_dict["url"] = streamer["channel"]["channel_link"]
      streamer_dict["viewers"] = streamer["media_views"]
      yield streamer_dict

@sopel.module.interval(20)
def monitor_streamers(bot):
  streaming_names = []
  try:
    streaming = twitch_api(streamers)
    # streaming = requests.get('https://api.twitch.tv/kraken/streams', params={"channel": ",".join(streamers)}, headers={"Client-ID":twitchclientid}).json()
  except Exception as  e:
    return print("There was an error reading twitch API  {0}".format(e))
  results = []
  if streaming.get("streams"):
    twitch_gen = twitch_generator(streaming)
    for streamer in twitch_gen:
      if streamer["name"] not in currently_streaming:
        currently_streaming[streamer["name"]] = streamer["game"], {'cooldown': 0, 'starttime': streamer["starttime"]}
        results.append("%s just went live playing %s! [%s] (%s - %s viewer%s)" % (streamer["name"],
                                                                                  streamer["game"],
                                                                                  streamer["status"],
                                                                                  streamer["url"],
                                                                                  streamer["viewers"],
                                                                                  "s" if streamer["viewers"] != 1 else ""))
      streaming_names.append(streamer["name"])

  if results:
    bot.msg(announce_chan, ", ".join(results))  

  # Remove people who stopped streaming
  for streamer in list(currently_streaming):
    if streamer not in streaming_names:
      currently_streaming[streamer][1]['cooldown'] += 10
    if currently_streaming[streamer][1]['cooldown'] > 130:
      #bot.msg(logchannel,'{0} was removed from currently_streaming for reaching a cooldown of {1}'.format(streamer,currently_streaming[streamer][1]['cooldown']))
      del currently_streaming[streamer]

  hstreaming_names = []
  hs = ",".join(hstreamers)
  try:
    testingtimeout = datetime.datetime.now()
    hstreaming = requests.get('http://api.smashcast.tv/media/live/{0}'.format(hs),timeout=(1.5,1.5)).json()
  except requests.exceptions.ConnectionError:
    return bot.msg(logchannel,"timeout time: {}".format((datetime.datetime.now() - testingtimeout).total_seconds()))
  except:
    return bot.msg(logchannel,"error with smashcast api")
  hresults = []
  if hstreaming.get("livestream"):
    smash_gen = smash_generator(hstreaming)
    for hstreamer in smash_gen:     
      if hstreamer["name"] not in currently_hstreaming:
        currently_hstreaming[hstreamer["name"]] = hstreamer["game"], {'cooldown': 0}
        hresults.append("%s just went live playing %s! (%s - %s viewer%s)" % (hstreamer["name"],hstreamer["game"],hstreamer["url"],hstreamer["viewers"],"s" if hstreamer["viewers"] != 1 else ""))

        hstreaming_names.append(hstreamer["name"])

  if hresults:
    bot.msg(announce_chan, ", ".join(hresults))
  
  for hstreamer in list(currently_hstreaming):
    if hstreamer not in hstreaming_names:
      currently_hstreaming[hstreamer][1]['cooldown'] += 10
    if currently_hstreaming[hstreamer][1]['cooldown'] > 130:
      del currently_hstreaming[hstreamer]

@sopel.module.commands('twitchtv','twitch')
@sopel.module.example('.twitch  or .twitch twitchusername')
def streamer_status(bot, trigger):
  streamer_name = trigger.group(2)
  query = streamers if streamer_name is None else streamer_name.split(" ")
  try:
    streaming = twitch_api(query)
    # streaming = requests.get('https://api.twitch.tv/kraken/streams', params={"channel": ",".join(query)}, headers={"Client-ID":twitchclientid}).json()
  except Exception as  e:
    return print("There was an error reading twitch API  {0}".format(e))
  results = []
  if streaming.get("streams"):
    twitch_gen = twitch_generator(streaming)
    for streamer in twitch_gen:
      results.append("%s is playing %s [%s] (%s - %s viewer%s)" % (streamer["name"],
                                                                   streamer["game"],
                                                                   streamer["status"],
                                                                   streamer["url"],
                                                                   streamer["viewers"],
                                                                   "s" if streamer["viewers"] != 1 else ""))
  if results:
    bot.say(", ".join(results))
  else:
    bot.say("Nobody is currently streaming.")


@sopel.module.commands('sc','smashcast')
@sopel.module.example('.sc  or .sc twitchusername')
def hstreamer_status(bot, trigger):
  hstreamer_name = trigger.group(2)
  query = ",".join(hstreamers) if hstreamer_name is None else hstreamer_name
  hstreaming = requests.get('http://api.smashcast.tv/media/live/{0}'.format(query)).json()
  hresults = []
  if hstreaming.get("livestream"):
    smash_gen = smash_generator(hstreaming)
    for hstreamer in smash_gen:  
      hresults.append("%s is playing %s (%s - %s viewer%s)" % (hstreamer["name"],
                                                           hstreamer["game"],
                                                           hstreamer["url"],
                                                           hstreamer["viewers"],
                                                           "s" if hstreamer["viewers"] != 1 else "" ))
  if hresults:
    bot.say(", ".join(hresults))
  else:
    bot.say("Nobody is currently streaming.")

@sopel.module.commands('tv')
@sopel.module.example('.tv')
def allstreamer_status(bot, trigger):
  streamer_name = trigger.group(2)
  query = streamers if streamer_name is None else streamer_name.split(" ")
  try:
    streaming = twitch_api(query)
    # streaming = requests.get('https://api.twitch.tv/kraken/streams', params={"channel": ",".join(query)}, headers={"Client-ID":twitchclientid}).json()
  except Exception as  e:
    return print("There was an error reading twitch API  {0}".format(e))
  results = []
  if streaming.get("streams"):
    twitch_gen = twitch_generator(streaming)
    for streamer in twitch_gen:
      results.append("%s is playing %s [%s] (%s - %s viewer%s)" % (streamer["name"],
                                                                   streamer["game"],
                                                                   streamer["status"],
                                                                   streamer["url"],
                                                                   streamer["viewers"],
                                                                   "s" if streamer["viewers"] != 1 else ""))
  query = ",".join(hstreamers)
  hstreaming = requests.get('http://api.smashcast.tv/media/live/{0}'.format(query)).json()
  hresults = []
  if hstreaming.get("livestream"):
    smash_gen = smash_generator(hstreaming)
    for hstreamer in smash_gen:  
      hresults.append("%s is playing %s (%s - %s viewer%s)" % (hstreamer["name"],
                                                           hstreamer["game"],
                                                           hstreamer["url"],
                                                           hstreamer["viewers"],
                                                           "s" if hstreamer["viewers"] != 1 else "" ))

  if results:
    bot.say(", ".join(results))
  else:
    bot.say("Nobody is currently streaming.")

@sopel.module.rule('(?!.*\/v\/).*https?:\/\/(?:www\.)?twitch.tv\/(.*?)\/?(?:(?=[\s])|$)')
def twitchirc(bot, trigger, match = None):
  match = match or trigger
  streamer_name = match.group(1)
  query = streamers if streamer_name is None else streamer_name.split(" ")
  try:
    streaming = twitch_api(query)
    # streaming = requests.get('https://api.twitch.tv/kraken/streams', params={"channel": ",".join(query)}, headers={"Client-ID":twitchclientid}).json()
  except Exception as  e:
    return print("There was an error reading twitch API  {0}".format(e))
  results = []
  if streaming.get("streams"):
    twitch_gen = twitch_generator(streaming)
    for streamer in twitch_gen:
      results.append("%s is playing %s [%s] (%s - %s viewer%s)" % (streamer["name"],
                                                                   streamer["game"],
                                                                   streamer["status"],
                                                                   streamer["url"],
                                                                   streamer["viewers"],
                                                                   "s" if streamer["viewers"] != 1 else ""))
  if results:
    bot.say(", ".join(results))
  else:
    pass
    #bot.say("Nobody is currently streaming.")

@sopel.module.rule('(?!.*\/v\/).*https?:\/\/(?:www\.)?mixer.com\/(.*?)\/?(?:(?=[\s])|$)')
def mixerirc(bot, trigger, match = None):
  match = match or trigger
  streamer_name = match.group(1)
  streaming = requests.get('https://mixer.com/api/v1/channels/{}'.format(streamer_name)).json()
  results = []
  if streaming:
    streamer_name = streaming["token"]
    if streaming.get("type"):
      streamer_game = streaming["type"]["name"]
    else:
      streamer_game = "a game"
    streamer_status = streaming["name"]
    streamer_viewers = streaming["viewersCurrent"]

  results.append("%s is playing %s [%s] - %s viewer%s" % (streamer_name,
                                                         streamer_game,
                                                         streamer_status,
                                                         streamer_viewers,
                                                         "s" if streamer_viewers != 1 else "" ))
  if results:
    bot.say(", ".join(results))
  else:
    pass

@sopel.module.commands('debugtv')
def debug(bot, trigger):
    bot.msg(logchannel,"currently_streaming: {}".format(", ".join(currently_streaming)))
    bot.msg(logchannel,"currently_hstreaming: {}".format(", ".join(currently_hstreaming)))