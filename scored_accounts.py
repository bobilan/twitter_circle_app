import itertools
import tweepy
import time
import operator
from collections import Counter
import concurrent.futures
import os
from suspisious_mentions import SUSPICIOUS_MENTIONS_LIST
import newrelic.agent

TWITTER_BEARER_TOKEN = os.environ["BEARER_TOKEN"]
Client = tweepy.Client(TWITTER_BEARER_TOKEN)


class Scored:
    @newrelic.agent.function_trace()
    def __init__(self, screen_name):
        self.screen_name = screen_name.replace("@", "").replace(" ", "")
        self.searched_user_id = self.screen_name_to_id()
        self.searched_user_data = {}
        self.searched_user_suspicious_mentions = {}
        self.scored_sorted_users = {}
        self.scored_users_data = []
        self.times_connected_user_liked = {}
        self.times_connected_user_replied = {}
        self.times_connected_user_retweeted = {}

    @newrelic.agent.function_trace()
    def screen_name_to_id(self):
        user = Client.get_user(
            username=self.screen_name,
            user_fields=[
                "profile_image_url",
                "id",
                "public_metrics",
                "created_at",
                "location",
                "description",
            ],
        )
        self.searched_user_id = user.data.id
        self.searched_user_data = {
            "username": user.data.username,
            "name": user.data.name,
            "profile_image_url": user.data.profile_image_url.replace(
                "_normal.jpg", ".jpg"
            ).replace("_normal.png", ".png"),
            "bio": user.data.description,
            "created_at": user.data.created_at.strftime("%d.%m.%Y"),
            "location": user.data.location,
            "followers_count": user.data.public_metrics["followers_count"],
            "following_count": user.data.public_metrics["following_count"],
            "tweet_count": user.data.public_metrics["tweet_count"],
        }

        return self.searched_user_id

    @newrelic.agent.function_trace()
    def get_suspicious_mentions(self) -> dict:
        suspicious_mentions = {}
        paginator = tweepy.Paginator(
            Client.get_users_mentions,
            id=self.searched_user_id,
            user_fields=["id"],
            max_results=100,
            expansions=["author_id", "entities.mentions.username"],
        )
        for mention in paginator.flatten(limit=500):
            if any(x in mention.text for x in SUSPICIOUS_MENTIONS_LIST):
                suspicious_mentions.update({mention.text: mention.id})
        self.searched_user_suspicious_mentions = suspicious_mentions
        return self.searched_user_suspicious_mentions

    @staticmethod
    @newrelic.agent.function_trace()
    def id_to_screen_name(accounts) -> list[tuple[str, int]]:
        accounts_map = {k: v for k, v in accounts}
        users = Client.get_users(ids=list(accounts_map.keys()))
        return [(u.username, accounts_map[u.id]) for u in users.data]

    @newrelic.agent.function_trace()
    def most_liked_accounts(self):
        """
        Returns 10 most liked tweets' authors usernames, sorted by frequency
        """
        paginator = tweepy.Paginator(
            Client.get_liked_tweets,
            id=f"{self.searched_user_id}",
            user_fields=["id"],
            expansions=["author_id"],
        )
        author_id = [
            tweet.author_id
            for tweet in paginator.flatten(limit=500)  # change to 1000
            if tweet.author_id != self.searched_user_id
        ]  # actual working limit = 1000
        result = self.id_to_screen_name(Counter(author_id).most_common(10))

        return result

    @newrelic.agent.function_trace()
    def most_retweeted_accounts(self):
        paginator = tweepy.Paginator(
            Client.get_users_tweets,
            f"{self.searched_user_id}",
            max_results=100,
            expansions=["referenced_tweets.id.author_id"],
            exclude=["replies"],
        )
        retweeted_accounts = [
            tweet.text.split(" ")[1][1:-1]
            for tweet in paginator.flatten(limit=500)  # change to 1000
            if tweet["text"].startswith("RT ")
            if tweet.text.split(" ")[1][1:-1] != self.screen_name
        ]  # user's account is still present
        return Counter(retweeted_accounts).most_common(15)

    @newrelic.agent.function_trace()
    def most_replied_to_accounts(self):
        paginator = tweepy.Paginator(
            Client.get_users_tweets,
            f"{self.searched_user_id}",
            max_results=100,
            expansions=[
                "referenced_tweets.id",
                "referenced_tweets.id.author_id",
                "in_reply_to_user_id",
            ],
        )
        replied_to_accounts = [
            tweet.in_reply_to_user_id
            for tweet in paginator.flatten(limit=500)  # change to 1000
            if tweet.in_reply_to_user_id is not None
            if tweet.in_reply_to_user_id != self.searched_user_id
        ]
        return self.id_to_screen_name(Counter(replied_to_accounts).most_common(10))

    @newrelic.agent.function_trace()
    def compose_scored_account(self):
        """
        Function takes results of user activities in form of ("user, interacted with", number of interactions)
        and sums this interactions up and returns a dictionary in descending order by score(interactions).

        Retweeted accounts get x2 coefficient compared to liked tweets, as it supposed to have greater importance.
        Replied_to accounts get x1,25 coefficient compared to liked tweets, as it supposed to have greater importance.
        """
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                t1 = executor.submit(self.most_liked_accounts)
                t2 = executor.submit(self.most_retweeted_accounts)
                t3 = executor.submit(self.most_replied_to_accounts)
                t4 = executor.submit(self.get_suspicious_mentions)

            self.times_connected_user_liked = dict(t1)
            self.times_connected_user_retweeted = dict(t2)
            self.times_connected_user_replied = dict(t3)
            self.searched_user_suspicious_mentions = t4
        except ConnectionError:
            print("Oops! It seems we lost connection")
        except TimeoutError:
            print("Oops! For some reason response took to long:(")

        scored_accounts = self.compile_scored_accounts()
        self.scored_sorted_users = dict(itertools.islice(scored_accounts.items(), 10))
        return self.scored_sorted_users

    @newrelic.agent.function_trace()
    def compile_scored_accounts(self):
        score_accounts = {
            key: round(self.times_connected_user_retweeted.get(key, 0))
                 + round(self.times_connected_user_retweeted.get(key, 0) * 2)
                 + round(self.times_connected_user_replied.get(key, 0) * 1.25)
            for key in set(self.times_connected_user_retweeted)
                       | set(self.times_connected_user_retweeted)
                       | set(self.times_connected_user_replied)
        }
        scored_accounts = dict(
            sorted(score_accounts.items(), key=operator.itemgetter(1), reverse=True)
        )
        return scored_accounts

    @newrelic.agent.function_trace()
    def get_scored_users_data(self):
        users_selected_data = []
        searched_usernames = list(self.scored_sorted_users.keys())
        scores = list(self.scored_sorted_users.values())
        users = Client.get_users(
            usernames=searched_usernames,
            user_fields=[
                "profile_image_url",
                "id",
                "public_metrics",
                "created_at",
                "description",
            ],
        )
        for count, user in enumerate(range(10), start=0):
            users_selected_data.append(
                {
                    "connection_score": scores[count],
                    "name": users.data[user].name,
                    "username": users.data[user].username,
                    "bio": users.data[user].description,
                    "profile_image_url": users.data[user]
                    .profile_image_url.replace("_normal.jpg", ".jpg")
                    .replace("_normal.png", ".png"),
                    "created_at": users.data[user].created_at.strftime("%d.%m.%Y"),
                    "followers_count": users.data[user].public_metrics[
                        "followers_count"
                    ],
                    "following_count": users.data[user].public_metrics[
                        "following_count"
                    ],
                    "tweet_count": users.data[user].public_metrics["tweet_count"],
                    "times_liked": self.times_connected_user_liked.get(users.data[user].username, 0),
                    "times_retweeted": self.times_connected_user_retweeted.get(users.data[user].username, 0),
                    "times_replied": self.times_connected_user_replied.get(users.data[user].username, 0),
                }
            )

        self.scored_users_data = users_selected_data

        return self.scored_users_data


if __name__ == "__main__":
    start = time.time()

    searched_user = Scored("helloimmorgan")

    searched_user.compose_scored_account()
    searched_user.get_scored_users_data()

    print(searched_user.searched_user_data)
    print(searched_user.searched_user_suspicious_mentions)
    print(searched_user.scored_users_data)

    end = time.time()
    run_time = start - end
    print(f"Program ran:{run_time} sec")


# TODO: ' symbol infront tweepy.errors.BadRequest: 400 Bad Request The `username` query parameter value ['SkiddilyNFT] does not match ^[A-Za-z0-9_]{1,15}$
# TODO:  Connection error    raise ConnectionError(e, request=request) multithreading
# TODO:  Time ran out multithreading
# TODO: 'Error! Failed to get request token.
# TODO: f.x. @Metaarksnft IndexError: list index out of range of get_scored_users_data. when not enough connected users
