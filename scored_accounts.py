import tweepy
import time
import operator
from collections import Counter
import concurrent.futures
import os

TWITTER_BEARER_TOKEN = os.environ["BEARER_TOKEN"]
Client = tweepy.Client(TWITTER_BEARER_TOKEN)


def screen_name_to_id(screen_name):
    user = Client.get_user(username=screen_name)
    user_id = user.data.id
    return user_id


def id_to_screen_name(accounts):
    screen_names = []
    for account_id, count in accounts:
        try:
            user = Client.get_user(id=f"{account_id}")
            screen_name = user.data.username
            screen_names.append((screen_name, count))
        except AttributeError:
            continue
    return screen_names


def most_liked_accounts(searched_user_id):
    """
    Returns 15 most liked tweets' authors usernames, sorted by frequency
    """
    paginator = tweepy.Paginator(
        Client.get_liked_tweets,
        id=f"{searched_user_id}",
        user_fields=["id"],
        expansions=["author_id"],
    )
    author_id = [
        tweet.author_id
        for tweet in paginator.flatten(limit=100)  # change to 1000
        if tweet.author_id != searched_user_id
    ]  # actual working limit = 2000
    return id_to_screen_name(Counter(author_id).most_common(15))


def most_retweeted_accounts(searched_user_id):
    paginator = tweepy.Paginator(
        Client.get_users_tweets,
        f"{searched_user_id}",
        max_results=100,
        expansions=["referenced_tweets.id.author_id"],
        exclude=["replies"],
    )
    retweeted_accounts = [
        tweet.text.split(" ")[1][1:-1]
        for tweet in paginator.flatten(limit=100)  # change to 1000
        if tweet["text"].startswith("RT ")
        # if tweet.text.split(" ")[1][1:-1] != USERS_SCREEN_NAME_INPUT
    ]  # user's account is still present
    return Counter(retweeted_accounts).most_common(15)


def most_replied_to_accounts(searched_user_id):
    paginator = tweepy.Paginator(
        Client.get_users_tweets,
        f"{searched_user_id}",
        max_results=100,
        expansions=[
            "referenced_tweets.id",
            "referenced_tweets.id.author_id",
            "in_reply_to_user_id",
        ],
    )
    replied_to_accounts = [
        tweet.in_reply_to_user_id
        for tweet in paginator.flatten(limit=100) # change to 1000
        if tweet.in_reply_to_user_id is not None
        # if tweet.in_reply_to_user_id != SEARCHED_USER_ID # SOLVE
    ]
    return id_to_screen_name(Counter(replied_to_accounts).most_common(15))


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
    php_urls_small = [x.profile_image_url for x in phps.data]
    php_urls_big = [url.replace("_normal.jpg", ".jpg").replace("_normal.png", ".png") for url in php_urls_small]
    return dict(zip(searched_usernames, php_urls_big))


def main(searched_user_id):
    """
    Function takes results of user activities in form of ("user, interacted with", number of interactions)
    and sums this interactions up and returns a dictionary in descending order by score(interactions).

    Retweeted accounts get x2 coefficient compared to liked tweets, as it supposed to have greater importance.
    Replied_to accounts get x1,25 coefficient compared to liked tweets, as it supposed to have greater importance.
    """
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            t1 = executor.submit(most_liked_accounts, searched_user_id)
            t2 = executor.submit(most_retweeted_accounts, searched_user_id)
            t3 = executor.submit(most_replied_to_accounts, searched_user_id)
            most_liked_accs = dict(t1.result(timeout=60))
            most_retweeted_accs = dict(t2.result(timeout=60))
            most_replied_to_accs = dict(t3.result(timeout=60))
    except ConnectionError:
        print("Oops! It seems we lost connection")
    except TimeoutError:
        print("Oops! For some reason response took to long:(")

    scored_accs = {
        key: most_liked_accs.get(key, 0)
        + most_retweeted_accs.get(key, 0) * 2
        + most_replied_to_accs.get(key, 0) * 1.25
        for key in set(most_liked_accs)
        | set(most_retweeted_accs)
        | set(most_replied_to_accs)
    }
    return dict(sorted(scored_accs.items(), key=operator.itemgetter(1), reverse=True))


if __name__ == "__main__":
    start = time.time()
    USERS_SCREEN_NAME_INPUT = "bo_bilan"  # put twitter handle to analyse
    SEARCHED_USER_ID = screen_name_to_id(USERS_SCREEN_NAME_INPUT)

    print(get_php_url(main(SEARCHED_USER_ID), 11))

    end = time.time()
    run_time = start - end
    print(f"Program ran:{run_time} sec")


# TODO: id_to_screen_name - change get_userS
# TODO: ' symbol infront tweepy.errors.BadRequest: 400 Bad Request The `username` query parameter value ['SkiddilyNFT] does not match ^[A-Za-z0-9_]{1,15}$
# TODO:  Connection error    raise ConnectionError(e, request=request) multithreading
# TODO:  Time ran out multithreading
# TODO: 'Error! Failed to get request token.
