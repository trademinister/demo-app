import os
import urllib
import traceback

from flask import Flask, redirect, request, render_template
import shopify
import pyactiveresource

from lib.signature_validation import shopify_sign_valid_ids_required

app = Flask(__name__)
app.config.from_pyfile('config.py')

base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, 'data')
token_dir = os.path.join(base_dir, 'data', 'token')
merchant_dir = os.path.join(base_dir, 'data', 'merchant')

if not os.path.isdir(os.path.join(base_dir, 'data')):
    os.mkdir(os.path.join(base_dir, 'data'))

if not os.path.isdir(token_dir):
    os.mkdir(token_dir)

if not os.path.isdir(merchant_dir):
    os.mkdir(merchant_dir)


def reinstall_app(shop_name):
    app.logger.info('reinstall app for {}'.format(shop_name))
    args = urllib.parse.urlencode({'shop': shop_name})
    url = 'https://{}/authorize?{}'
    # редирект в админку
    return redirect(url.format(app.config.get('HOSTNAME'), args))


def get_token(shop_name):
    token_path = os.path.join(token_dir, shop_name)

    with open(token_path) as f:
        token = f.read().strip()

    return token


@app.route('/app/')
@shopify_sign_valid_ids_required
def home():
    shop_name = request.args.get('shop')
    token_path = os.path.join(token_dir, shop_name)

    if not os.path.exists(token_path):

        return reinstall_app(shop_name)

    with open(token_path) as f:
        token = f.read().strip()

    try:

        with shopify.Session.temp(shop_name,
                                  app.config.get('SHOPIFY_VERSION'), token):
            shop = shopify.Shop.current()

    except pyactiveresource.connection.UnauthorizedAccess:
        app.logger.warning(traceback.format_exc())

        return reinstall_app(shop_name)

    return 'demo publicapp'


@app.route('/install')
def install():
    return render_template('install.html')


@app.route('/authorize')
def authorize():
    """авторизация приложения"""
    shop_name = request.args.get('shop')
    shopify.Session.setup(api_key=app.config['SHOPIFY_API_KEY'],
                          secret=app.config['SHOPIFY_API_SECRET'])
    session = shopify.Session(shop_name, app.config['SHOPIFY_VERSION'])
    scope = app.config.get('SCOPE')
    redirect_url = app.config['REDIRECT_URL']
    print(redirect_url)
    permission_url = session.create_permission_url(scope, redirect_url)

    return redirect(permission_url)


@app.route('/finalize')
def finalize():
    shop_name = request.args.get('shop')
    shopify.Session.setup(api_key=app.config['SHOPIFY_API_KEY'],
                          secret=app.config['SHOPIFY_API_SECRET'])
    session = shopify.Session(shop_name, app.config['SHOPIFY_VERSION'])
    token = session.request_token(request.args.to_dict())
    print(token)
    # сохраняем токен
    filepath = os.path.join(token_dir, shop_name)

    with open(filepath, 'w') as f:
        f.write(token)

    url = 'https://{}/admin/apps/{}'
    # редирект в админку
    return redirect(url.format(shop_name, app.config.get('SHOPIFY_API_KEY')))


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8003)
