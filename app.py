from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Temporary passage list (later replaced by database)

passages = {
"kc001": "This is a sample passage text used for testing the typing system.",
"kc002": "Another example passage stored temporarily inside the system."
}

@app.route("/")
def home():
    return render_template("passage_code.html")


@app.route("/start", methods=["POST"])
def start():

    code = request.form["code"]

    if code not in passages:
        return render_template("passage_code.html", error="Invalid Passage Code")

    return render_template("typing_test.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)