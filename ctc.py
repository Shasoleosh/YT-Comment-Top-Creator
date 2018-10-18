#!/usr/bin/python
# -*- encoding: utf-8 -*-

"""
#**********************************************************************;
# Project           : Collect comments, sort, write to file.
#
# Program name      : Comment Top Creator (CTC)
#
# Author            : Shasoleosh Boshasart
#
# Date created      : 20181017
#
|**********************************************************************;

How to use:
0) configurate 'client_secret.json'
    (See the comment on line 51)
1) Run start.bat or in cmd 'python ctc.py'
2) Enter YouTube link
3) Enter top comment count
4) When you first start asking for a login to google account
5) Wait for the completion message...
6) The result can be found in the folder '/results'
    (Example file name: 3arjZJlAU5A_top10_comments.csv)

Result format: Like; Name; Comment;
    (All string type)

"""

import httplib2
import os
import sys
import time, math, csv, re

from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


videoid = input("Enter the link to the video: ").split('?v=')[1]
commentCount = int(input("Enter the number of comments you want to receive: "))

best_comments = []
nextToken = ""
page = 0
startTime = time.time()

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains

# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SSL_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  # Trusted testers can download this discovery document from the developers page
  # and it should be in the same directory with the code.
  with open("youtube-v3-discoverydocument.json", "r", encoding='utf-8') as f:
    doc = f.read()
    return build_from_document(doc, http=credentials.authorize(httplib2.Http()))

#The function to record the result in a csv file
def csv_writer(data, path):
    with open(path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=';')
        for line in data:
            writer.writerow(line)

# Call the API's commentThreads.list method to list the esxisting comments.
def get_comments(youtube, video_id, channel_id):
    global nextToken
    global page
    global best_comments

    while(True):
        #We count pages
        page += 1
        print(page)

        #We collect request
        results = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        channelId=channel_id,
        textFormat="plainText",
        pageToken=nextToken
        ).execute()

        #We collect data from the request
        for item in results["items"]:
            comment = item["snippet"]["topLevelComment"]

            author = comment["snippet"]["authorDisplayName"]
            text = comment["snippet"]["textDisplay"]
            like = comment["snippet"]["likeCount"]

            #We remove the excess from the string
            reg = re.compile('[^a-zA-Z ^а-яА-Я ^0-9 ^(/!&.,@#=?\"\':$&)]')
            text = reg.sub('', text)

            #Putting it all in the final sheet
            best_comments.append([like, author, text])

        #Sort and remove too much
        if commentCount < len(best_comments):
            best_comments.sort()
            best_comments.reverse()
            best_comments = best_comments[0:commentCount]

        #Here, when we exit the cycle   while(True)  line 96:
        try:
            nextToken = results['nextPageToken']
        except KeyError:
            break

    return results["items"]


if __name__ == "__main__":

    args = argparser.parse_args()
    youtube = get_authenticated_service(args)

    #Check if everything is good
    try:
        video_comments = get_comments(youtube, videoid, None)
    except HttpError:
        print ("Ohh... it's Http Error!")
    else:
        #Sort and remove too much again
        if commentCount < len(best_comments):
            best_comments.sort()
            best_comments.reverse()
            best_comments = best_comments[0:commentCount]

    #Print everything to console
    d = time.time() - startTime
    print('Done! The result is recorded in the folder \"/results\"')
    print(videoid,'\nTime spent: \nseconds: %s\n' %  (d))
    for l in best_comments:
        print(l)
    best_comments.append(['','Time spent:'+str(d)+'seconds',' Total pages:'+str(page)])
    print('Done! The result is recorded in the folder \"/results\"')
    #Save result to csv file
    csv_writer(best_comments, 'results/'+videoid+'_top'+str(commentCount)+'_comments.csv')
