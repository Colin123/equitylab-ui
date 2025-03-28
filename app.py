import dash
from dash import html, dcc
import flask

# Set up Flask server for Dash app
server = flask.Flask(__name__)  # Required for Gunicorn

# Create Dash app instance
app = dash.Dash(__name__, server=server, suppress_callback_exceptions=True)

# Define layout for the Dash app
app.layout = html.Div([
    html.H1("Welcome to My Cool Dash App!", style={"textAlign": "center"}),

    dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'Example Bar Chart'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'line', 'name': 'Example Line Chart'},
            ],
            'layout': {
                'title': 'Dash Plot Example'
            }
        }
    )
])

# Add a simple Flask route (Optional)
@server.route("/hello")
def hello():
    return "Hello from Flask!"

# Run the app locally (for local testing)
if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
