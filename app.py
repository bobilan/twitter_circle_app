# The user details get print in the console.
# so you can do whatever you want to do instead
# of printing it

from flask import Flask, render_template, request, url_for, redirect
from data import php_urls
from scored_accounts import get_php_url, main, screen_name_to_id


app = Flask(__name__)
app.secret_key = '9379992'


app.config['SERVER_NAME'] = '127.0.0.1:5700'
screen_name_input = []


@app.route('/', methods=["GET", "POST"])
def index():
    scored_accounts = {}
    if request.method == "POST":
        screen_name = request.form["name"]
        user_id = screen_name_to_id(screen_name)
        scored_accounts = [get_php_url(main(user_id), 11)]
        print(scored_accounts)
    return render_template("result.html", php_urls=scored_accounts)


@app.route('/result', methods=["GET", "POST"])
def result():
    return render_template("result.html", php_urls=php_urls)


if __name__ == "__main__":
    app.run()
    print(screen_name_input)
    print("hello world")


#TODO: most_retwetted_accs and most_replied_to_accounts remove self_account!!
#TODO: retrive php urls without "_normal"