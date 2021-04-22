# TTN Munich Node Watchdog
The TTN Munich Node Watchdog watches your LoRaWAN nodes, and let's you know when they've been gone for a while.
## Usage
### Requirements
* A LoRaWAN node (or more)
* A TTN v3 application

### Quickstart
In your TTN v3 application, add a new Webhook (under Integrations -> Webhook). Use the following settings:
<table class="table table-bordered">
    <tr>
        <th>Webhook ID</th>
        <td><i>choose your ID, e.g.<i><code>ttn-node-watchdog</code></td>
    </tr>
    <tr>
        <th>Webhook Format</th>
        <td>JSON</td>
    </tr>
    <tr>
        <th>Base URL</th>
        <td><code>https://watchdog.platform.ttn-munich.de/api/v1/ping/&lt;email address&gt;</code></td>
    </tr>
    <tr>
        <th>Downlink API Key</th>
        <td><i>leave emtpy</i></td>
    </tr>
    <tr>
        <th>Uplink message</th>
        <td><i>Set check box, leave text field empty</i></td>
    </tr>
</table>
You'll receive an email from the watchdog to confirm your email address. Once you've confirmed your address, you'll receive a message for every node that hasn't sent an uplink message for more than 24h.

## Setup
Simple dev setup:
```
git clone https://github.com/tiefpunkt/ttn-node-watchdog.git
cd ttn-node-watchdog
python3 -mvenv env
. env/bin/activate
pip install -r requirements.txt
cp config.yml.sample config.yml
vi config.yml
export FLASK_APP=main.py
export FLASK_ENV=development
flask init-db
flask run
```

To check the current device status, you need to run a regular cron job.
```
flask check-devices
```

## Notes
* SQL Alchemy:
  * https://flask.palletsprojects.com/en/1.1.x/patterns/sqlalchemy/
  * https://docs.sqlalchemy.org/en/14/orm/mapping_styles.html#orm-declarative-mapping
  * https://towardsdatascience.com/use-flask-and-sqlalchemy-not-flask-sqlalchemy-5a64fafe22a4
  * https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
  * Migrations: https://alembic.sqlalchemy.org/en/latest/autogenerate.html
* Blueprints: https://www.digitalocean.com/community/tutorials/build-a-crud-web-app-with-python-and-flask-part-one#blueprints

Reference: https://github.com/healthchecks/healthchecks

* Email
  * Providers with free offers: https://www.mailjet.de/
