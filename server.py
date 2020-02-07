import os

import es
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__,
            static_folder="./static/assets",
            template_folder="./static")


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/favicon.ico')
def send_favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')


@app.route('/api/search', methods=['POST'])
def search():
    query = request.json.get('query')
    facets = request.json.get('facets')

    return jsonify(
        es.search(query, facets)
    )


@app.route('/api/facets')
def facets():
    return jsonify(
        es.get_facets()
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0')
