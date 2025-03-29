from dash import Dash, html, dcc, Input, Output, callback
import dash.dash_table.Format as Format
from dash import callback_context
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
import os
import re
import logging
import dash_bootstrap_components as dbc

from flask import Flask, redirect, request, session, url_for, jsonify
from authlib.integrations.flask_client import OAuth
from functools import wraps
from urllib.parse import urlencode

class RRGCharts:

    def __init__(self):
        # Initialize Flask app
        self.server = Flask(__name__)
        self.server.secret_key = os.environ.get("SECRET_KEY") or "your-secret-key"  # Replace with a real secret key in production
        self.oauth = OAuth(self.server)

        # Auth0 configuration
        AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID")
        AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET")
        AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN")
        AUTH0_CALLBACK_URL = os.environ.get("AUTH0_CALLBACK_URL")
        AUTH0_AUDIENCE = os.environ.get("AUTH0_AUDIENCE") 

        # Register Auth0 client
        self.auth0 = self.oauth.register(
            'auth0',
            client_id=AUTH0_CLIENT_ID,
            client_secret=AUTH0_CLIENT_SECRET,
            api_base_url=f"https://{AUTH0_DOMAIN}",
            access_token_url=f"https://{AUTH0_DOMAIN}/oauth/token",
            authorize_url=f"https://{AUTH0_DOMAIN}/authorize",
            jwks_uri=f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", 
            client_kwargs={
                'scope': 'openid profile email',
            },
        )

        # Initialize Dash app
        self.app = Dash(__name__, server=self.server, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
        self.app.title = "Recursa Regime Analysis"

        # FIXME DATA
        # self.init_equity_list()

        # In a specific order so I can see cyclicals in one column and defensives in another
        self.sector_mapping = [
            ('Cyclical', 'Financials', 'XLF'),
            ('Defensive', 'Health Care', 'XLV'),
            ('Cyclical', 'Industrials', 'XLI'),
            ('Defensive', 'Consumer Staples', 'XLP'),
            ('Cyclical', 'Consumer Discretionary', 'XLY'),
            ('Defensive', 'Utilities', 'XLU'),
            ('Cyclical', 'Materials', 'XLB'),
            ('Sensitive', 'Information Technology', 'XLK'),
            ('Cyclical', 'Real Estate', 'XLRE'),
            ('Sensitive', 'Communication Services', 'XLC'),
            ('Index', 'Information Technology', 'SPY'),
            ('Sensitive', 'Energy', 'XLE')
        ]

        self.sector_industry_mapping = {
            "Energy": [
                "Oil, Gas & Consumable Fuels",
                "Energy Equipment & Services"
            ],
            "Materials": [
                "Chemicals",
                "Containers & Packaging",
                "Metals & Mining",
                "Construction Materials",
                "Paper & Forest Products"
            ],
            "Consumer Discretionary": [
                "Automobiles",
                "Automobile Components",
                "Broadline Retail",
                "Household Durables",
                "Textiles, Apparel & Luxury Goods",
                "Specialty Retail",
                "Diversified Consumer Services",        
                "Hotels, Restaurants & Leisure",
                "Leisure Products",
                "Distributors",
                "Education Services"
            ],
            "Financials": [
                "Banks",
                "Capital Markets",
                "Consumer Finance",
                "Financial Services",
                "Insurance",
                "Mortgage Real Estate Investment Trusts (REITs)"
            ],
            "Utilities": [
                "Electric Utilities",
                "Gas Utilities",
                "Independent Power and Renewable Electricity Producers",
                "Multi-Utilities",
                "Water Utilities"
            ],
            "Consumer Staples": [
                "Beverages",
                "Consumer Staples Distribution & Retail",
                "Food Products",
                "Household Products",
                "Personal Care Products",
                "Tobacco"
            ],
            "Health Care": [
                "Health Care Equipment & Supplies",
                "Health Care Providers & Services",
                "Pharmaceuticals",
                "Biotechnology",
                "Health Care Technology",
                "Life Sciences Tools & Services"
            
            ],
            "Industrials": [
                "Aerospace & Defense",
                "Commercial Services & Supplies",
                "Industrial Conglomerates",
                "Building Products",
                "Construction & Engineering",
                "Ground Transportation",
                "Electrical Equipment",
                "Machinery",
                "Professional Services",
                "Air Freight & Logistics",
                "Marine Transportation",
                "Passenger Airlines",
                "Trading Companies & Distributors",
                "Transportation Infrastructure"
            ],
            "Real Estate": [
                "Diversified REITs",
                "Residential REITs",
                "Specialized REITs",
                "Office REITs",
                "Real Estate Management & Development",
                "Retail REITs"
                
            ],
            "Information Technology": [
                "IT Services",
                "Semiconductors & Semiconductor Equipment",
                "Software",
                "Communications Equipment",
                "Electronic Equipment, Instruments & Components",
                "Technology Hardware, Storage & Peripherals"
            ],
            "Communication Services": [
                "Diversified Telecommunication Services",
                "Media",
                "Wireless Telecommunication Services",
                "Entertainment",
                "Interactive Media & Services"
            ]
        }

        # Load sector names for dropdown
        self.sorted_sector_mapping = sorted(self.sector_mapping, key=lambda x: (x[0], x[1]))
        self.sector_options = [{'label': f"{category}: {sector}", 'value': sector} for category, sector, ticker in self.sorted_sector_mapping]

        # Define a function to check if the user is authenticated
        def requires_auth(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if 'profile' not in session:
                    return redirect('/login')
                return f(*args, **kwargs)
            return decorated

        # Flask routes for login, callback, and logout
        @self.server.route('/login')
        def login():
            return self.auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL)
        
        @self.server.route('/health', methods=['GET'])
        def health():
            print('Health check called')
            return jsonify(status="healthy"), 200 

        @self.server.route('/callback')
        def callback_handling():
            self.auth0.authorize_access_token()
            resp = self.auth0.get('userinfo')
            userinfo = resp.json()
            
            session['jwt_payload'] = userinfo
            session['profile'] = {
                'user_id': userinfo['sub'],
                'name': userinfo.get('name', ''),
                'picture': userinfo.get('picture', ''),
                'email': userinfo.get('email', '')
            }
            return redirect('/dashboard')

        @self.server.route('/logout')
        def logout():
            session.clear()
            params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
            return redirect(f"https://{AUTH0_DOMAIN}/v2/logout?{urlencode(params)}")

        @self.server.route('/dashboard')
        @requires_auth
        def dashboard():
            userinfo = session['profile']
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Dashboard</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                    .container {{ width: 80%; margin: 0 auto; padding: 20px; }}
                    .profile {{ background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }}
                    .profile-header {{ display: flex; align-items: center; margin-bottom: 20px; }}
                    .profile-header img {{ width: 80px; height: 80px; border-radius: 50%; margin-right: 20px; }}
                    .btn {{ display: inline-block; padding: 10px 15px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 3px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="profile">
                        <div class="profile-header">
                            <img src="{userinfo['picture']}" alt="Profile picture">
                            <div>
                                <h2>{userinfo['name']}</h2>
                                <p>{userinfo['email']}</p>
                            </div>
                        </div>
                        <h3>User Information</h3>
                        <p>User ID: {userinfo['user_id']}</p>
                        <a class="btn" href="/logout">Logout</a>
                    </div>
                </div>
            </body>
            </html>
            """

        # Dash layout
        self.app.layout = html.Div([
            html.Button("Sector Overview", id="sector-overview-btn", n_clicks=0),
            html.Button("Industry Overview", id="industry-overview-btn", n_clicks=0),
            html.Button("Opportunity Set", id="stock-list-btn", n_clicks=0),
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content')
        ])

        self.register_callbacks()

    def init_equity_list(self):
        equities_file = './data/eodhistoricaldata_tickers_config.csv'
        self.equities_df = pd.read_csv(equities_file)
        self.equities_df = self.equities_df[self.equities_df['Type'] == 'Equity']

        self.equities_df = self.equities_df.drop(columns=['Code with extension', 'Type','Subtype1', 'SOIL', 'S1', 'CoT', 'CoTCode', 'Country', 'Rank', 'Remarks'])        
        self.equities_df.rename(columns={'Code': 'Ticker', 'Subtype2': 'Sector', 'Subtype3': 'Industry', 'TickerComma': 'Ticker Comma'}, inplace=True)

        kl_df, ks_df = self.get_latest_klass_files()

        self.equities_df = self.equities_df.merge(kl_df, on="Ticker", how="outer")  
        self.equities_df = self.equities_df.merge(ks_df, on="Ticker", how="outer")  

        self.equities_df["Classification"] = self.equities_df.apply(
            lambda row: (
                f"{row['Classification_long']}, {row['Classification_short']}"
                if row["Classification_long"] != row["Classification_short"]
                else row["Classification_long"]
            ),
            axis=1,
        )
        self.equities_df["Classification"] = self.equities_df["Classification"].str.replace(r'(,?\s*Unknown\s*,?\s*)', '', regex=True)
        self.equities_df["Classification"] = self.equities_df["Classification"].str.strip(', ')

        self.equities_df.drop(columns=["Classification_short", "Classification_long"], inplace=True)

        self.equities_df["Forward P/E"] = self.equities_df["ForwardPE_x"].combine_first(self.equities_df["ForwardPE_y"]).round(2)
        self.equities_df.drop(columns=["ForwardPE_x", "ForwardPE_y"], inplace=True)

        self.equities_df["Sub-Industry"] = self.equities_df["GicSubIndustry_x"].combine_first(self.equities_df["GicSubIndustry_y"]).round(2)
        self.equities_df.drop(columns=["GicSubIndustry_x", "GicSubIndustry_y"], inplace=True)

        os_df = self.get_latest_oi_file()

        self.equities_df = self.equities_df.merge(os_df, on="Ticker", how="outer")  

        self.equities_df["Finviz"] = self.equities_df["Ticker"].apply(lambda x: f"[Link](https://finviz.com/quote.ashx?t={x}&p=d)")

        self.equities_df  = self.equities_df.sort_values(by=['Forward P/E'], ascending=[False])

        column_order = ['Ticker', 'Description', 'Sector', 'Industry', 'Sub-Industry', 'Classification', 'Forward P/E', 'OI', 'Finviz', 'Ticker Comma']   
        self.equities_df = self.equities_df[column_order]

    def get_latest_oi_file(self):
        directory = os.path.expanduser('~/Downloads/EquityProcessing/oi/')
        pattern = re.compile(r"oi_(\d{8}_\d{6})\.csv$")
        files = [f for f in os.listdir(directory) if pattern.search(f)]
        latest_file = max(files, key=lambda f: pattern.search(f).group(1)) if files else None

        logging.getLogger(__name__).info(f"Latest oi file: {latest_file}")
        oi_df = pd.read_csv(os.path.join(directory, latest_file), index_col=0)

        drop_cols = ['Weekly', 'Monthly', 'Quarterly', 'OI Threshold']
        oi_df = oi_df.drop(columns=drop_cols)

        return oi_df

    def get_latest_klass_files(self):
        directory = os.path.expanduser('~/Downloads/EquityProcessing/kclass/')
        pattern = re.compile(r"ticker_classification_(long|short)_(\d{8}_\d{6})\.csv$")

        latest_files = {"long": None, "short": None}
        latest_timestamps = {"long": "", "short": ""}

        for filename in os.listdir(directory):
            match = pattern.search(filename)
            if match:
                file_type, timestamp = match.groups()
                if timestamp > latest_timestamps[file_type]:
                    latest_timestamps[file_type] = timestamp
                    latest_files[file_type] = filename

        logging.getLogger(__name__).info(f"Latest Long File: {latest_files['long']}")
        logging.getLogger(__name__).info(f"Latest Short File: {latest_files['short']}")

        drop_cols = ['Name', 'GicSector', 'GicIndustry']

        kfile = os.path.join(directory, latest_files['long'])
        kl = pd.read_csv(kfile)    
        kl = kl.drop(columns=drop_cols)

        kfile = os.path.join(directory, latest_files['short'])
        ks = pd.read_csv(kfile) 
        ks = ks.drop(columns=drop_cols)

        return kl, ks

    def replace_invalid_filename_chars(self, old_name):
        return old_name.replace(' ', '_').replace(',', '_and').replace('&', 'and').replace('(', '').replace(')', '')

    def register_callbacks(self):
        @self.app.callback(
            Output('page-content', 'children'),
            [Input('sector-overview-btn', 'n_clicks'), Input('industry-overview-btn', 'n_clicks'), Input('stock-list-btn', 'n_clicks'), Input('url', 'pathname')],
            prevent_initial_call=True
        )
        def display_page(sector_clicks, industry_clicks, stock_clicks, pathname):
            ctx = callback_context
            if not ctx.triggered:
                return self.sector_overview_layout()

            button_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if 'profile' not in session and pathname != '/login' and pathname != '/callback':
                return dcc.Location(pathname='/login', id='login-redirect')

            if button_id == 'sector-overview-btn':
                return self.sector_overview_layout()
            elif button_id == 'stock-list-btn':
                return self.stock_list_layout()
            elif button_id == 'industry-overview-btn':
                return self.industry_overview_layout()
            elif pathname == '/login':
                return dcc.Location(pathname='/login', id='login-redirect', href=self.auth0.authorize_redirect(redirect_uri=AUTH0_CALLBACK_URL))
            elif pathname == '/callback':
                self.auth0.authorize_access_token()
                resp = self.auth0.get('userinfo')
                userinfo = resp.json()
                
                session['jwt_payload'] = userinfo
                session['profile'] = {
                    'user_id': userinfo['sub'],
                    'name': userinfo.get('name', ''),
                    'picture': userinfo.get('picture', ''),
                    'email': userinfo.get('email', '')
                }
                return dcc.Location(pathname='/', id='callback-redirect')

            return self.sector_overview_layout()

        @self.app.callback(
            [Output('sector-market-chart', 'figure'),
            Output('industry-charts-container', 'children')],
            [Input('sector-dropdown', 'value')],
            prevent_initial_call=True
        )
        def update_chart(selected_sector):
            sector_ticker = next((ticker for category, sector, ticker in self.sector_mapping if sector == selected_sector), None)
            if not sector_ticker:
                return go.Figure(), []

            sector_file = os.path.join(self.rrg_data_home, f"sector_{self.replace_invalid_filename_chars(selected_sector)}.csv")
            market_file = os.path.join(self.market_data_dir, f"{sector_ticker}.US.csv")

            if not os.path.exists(sector_file) or not os.path.exists(market_file):
                return go.Figure(), []

            sector_df = pd.read_csv(sector_file, parse_dates=['Date'])
            market_df = pd.read_csv(market_file, parse_dates=['Date'])

            last_sector_date = sector_df['Date'].max()
            last_market_date = market_df['Date'].max()
            
            merged_df = pd.merge(market_df[['Date', 'Adjusted_close']], sector_df[['Date', 'rrg']], on='Date', how='inner')
            merged_df = merged_df.sort_values(by='Date')

            sector_name=f"{sector_ticker} Adjusted Close<br>{last_sector_date.strftime('%Y-%m-%d')}"
            market_name=f"{selected_sector} RRG <br>{last_market_date.strftime('%Y-%m-%d')}"

            sector_fig = go.Figure()

            sector_fig.add_trace(go.Scatter(x=merged_df['Date'], y=merged_df['Adjusted_close'], mode='lines', name=sector_name, line=dict(color='blue')))
            sector_fig.add_trace(go.Scatter(x=merged_df['Date'], y=merged_df['rrg'], mode='lines', name=market_name, line=dict(color='red')))

            sector_fig.update_layout(
                title=f'{selected_sector} vs {sector_ticker} Adjusted Close',
                xaxis_title='Date',
                yaxis_title='Value',
                template='plotly_dark'
            )

            industry_charts = []
            if selected_sector in self.sector_industry_mapping:
                industries = self.sector_industry_mapping[selected_sector]
                industry_charts = [
                    dcc.Graph(
                        id=self.replace_invalid_filename_chars(f'{selected_sector}-{industry}-chart'),
                        figure=self.create_industry_chart(selected_sector, industry)
                    ) for industry in industries
                ]

            return sector_fig, industry_charts

    def get_latest_oi_file(self):
        directory = os.path.expanduser('~/Downloads/EquityProcessing/oi/')
        pattern = re.compile(r"oi_(\d{8}_\d{6})\.csv$")
        files = [f for f in os.listdir(directory) if pattern.search(f)]
        latest_file = max(files, key=lambda f: pattern.search(f).group(1)) if files else None

        logging.getLogger(__name__).info(f"Latest oi file: {latest_file}")
        oi_df = pd.read_csv(os.path.join(directory, latest_file), index_col=0)

        drop_cols = ['Weekly', 'Monthly', 'Quarterly', 'OI Threshold']
        oi_df = oi_df.drop(columns=drop_cols)

        return oi_df

    def get_latest_klass_files(self):
        directory = os.path.expanduser('~/Downloads/EquityProcessing/kclass/')
        pattern = re.compile(r"ticker_classification_(long|short)_(\d{8}_\d{6})\.csv$")

        latest_files = {"long": None, "short": None}
        latest_timestamps = {"long": "", "short": ""}

        for filename in os.listdir(directory):
            match = pattern.search(filename)
            if match:
                file_type, timestamp = match.groups()
                if timestamp > latest_timestamps[file_type]:
                    latest_timestamps[file_type] = timestamp
                    latest_files[file_type] = filename

        logging.getLogger(__name__).info(f"Latest Long File: {latest_files['long']}")
        logging.getLogger(__name__).info(f"Latest Short File: {latest_files['short']}")

        drop_cols = ['Name', 'GicSector', 'GicIndustry']

        kfile = os.path.join(directory, latest_files['long'])
        kl = pd.read_csv(kfile)    
        kl = kl.drop(columns=drop_cols)

        kfile = os.path.join(directory, latest_files['short'])
        ks = pd.read_csv(kfile) 
        ks = ks.drop(columns=drop_cols)

        return kl, ks

    def replace_invalid_filename_chars(self, old_name):
        return old_name.replace(' ', '_').replace(',', '_and').replace('&', 'and').replace('(', '').replace(')', '')

    def sector_overview_layout(self):
        return html.Div([
            html.H2("Sector Overview"),
            dcc.Dropdown(
                id='sector-dropdown',
                options=self.sector_options,
                value=self.sector_options[0]['value'] if self.sector_options else None,
                style={'width': '50%'}
            ),
            dcc.Graph(id='sector-market-chart'),
            html.Div(id='industry-charts-container')
        ])

    def industry_overview_layout(self):
        return html.Div([
            html.H2("Industry Overview"),
            html.P("Select an industry to view detailed charts."),
            # Add industry selection and charts here
        ])

    def stock_list_layout(self):

        # Ensure 'Finviz' column is correctly formatted as Markdown
        self.equities_df['Finviz'] = self.equities_df['Finviz'].apply(lambda x: f"[Finviz]({x.split('[Link](')[1][:-1]})")
        
        return html.Div([
            html.H2("Opportunity Set"),
            dash_table.DataTable(
                id='stock-table',
                columns=[
                    {"name": i, "id": i, "presentation": "markdown"} if i == 'Finviz' else {"name": i, "id": i}
                    for i in self.equities_df.columns
                ],
                data=self.equities_df.to_dict('records'),
                markdown_options={"html": True},
                style_cell={'textAlign': 'left'},
                sort_action='native',
                filter_action='native',
                page_size=20,
                style_data={
                    'color': 'black',
                    'backgroundColor': 'white'
                },
                style_header={
                    'backgroundColor': 'rgb(220, 220, 220)',
                    'color': 'black',
                    'fontWeight': 'bold'
                }
            )
        ])

    def create_industry_chart(self, selected_sector, industry):
        industry_file = os.path.join(self.rrg_data_home, self.replace_invalid_filename_chars(f"{selected_sector}-{industry}.csv"))
        if not os.path.exists(industry_file):
            return go.Figure()

        industry_df = pd.read_csv(industry_file, parse_dates=['Date'])
        last_industry_date = industry_df['Date'].max()

        industry_name=f"{industry} RRG<br>{last_industry_date.strftime('%Y-%m-%d')}"

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=industry_df['Date'], y=industry_df['rrg'], mode='lines', name=industry_name, line=dict(color='green')))
        fig.update_layout(
            title=f'{industry} RRG Chart',
            xaxis_title='Date',
            yaxis_title='RRG Value',
            template='plotly_dark'
        )
        return fig

if __name__ == '__main__':
    rrg_charts = RRGCharts()
    # rrg_charts.app.run_server(debug=True)
    rrg_charts.app.run(debug=True)


# Create an instance of the RRGCharts class
rrg_charts_instance = RRGCharts()

# Make the app accessible via `app` for Gunicorn
app = rrg_charts_instance.app





