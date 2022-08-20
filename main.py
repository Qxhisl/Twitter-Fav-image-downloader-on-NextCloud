from requests_oauthlib import OAuth1Session
import os
import requests
import json
import datetime
import schedule
import time

twitter = OAuth1Session(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'], os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])

twitter_params =  {"screen_name": os.environ['TWITTER_USER_ID'], # 自身のTwitterID
                   "count": int(os.environ['TWITTER_API_COUNT']) # 取得するツイート数(最大200)
                   }

fav_tweet_data = [] # TwitterAPIからJSON形式で返ってくるツイートデータ
urls = [] 

def main():
  log = open('log.txt', 'a')
  log.write(str(datetime.datetime.now()) + "\n")
  log.close()

  get_fav_tweet_data()

  latest_fav_tweet_check()

  if fav_tweet_data:
    f = open('latest_fav_tweet_id.txt', 'w')
    f.write(str(fav_tweet_data[0]["id"]))
    f.close()
    extract_url()
    save_image()

  else:
      log = open('log.txt', 'a')
      log.write('今日新しくいいねしたツイートはありません\n')
      log.write('-'*10 + '\n')
      log.close()

def get_fav_tweet_data():
  global fav_tweet_data
  req = twitter.get("https://api.twitter.com/1.1/favorites/list.json", params = twitter_params)
  fav_tweet_data = json.loads(req.text)

def latest_fav_tweet_check():
  global fav_tweet_data

  f = open('latest_fav_tweet_id.txt', 'r')
  latest_fav_tweet_id = int(f.read())
  f.close()
  
  # 画像の重複保存を防ぐため、取得したfav_tweet_dataの中に以前の実行で取得したツイートが含まれている場合は切り落とす
  for i in range(len(fav_tweet_data)):
    if fav_tweet_data[i]["id"] <= latest_fav_tweet_id:
      del fav_tweet_data[i:]
      break

def extract_url():
    # 新しくいいねをしたツイートのデータ(latest_fav_tweet_check()実行後の変数fav_tweet_data)から画像のURLを抽出して配列urlsに入れる
  for i in range(len(fav_tweet_data)):
    try:
      fav_tweet_data[i]["extended_entities"]["media"]
    except KeyError: # 取得したツイートに画像がない場合のエラー処理
      pass
    else:
      # gifや動画のツイートからサムネイル画像を取得してしまうのを防ぐための処理
      if fav_tweet_data[i]["extended_entities"]["media"][0]["type"] != "photo":
        continue
      image_num = len(fav_tweet_data[i]["extended_entities"]["media"])
      for j in range(image_num):
        urls.append(fav_tweet_data[i]["extended_entities"]["media"][j]["media_url"])

def save_image():
  global urls
  
  for url in urls:
    res = requests.get(url+":orig").content # 抽出したURLから原寸画像をダウンロード

    requests.put('http://'+ os.environ['SERVER_IP_ADDRESS']+ '/remote.php/dav/files/' + os.environ['NEXTCLOUD_USERNAME'] + '/'+ os.environ['DIRNAME']+'/'+ url[27:],data=res, auth=(os.environ['NEXTCLOUD_USERNAME'], os.environ['NEXTCLOUD_PW']))

    log = open('log.txt', 'a')
    log.write(f'Downloaded: {url}\n')
    log.close()

  log = open('log.txt', 'a')
  log.write('-'*10 + '\n')
  log.close()

  urls.clear() # 次回のために配列のデータを削除

schedule.every().day.at(os.environ['EXECUTION_TIME']).do(main)

while True:
  schedule.run_pending()
  time.sleep(1)