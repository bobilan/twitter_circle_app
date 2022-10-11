import os
from flask import Flask, render_template, request, url_for, redirect
from scored_accounts import Scored
import newrelic.agent


app = Flask(__name__)
app.secret_key = os.environ["APP_KEY"]
app.config["SERVER_NAME"] = "127.0.0.1:5700"


@app.route("/", methods=["GET", "POST"])
@newrelic.agent.function_trace()
def index():
    if request.method == "POST":
        screen_name = request.form["name"]
        searched_user = Scored(screen_name)
        searched_user.compose_scored_account()
        searched_user.get_scored_users_data()
        searched_user_data = searched_user.searched_user_data
        suspicious_mentions = searched_user.searched_user_suspicious_mentions
        suspicious_mentions_count = len(suspicious_mentions)
        connected_accounts_data = searched_user.scored_users_data

        return render_template(
            "result.html",
            searched_user_data=searched_user_data,
            suspicious_mentions=suspicious_mentions,
            connected_accounts_data=connected_accounts_data,
            suspicious_mentions_count=suspicious_mentions_count,
        )
    else:
        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
