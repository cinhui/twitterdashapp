import settings
import credentials
import tweepy
import dataset
from textblob import TextBlob
from sqlalchemy.exc import ProgrammingError
import json
import os
import psycopg2
import mysql.connector


class StreamListener(tweepy.StreamListener):

    def on_status(self, status):
        if status.retweeted:
            return
   
        created_at = status.created_at
        id_str = status.id_str
        text = status.text
        
        in_reply_to = status.in_reply_to_screen_name

        user_name = status.user.screen_name
        user_location = status.user.location
        user_description = status.user.description
        user_created_at = status.user.created_at
        followers_count = status.user.followers_count
        friends_count = status.user.friends_count
        
        coords = None
        geo = None
        
        retweet_count = status.retweet_count
        favorites_count = status.favorite_count

        blob = TextBlob(text)
        sent = blob.sentiment
        polarity=sent.polarity
        subjectivity=sent.subjectivity
#         longitude = None
#         latitude = None
#         if status.coordinates:
#             longitude = status.coordinates['coordinates'][0]
#             latitude = status.coordinates['coordinates'][1]

        if status.geo:
            geo = json.dumps(geo)

        if status.coordinates:
            coords = json.dumps(coords)

        was_retweet_id = None
        was_retweet_user = None
        if hasattr(status,'retweeted_status'):
            was_retweet_id = status.retweeted_status.id_str
            was_retweet_user = status.retweeted_status.user.screen_name

        # if conn.is_connected():
        curr = conn.cursor()
        
        sql = "INSERT INTO {} (created_at, id_str, text, in_reply_to, \
                was_retweet_id, was_retweet_user, \
                user_name, user_location , user_description, user_created , \
                geo, coordinates, \
                user_followers_count, user_friends_count, \
                retweet_count, favorites_count, polarity, subjectivity) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)".format(TABLE_NAME)
        val = (created_at, id_str, text, in_reply_to, \
            was_retweet_id, was_retweet_user, \
            user_name, user_location , user_description, user_created_at , \
            geo, coords, \
            followers_count, friends_count, \
            retweet_count, favorites_count, polarity, subjectivity)
        
        curr.execute(sql, val)
        conn.commit()
        curr.close()
        # table = db[TABLE_NAME]
        # try:
            # table.insert(dict(            
            #     created_at=created_at,
            #     id_str=id_str,
            #     text=text,
            #     in_reply_to = in_reply_to,  
            #     user_name=user_name,
            #     user_location=user_location,
            #     user_description=user_description,
            #     user_created=user_created_at,
            #     geo=geo,
            #     coordinates=coords,
            #     was_retweet_id = was_retweet_id,
            #     was_retweet_user = was_retweet_user,
            #     user_followers_count=followers_count,
            #     user_friends_count=friends_count,
            #     retweet_count=retweet_count,
            #     favorites_count=favorites_count,
            #     polarity=sent.polarity,
            #     subjectivity=sent.subjectivity,
            # ))
        # except ProgrammingError as err:
        #     print(err)

    def on_error(self, status_code):
        if status_code == 420:
            #returning False in on_data disconnects the stream
            return False

#Strip all non-ASCII characters
def clean_ascii(text): 
    if text:
        return text.encode('ascii', 'ignore').decode('ascii')
    else:
        return None

TABLE_ATTRIBUTES = "created_at TIMESTAMP, id_str VARCHAR(255), text VARCHAR(255), in_reply_to VARCHAR(255), \
            was_retweet_id VARCHAR(255), was_retweet_user VARCHAR(255), \
            user_name VARCHAR(255), user_location VARCHAR(255), user_description VARCHAR(255), user_created VARCHAR(255), \
            geo VARCHAR(255), coordinates VARCHAR(255), \
            user_followers_count INT, user_friends_count INT, \
            retweet_count INT, favorites_count INT, polarity DOUBLE PRECISION, subjectivity DOUBLE PRECISION"

TRACK_TERMS = ['#AEW', '#AllELiteWrestling', '#AEWDark', '#AEWDynamite', '#AEWonTNT', '#WWE', '#NXT']
TABLE_NAME = "dynamite"

# CONNECTION_STRING = "sqlite:///elite.db"
# DATABASE_URL = CONNECTION_STRING
# DATABASE_URL = os.environ['DATABASE_URL']
# conn = connect(DATABASE_URL)
# db = dataset.connect(DATABASE_URL)

conn = psycopg2.connect(user = "root",
                        password = "",
                        host = "localhost",
                        port = "5432",
                        database = "dbtwitter")
# conn = psycopg2.connect(DATABASE_URL, sslmode='require')
curr = conn.cursor()
# Check if this table exits. If not, then create a new one.
curr.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(TABLE_NAME))
if curr.fetchone()[0] == 0:
    curr.execute("CREATE TABLE {} ({});".format(TABLE_NAME, TABLE_ATTRIBUTES))
    conn.commit()
curr.close()

# conn = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     passwd="password",
#     database="TwitterDB",
#     charset = 'utf8'
# )
# Check if this table exits. If not, then create a new one.
# if conn.is_connected():
#     curr = conn.cursor()
#     curr.execute("""
#         SELECT COUNT(*)
#         FROM information_schema.tables
#         WHERE table_name = '{0}'
#         """.format(TABLE_NAME))
#     if curr.fetchone()[0] != 1:
#         curr.execute("CREATE TABLE {} ({})".format(TABLE_NAME, TABLE_ATTRIBUTES))
#         conn.commit()
#     curr.close()

auth = tweepy.OAuthHandler(credentials.TWITTER_APP_KEY, credentials.TWITTER_APP_SECRET)
auth.set_access_token(credentials.TWITTER_KEY, credentials.TWITTER_SECRET)
api = tweepy.API(auth)

stream_listener = StreamListener()
stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
stream.filter(track=TRACK_TERMS)