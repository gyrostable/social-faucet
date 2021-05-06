from flask import Flask, request


app = Flask("social-faucet-control")


@app.route("/rate-limit", methods=["GET", "POST", "DELETE"])
def rate_limit():
    address = request.values.get("address")
    user_id = request.values.get("user")

    if request.method == "GET":
        value = address or user_id
        if not value:
            return "'address' or 'user' must be set", 400
        return str(app.rate_limiter.get(value))

    if request.method == "DELETE":
        if not address and not user_id:
            return "'address' or 'user' must be set", 400
        return str(app.rate_limiter.remove(address=address, user_id=user_id))

    seconds = request.form.get("seconds", "")
    if not seconds.isdecimal():
        return "'seconds' parameter not given as an integer", 400
    app.rate_limiter.add(user_id=user_id, address=address, seconds=int(seconds))
    return f"rate limited ({user_id}, {address})"


@app.route("/send-tokens", methods=["POST"])
def send_tokens():
    address = request.form.get("address")
    if not address:
        return "'address' must be given", 400
    app.faucet_executor.send_transactions(address)
    return f"sent tokens to {address}"
