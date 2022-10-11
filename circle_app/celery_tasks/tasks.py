from celery import shared_task

from scored_accounts import Scored


@shared_task(
    bind=True,
    autoretry_for=(Exception, ),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
    name="scored_accounts:get_scored_accounts"
)
def score_accounts_task(username: str):
    searched_user = Scored(username)
    searched_user.compose_scored_account()
    searched_user.get_scored_users_data()
    searched_user_data = searched_user.searched_user_data
    suspicious_mentions = searched_user.searched_user_suspicious_mentions
    suspicious_mentions_count = len(suspicious_mentions)
    connected_accounts_data = searched_user.scored_users_data

    return dict(
        searched_user_data=searched_user_data,
        suspicious_mentions=suspicious_mentions,
        connected_accounts_data=connected_accounts_data,
        suspicious_mentions_count=suspicious_mentions_count
    )
