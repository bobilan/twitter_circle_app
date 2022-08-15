import tweepy
import time
import operator
from collections import Counter
import concurrent.futures
import os
from app import screen_name_input

TWITTER_BEARER_TOKEN = os.environ["BEARER_TOKEN"]
Client = tweepy.Client(TWITTER_BEARER_TOKEN)


def get_php_url(searched_usernames, count):
    """
    Returns profile pictures(php) url of Twitter users.

    :param searched_usernames: a dict of scored account, which is being converted to list of usernames
    :param count: number of element of the converted list
    :return: list of urls
    """
    searched_usernames = list(searched_usernames.keys())[:count]
    phps = Client.get_users(
        usernames=searched_usernames,
        user_fields=["profile_image_url", "id"])
    return print([x.profile_image_url for x in phps.data])


if __name__ == "__main__":
    start = time.time()
    USERS_SCREEN_NAME_INPUT = "bo_bilan"  # put twitter handle to analyse
    # SEARCHED_USER_ID = screen_name_to_id(USERS_SCREEN_NAME_INPUT)

    searched_ids = {'aerostar_pilot': 16.25, 'Alpha_Kamp': 12.0, 'InvsbleFriends': 8.75, 'wulfznft': 8.0, 'ChimpsNFT': 7.75, 'alina_the_bi': 6.25, 'BossBullsClub': 6.0, 'TrippinApeNFT': 6.0, 'operationSIN': 4.0, 'asian_mint': 4.0, 'WGMInterfaces': 3.0, 'GameFi_Official': 3.0, 'feyi_x': 3.0, 'TrustPad': 3.0, 'troll_town_wtf': 3.0, 'PolkaFoundry': 3.0, 'GrowGroupHQ': 2.5, 'AkuDreams': 2.5, 'OakParadiseNFT': 2.5, 'berg_sis': 2.5, 'a_skroznikov': 2.5, 'SixthReseau': 2.5, 'BAYCPrince': 2.5, 'paid_network': 2.5, 'dapenft': 2.5, 'ThePossessedNFT': 2.0, 'DocumentingBTC': 2.0, 'opensea': 2.0, '0xfoobar': 2.0, 'SilkNFT': 2.0, 'mythG_': 2.0, 'ThePilgrimsNFT': 2.0, 'eskyy': 2.0, 'wagmiarmynft': 2.0, 'thedefiedge': 2.0, 'ZssBecker': 2.0, 'NFTYKEYS': 2.0}

    # get_php_url(searched_ids, 10)
    # most_retweeted_accounts(477122869 )
    print(screen_name_input)

    end = time.time()
    run_time = start - end
    print(f"Program ran:{run_time} sec")


# TODO: ' symbol infront tweepy.errors.BadRequest: 400 Bad Request The `username` query parameter value ['SkiddilyNFT] does not match ^[A-Za-z0-9_]{1,15}$
# TODO:  Connection error    raise ConnectionError(e, request=request) multithreading
# TODO:  Time ran out multithreading
# TODO: 'Error! Failed to get request token.
