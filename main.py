from server import app


if __name__ == "__main__":
    app.run(port=5000, debug=False, use_reloader=False, threaded=True)
