import os
import time
import json
from slackclient import SlackClient
import pycurl
from io import BytesIO

# curlybot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

HOST = 'https://api.github.com' 
PATH = '/'

#'users/digitalWestie/repos'

def index_cmd(resource):
  result = make_request(resource)
  if (result == None):
    return "Sorry! Couldn't return a list of " + resource + "."
  else:
    return "Here's a list of "+resource+" you wanted: \n```\n"+result+"\n```"


def api_info_cmd():
  return "Here's some details:\nENDPOINT: "+HOST+PATH


FULLCOMMANDS = {
  "tell me about the API you're using": api_info_cmd,
  "what API?": api_info_cmd,
  "config info?": api_info_cmd,
  "that'll do pig": exit,
  "disconnect": exit,
  "exit": exit
}

PARAMCOMMANDS = {
  "list all the ": index_cmd, 
  "give me all the ": index_cmd,
  "give me a list of the ": index_cmd
}

#IDEA: split at the first 'the' to find the object

def make_request(resource):
  url = HOST+PATH+resource
  print 'Making a request to ' + url
  data = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, url)
  c.setopt(c.WRITEFUNCTION, data.write)
  c.perform()
  c.close()
  r = data.getvalue()
  data.close()
  try:
    jsondata = json.loads(r)
    return json.dumps(jsondata,  sort_keys=True, indent=2, separators=(',', ': '))
  except: 
    print "couldn't parse json from request to " + url


def handle_command(command, channel):
  """
    Receives commands directed at the bot and determines if they
    are valid commands. If so, then acts on the commands. If not,
    returns back what it needs for clarification.
  """
  #command = command.lower()
  command = command.encode('utf-8')
  response = "Not sure what you mean. Use the *list all the " + \
         "* command with a resource, delimited by spaces."

  for cmd in PARAMCOMMANDS.keys():
    if command.startswith(cmd.lower()):
      split = command.split(cmd)
      response = PARAMCOMMANDS[cmd](split[1])

  for cmd in FULLCOMMANDS.keys():
    if command == cmd.lower():
      response = FULLCOMMANDS[cmd]()

  slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
  """
    The Slack Real Time Messaging API is an events firehose.
    this parsing function returns None unless a message is
    directed at the Bot, based on its ID.
  """
  output_list = slack_rtm_output
  if output_list and len(output_list) > 0:
    for output in output_list:
      if output and 'text' in output and AT_BOT in output['text']:
        # return text after the @ mention, whitespace removed
        return output['text'].split(AT_BOT)[1].strip().lower(), \
             output['channel']
  return None, None


if __name__ == "__main__":
  READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
  if slack_client.rtm_connect():
    print("CurlyBot connected and running!")
    while True:
      command, channel = parse_slack_output(slack_client.rtm_read())
      if command and channel:
        handle_command(command, channel)
      time.sleep(READ_WEBSOCKET_DELAY)
  else:
    print("Connection failed. Invalid Slack token or bot ID?")
