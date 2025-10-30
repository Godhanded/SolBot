from flask import Flask, jsonify

app=Flask(__name__)

@app.route("/")
def base_func():
    return jsonify({
        "result": "hello world"
    }),200
    
@app.route("/name")
def get_name():
    return jsonify({
        "name":"ballo"
    }),200


app.run(debug=True)