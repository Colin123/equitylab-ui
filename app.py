import dash
from dash import html, dcc
import flask
from flask import jsonify

# Flask server setup
server = flask.Flask(__name__)
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)

# Dash layout
app.layout = html.Div([
    html.H1("Welcome to My SSL-Enabled Dash App!", style={"textAlign": "center"}),
    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Example Bar Chart'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'line', 'name': 'Example Line Chart'},
            ],
            'layout': {'title': 'Dash Plot Example'}
        }
    )
])

# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify(status="healthy"), 200 

# Define the /health endpoint on the Flask server (not on the Dash app)
@server.route('/health', methods=['GET'])
def health():
    return jsonify(status="healthy"), 200 


    
# # Redirect HTTP to HTTPS (Optional)
# @server.before_request
# def enforce_https():
#     if not flask.request.is_secure and flask.request.headers.get("X-Forwarded-Proto", "") != "https":
#         return flask.redirect(flask.request.url.replace("http://", "https://"), code=301)

if __name__ == "__main__":
    # Use your custom SSL certificate and key for HTTPS
    app.run_server(
        debug=False,
        host="0.0.0.0",
        port=8050
        #,
        # ssl_context=(
        #     "/etc/ssl/certs/recursa_biz.cert",  # Certificate file
        #     "/etc/ssl/certs/recursa_biz.key"    # Private key file
        # )
    )
