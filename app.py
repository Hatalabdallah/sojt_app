from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime
import re
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
import logging
import os
from dotenv import load_dotenv
from flask_limiter.util import get_remote_address
from redis import Redis


# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')  # Use environment variable for security

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'your_databse_url')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT', 1000)
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', True)
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', False)
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_email_password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your_email@gmail.com')

db = SQLAlchemy(app)
mail = Mail(app)

# Initialize Redis
redis = Redis(host='localhost', port=6379, db=0)

email = os.getenv('EMAIL_ADDRESS')

# Initialize the Limiter with Redis storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='redis://localhost:6379'
)
limiter.init_app(app)


# Initialize the URLSafeTimedSerializer
s = URLSafeTimedSerializer(app.secret_key)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Database model for subscriptions
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Database model for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)  # To track email verification

# Database model for scheduled calls
class ScheduledCall(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

# Database model for contact submissions
class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

# Function to get the current year
def get_current_year():
    return datetime.now().year

# Home Route
@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html', current_year=get_current_year())

# Function to create a styled email body for the client
def create_client_email_body(title, first_name, last_name, message):
    current_year = datetime.now().year
    return f"""
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en" style="background:#fff!important">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width">
  <title>{title}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}" />
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css">
</head>

<body
  style="-moz-box-sizing:border-box;-ms-text-size-adjust:100%;-webkit-box-sizing:border-box;-webkit-text-size-adjust:100%;Margin:0;box-sizing:border-box;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;min-width:100%;padding:0;text-align:left;width:100%!important">
  <span class="preheader"
    style="color:#fff;display:none!important;font-size:1px;line-height:1px;max-height:0;max-width:0;mso-hide:all!important;opacity:0;overflow:hidden;visibility:hidden"></span>
  <table class="body"
    style="Margin:0;background-color:#fff;border-collapse:collapse;border-color:transparent;border-spacing:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;height:100%;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;width:100%">
    <tr style="padding:0;text-align:left;vertical-align:top">
      <td class="center" align="center" valign="top"
        style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
        <center data-parsed="" style="min-width:580px;width:100%">
          <table class="spacer float-center"
            style="Margin:0 auto;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:100%">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td height="40px"
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:40px;font-weight:400;hyphens:auto;line-height:40px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  &#xA0;
                </td>
              </tr>
            </tbody>
          </table>
          <table align="center" class="container header float-center"
            style="Margin:0 auto;background:0 0;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:580px;max-width:580px">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  <table class="row collapse logo-wrapper"
                    style="background:0 0;border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <th class="small-12 large-6 columns first"
                          style="Margin:0 auto;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:0;padding-bottom:0;padding-left:0;padding-right:0;text-align:left;width:200px;">
                          <table
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                            <tr style="padding:0;text-align:left;vertical-align:top">
                              <th valign="middle" height="49"
                                style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:middle">
                                <img width="200" class="header-logo"
                                  src="https://infronte.co.uk/infronte.png"
                                  alt=""
                                  style="-ms-interpolation-mode:bicubic;clear:both;display:block;max-width:220px;width:auto;height:auto;outline:0;text-decoration:none;max-height:49px">
                              </th>
                            </tr>
                          </table>
                        </th>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
          <table class="spacer float-center"
            style="Margin:0 auto;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:100%">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td height="32px"
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:32px;font-weight:400;hyphens:auto;line-height:32px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  &#xA0;
                </td>
              </tr>
            </tbody>
          </table>
          <table cellpadding="0" cellspacing="0" border="0" align="center" class="container body-drip float-center"
            style="Margin:0 auto;background:#fff;border-bottom-left-radius:3px;border-bottom-right-radius:3px;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:580px;max-width:580px">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  <img width="580" height="8"
                    src="https://infronte.co.uk/border-top.png"
                    alt=""
                    style="min-width:100% !important;-ms-interpolation-mode:bicubic;clear:both;display:block;width:100%!important;max-width:580px;outline:0;text-decoration:none;border-top-left-radius:3px;border-top-right-radius:3px;">
                  <table class="container-radius"
                    style="border-top-width:0;border-top-color:#e6e6e6;border-left-width:1px;border-bottom-left-radius:3px;border-bottom-right-radius:3px;border-right-width:1px;border-bottom-width:1px;border-bottom-color:#e6e6e6;border-right-color:#e6e6e6;border-left-color:#e6e6e6;border-style:solid;display:table;padding-bottom:32px;border-spacing:48px 0;border-collapse:separate;width:100%;background:#fff;max-width:580px; word-break: break-word;">
                    <tbody>
                      <tr>
                        <td>
                          <table class="row"
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                            <tbody>
                              <tr style="padding:0;text-align:left;vertical-align:top"></tr>
                            </tbody>
                          </table>
                          <table class="spacer mobile-hide"
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                            <tbody>
                              <tr style="padding:0;text-align:left;vertical-align:top">
                                <td height="32px"
                                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:32px;font-weight:400;hyphens:auto;line-height:32px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                                </td>
                              </tr>
                            </tbody>
                          </table>
                          <!-- message header end -->
                          <p>
                            Hi {first_name} {last_name},
                          </p>
                          <p>
                            {message}.
                          </p>
                          <p>
                            You will receive an email from us shortly from your mentors.
                          <p>
                            ---<br />
                            Infronte Team
                          </p>
                          <!-- message footer start -->
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <table class="spacer"
                    style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <td height="40px"
                          style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:40px;font-weight:400;hyphens:auto;line-height:40px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                          &#xA0;
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <table align="left" class="container aside-content"
                    style="Margin:0 auto;background:#fff;border-collapse:collapse;border-color:transparent;border-spacing:0;margin:0 auto;padding:0;text-align:inherit;vertical-align:top;width:580px">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <td
                          style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                          <table class="row row-wide"
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                            <tbody>
                              <tr style="padding:0;text-align:left;vertical-align:top">

                                <th class="small-12 large-4 columns last"
                                  style="Margin:0 auto;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:0!important;padding-bottom:16px;text-align:right;width:120px">
                                  <table
                                    style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:right;vertical-align:top;width:100%">
                                    <tr style="padding:0;text-align:right;vertical-align:top">
                                      <th
                                        style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;text-align:right">
                                        <table class="menu"
                                          style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:right;vertical-align:top;width:auto;margin-left:auto;border-spacing:0">
                                          <tr style="padding:0;text-align:left;vertical-align:top">
                                            <td
                                              style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:right;vertical-align:top;word-wrap:break-word">
                                              <table
                                                style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                                                <tr style="padding:0;text-align:left;vertical-align:top">
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- WhatsApp -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="https://wa.me/+447919259050"
                                                      style="Margin:0;color:#25D366;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items:center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-whatsapp"
                                                          style="font-size: 24px; color: #25D366;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- LinkedIn -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="https://www.linkedin.com/company/infronte-it-recruitment/"
                                                      style="Margin:0;color:#0077B5;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items:center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-linkedin"
                                                          style="font-size: 24px; color: #0077B5;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- Twitter -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="https://x.com/HelloInfronte"
                                                      style="Margin:0;color:#1DA1F2;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items:center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-twitter"
                                                          style="font-size: 24px; color: #1DA1F2;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- Email -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="mailto:hello@infronte.co.uk"
                                                      style="Margin:0;color:#173b3f;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items :center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-envelope"
                                                          style="font-size: 24px; color: #173b3f;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                </tr>
                                              </table>
                                            </td>
                                          </tr>
                                        </table>
                                      </th>
                                    </tr>
                                  </table>
                                </th>
                              </tr>
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
          <table class="spacer float-center"
            style="Margin:0 auto;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:100%">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td height="40px"
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:40px;font-weight:400;hyphens:auto;line-height:40px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  &#xA0;
                </td>
              </tr>
            </tbody>
          </table>
          <hr align="center" class="float-center"
            style="background:#dddedf;border:none;color:#dddedf;height:1px;margin-bottom:0;margin-top:0">
          <table align="center" class="container aside-content float-center"
            style="Margin:0 auto;background:#fff;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:580px">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  <table class="row collapsed footer"
                    style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <table class="row row-wide"
                          style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                          <tbody>
                            <tr style="padding:0;text-align:left;vertical-align:top">
                              <th class="small-12 large-12 columns first last"
                                style="Margin:0 auto;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:0!important;padding-bottom:16px;text-align:left;width:532px">
                                <table
                                  style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                                  <tr style="padding:0;text-align:left;vertical-align:top">
                                    <th
                                      style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;text-align:left">
                                      <table class="spacer"
                                        style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                                        <tbody>
                                          <tr style="padding:0;text-align:left;vertical-align:top">
                                            <td height="16px"
                                              style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:16px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                                              &#xA0;
                                            </td>
                                          </tr>
                                        </tbody>
                                      </table>
                                      <table
                                        style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:12px;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;border-spacing:0!important;">
                                        <tbody>
                                          <tr>

                                            <th class="small-12 large-6 columns first" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">Home</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/programs"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">SOJT Programs</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/terms"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">Terms of service</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/privacy"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">Privacy policy</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns last" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/about"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">About</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                          </tr>
                                        </tbody>
                                      </table>
                                      <table class="spacer"
                                        style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%;background:transparent">
                                        <tbody>
                                          <tr style="padding:0;text-align:left;vertical-align:top">
                                            <td height="16px"
                                              style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:16px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                                              &#xA0;
                                            </td>
                                          </tr>
                                        </tbody>
                                      </table>
                                      <span class="footer-description"
                                        style="color:#ACB0B8;font-size:11px;line-height:18px;padding-bottom:30px;">Infronte
                                        © { current_year }. All rights reserved.</span>
                                    </th>
                                    <th class="expander"
                                      style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;text-align:left;visibility:hidden;width:0">
                                    </th>
                                  </tr>
                                </table>
                              </th>
                            </tr>
                          </tbody>
                        </table>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
        </center>
      </td>
    </tr>
  </table>
  <div style="display:none;white-space:nowrap;font:15px courier;line-height:0">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
  </div>
  <table class="spacer"
    style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%;background:transparent">
    <tbody>
      <tr style="padding:0;text-align:left;vertical-align:top">
        <td height="16px"
          style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:16px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
          &#xA0;
        </td>
      </tr>
    </tbody>
  </table>
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>

</html>



    """

# Function to create a styled email body for yourself
def create_notification_email_body(first_name, last_name, email, message):
    current_year = datetime.now().year
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <title>New Submission Notification</title>
</head>
<body>
    <div class="container">
        <div class="alert alert-info mt-5">
            <h4 class="alert-heading">New Submission from {first_name} {last_name}</h4>
            <p>Email: {email}</p>
            <p>Message: {message}</p>
            <hr>
            <p class="mb-0">Please follow up with the client.</p>
        </div>
    </div>
</body>
</html>



<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en" style="background:#fff!important">

<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="viewport" content="width=device-width">
  <title>New Submission Notification</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}" />
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.5.0/font/bootstrap-icons.css">
</head>

<body
  style="-moz-box-sizing:border-box;-ms-text-size-adjust:100%;-webkit-box-sizing:border-box;-webkit-text-size-adjust:100%;Margin:0;box-sizing:border-box;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;min-width:100%;padding:0;text-align:left;width:100%!important">
  <span class="preheader"
    style="color:#fff;display:none!important;font-size:1px;line-height:1px;max-height:0;max-width:0;mso-hide:all!important;opacity:0;overflow:hidden;visibility:hidden"></span>
  <table class="body"
    style="Margin:0;background-color:#fff;border-collapse:collapse;border-color:transparent;border-spacing:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;height:100%;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;width:100%">
    <tr style="padding:0;text-align:left;vertical-align:top">
      <td class="center" align="center" valign="top"
        style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
        <center data-parsed="" style="min-width:580px;width:100%">
          <table class="spacer float-center"
            style="Margin:0 auto;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:100%">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td height="40px"
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:40px;font-weight:400;hyphens:auto;line-height:40px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  &#xA0;
                </td>
              </tr>
            </tbody>
          </table>
          <table align="center" class="container header float-center"
            style="Margin:0 auto;background:0 0;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:580px;max-width:580px">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  <table class="row collapse logo-wrapper"
                    style="background:0 0;border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <th class="small-12 large-6 columns first"
                          style="Margin:0 auto;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:0;padding-bottom:0;padding-left:0;padding-right:0;text-align:left;width:200px;">
                          <table
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                            <tr style="padding:0;text-align:left;vertical-align:top">
                              <th valign="middle" height="49"
                                style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:middle">
                                <img width="200" class="header-logo"
                                  src="https://infronte.co.uk/infronte.png"
                                  alt=""
                                  style="-ms-interpolation-mode:bicubic;clear:both;display:block;max-width:220px;width:auto;height:auto;outline:0;text-decoration:none;max-height:49px">
                              </th>
                            </tr>
                          </table>
                        </th>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
          <table class="spacer float-center"
            style="Margin:0 auto;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:100%">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td height="32px"
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:32px;font-weight:400;hyphens:auto;line-height:32px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  &#xA0;
                </td>
              </tr>
            </tbody>
          </table>
          <table cellpadding="0" cellspacing="0" border="0" align="center" class="container body-drip float-center"
            style="Margin:0 auto;background:#fff;border-bottom-left-radius:3px;border-bottom-right-radius:3px;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:580px;max-width:580px">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  <img width="580" height="8"
                    src="https://infronte.co.uk/border-top.png"
                    alt=""
                    style="min-width:100% !important;-ms-interpolation-mode:bicubic;clear:both;display:block;width:100%!important;max-width:580px;outline:0;text-decoration:none;border-top-left-radius:3px;border-top-right-radius:3px;">
                  <table class="container-radius"
                    style="border-top-width:0;border-top-color:#e6e6e6;border-left-width:1px;border-bottom-left-radius:3px;border-bottom-right-radius:3px;border-right-width:1px;border-bottom-width:1px;border-bottom-color:#e6e6e6;border-right-color:#e6e6e6;border-left-color:#e6e6e6;border-style:solid;display:table;padding-bottom:32px;border-spacing:48px 0;border-collapse:separate;width:100%;background:#fff;max-width:580px; word-break: break-word;">
                    <tbody>
                      <tr>
                        <td>
                          <table class="row"
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                            <tbody>
                              <tr style="padding:0;text-align:left;vertical-align:top"></tr>
                            </tbody>
                          </table>
                          <table class="spacer mobile-hide"
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                            <tbody>
                              <tr style="padding:0;text-align:left;vertical-align:top">
                                <td height="32px"
                                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:32px;font-weight:400;hyphens:auto;line-height:32px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                                </td>
                              </tr>
                            </tbody>
                          </table>
                          <!-- message header end -->
                          <p>
                            New Submission from {first_name} {last_name},
                          </p>
                          <p>
                            <p>Email: {email}</p>
                            <p>Message: {message}</p>
                          </p>
                          <p>
                            Please follow up with the client.
                          <p>
                            ---<br />
                            Infronte Management
                          </p>
                          <!-- message footer start -->
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <table class="spacer"
                    style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <td height="40px"
                          style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:40px;font-weight:400;hyphens:auto;line-height:40px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                          &#xA0;
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <table align="left" class="container aside-content"
                    style="Margin:0 auto;background:#fff;border-collapse:collapse;border-color:transparent;border-spacing:0;margin:0 auto;padding:0;text-align:inherit;vertical-align:top;width:580px">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <td
                          style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                          <table class="row row-wide"
                            style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                            <tbody>
                              <tr style="padding:0;text-align:left;vertical-align:top">

                                <th class="small-12 large-4 columns last"
                                  style="Margin:0 auto;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:0!important;padding-bottom:16px;text-align:right;width:120px">
                                  <table
                                    style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:right;vertical-align:top;width:100%">
                                    <tr style="padding:0;text-align:right;vertical-align:top">
                                      <th
                                        style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;text-align:right">
                                        <table class="menu"
                                          style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:right;vertical-align:top;width:auto;margin-left:auto;border-spacing:0">
                                          <tr style="padding:0;text-align:left;vertical-align:top">
                                            <td
                                              style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:right;vertical-align:top;word-wrap:break-word">
                                              <table
                                                style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                                                <tr style="padding:0;text-align:left;vertical-align:top">
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- WhatsApp -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="https://wa.me/+447919259050"
                                                      style="Margin:0;color:#25D366;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items:center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-whatsapp"
                                                          style="font-size: 24px; color: #25D366;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- LinkedIn -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="https://www.linkedin.com/company/infronte-it-recruitment/"
                                                      style="Margin:0;color:#0077B5;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items:center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-linkedin"
                                                          style="font-size: 24px; color: #0077B5;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- Twitter -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="https://x.com/HelloInfronte"
                                                      style="Margin:0;color:#1DA1F2;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items:center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-twitter"
                                                          style="font-size: 24px; color: #1DA1F2;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                  <th
                                                    style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                                    width="16px"></th>
                                                  <!-- Email -->
                                                  <th class="menu-item float-center"
                                                    style="Margin:0 auto;color:#0a0a0a;float:none;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:4px 0!important;text-align:center">
                                                    <a href="mailto:hello@infronte.co.uk"
                                                      style="Margin:0;color:#173b3f;font-family:Roboto,sans-serif;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;text-decoration:none">
                                                      <span class="rounded-button"
                                                        style="align-items :center;display:flex;float:right;height:42px;justify-content:center;width:42px;">
                                                        <i class="bi bi-envelope"
                                                          style="font-size: 24px; color: #173b3f;"></i>
                                                      </span>
                                                    </a>
                                                  </th>
                                                </tr>
                                              </table>
                                            </td>
                                          </tr>
                                        </table>
                                      </th>
                                    </tr>
                                  </table>
                                </th>
                              </tr>
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
          <table class="spacer float-center"
            style="Margin:0 auto;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:100%">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td height="40px"
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:40px;font-weight:400;hyphens:auto;line-height:40px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  &#xA0;
                </td>
              </tr>
            </tbody>
          </table>
          <hr align="center" class="float-center"
            style="background:#dddedf;border:none;color:#dddedf;height:1px;margin-bottom:0;margin-top:0">
          <table align="center" class="container aside-content float-center"
            style="Margin:0 auto;background:#fff;border-collapse:collapse;border-color:transparent;border-spacing:0;float:none;margin:0 auto;padding:0;text-align:center;vertical-align:top;width:580px">
            <tbody>
              <tr style="padding:0;text-align:left;vertical-align:top">
                <td
                  style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:1.3;margin:0;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                  <table class="row collapsed footer"
                    style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                    <tbody>
                      <tr style="padding:0;text-align:left;vertical-align:top">
                        <table class="row row-wide"
                          style="border-collapse:collapse;border-color:transparent;border-spacing:0;display:table;padding:0;position:relative;text-align:left;vertical-align:top;width:100%">
                          <tbody>
                            <tr style="padding:0;text-align:left;vertical-align:top">
                              <th class="small-12 large-12 columns first last"
                                style="Margin:0 auto;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0 auto;padding:0!important;padding-bottom:16px;text-align:left;width:532px">
                                <table
                                  style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                                  <tr style="padding:0;text-align:left;vertical-align:top">
                                    <th
                                      style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;text-align:left">
                                      <table class="spacer"
                                        style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%">
                                        <tbody>
                                          <tr style="padding:0;text-align:left;vertical-align:top">
                                            <td height="16px"
                                              style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:16px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                                              &#xA0;
                                            </td>
                                          </tr>
                                        </tbody>
                                      </table>
                                      <table
                                        style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:12px;font-weight:400;line-height:1.3;margin:0;padding:0;text-align:left;border-spacing:0!important;">
                                        <tbody>
                                          <tr>

                                            <th class="small-12 large-6 columns first" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">Home</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/programs"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">SOJT Programs</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/terms"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">Terms of service</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/privacy"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">Privacy policy</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                            <th class="small-12 large-6 columns last" tabindex="0" role="button"
                                              style="text-decoration:none;padding-left:0!important;text-align:left !important;"
                                              align="left">
                                              <a class="footer-link" role="link" target="_blank" rel="noopener"
                                                href="https://sojt.infronte.co.uk/about"
                                                style="Margin:0;color:#4e4e4e;font-family:Roboto,sans-serif;cursor:pointer;font-size:12px;font-weight:400;line-height:29px;display:inline-block;margin:0;padding:0;text-align:left;text-decoration:none;line-height:18px;">
                                                <font color="#4e4e4e">About</font>
                                              </a>
                                            </th>
                                            <th
                                              style="Margin:0 auto;color:#0a0a0a;width:16px;display:inline-block;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;"
                                              width="16px"></th>
                                          </tr>
                                        </tbody>
                                      </table>
                                      <table class="spacer"
                                        style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%;background:transparent">
                                        <tbody>
                                          <tr style="padding:0;text-align:left;vertical-align:top">
                                            <td height="16px"
                                              style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:16px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
                                              &#xA0;
                                            </td>
                                          </tr>
                                        </tbody>
                                      </table>
                                      <span class="footer-description"
                                        style="color:#ACB0B8;font-size:11px;line-height:18px;padding-bottom:30px;">Infronte
                                        © { current_year }. All rights reserved.</span>
                                    </th>
                                    <th class="expander"
                                      style="Margin:0;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;line-height:1.3;margin:0;padding:0!important;text-align:left;visibility:hidden;width:0">
                                    </th>
                                  </tr>
                                </table>
                              </th>
                            </tr>
                          </tbody>
                        </table>
                      </tr>
                    </tbody>
                  </table>
                </td>
              </tr>
            </tbody>
          </table>
        </center>
      </td>
    </tr>
  </table>
  <div style="display:none;white-space:nowrap;font:15px courier;line-height:0">&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
    &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
  </div>
  <table class="spacer"
    style="border-collapse:collapse;border-color:transparent;border-spacing:0;padding:0;text-align:left;vertical-align:top;width:100%;background:transparent">
    <tbody>
      <tr style="padding:0;text-align:left;vertical-align:top">
        <td height="16px"
          style="-moz-hyphens:auto;-webkit-hyphens:auto;Margin:0;border-collapse:collapse!important;color:#0a0a0a;font-family:Roboto,sans-serif;font-size:16px;font-weight:400;hyphens:auto;line-height:16px;margin:0;mso-line-height-rule:exactly;padding:0;text-align:left;vertical-align:top;word-wrap:break-word">
          &#xA0;
        </td>
      </tr>
    </tbody>
  </table>
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
  <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</body>

</html>
    """

# Update the subscribe route
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('subscribeEmail')
    
    # Validate email format
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('home'))

    # Check if the email is already subscribed
    existing_subscription = Subscription.query.filter_by(email=email).first()
    if existing_subscription:
        flash('This email is already subscribed.', 'info')
        return redirect(url_for('home'))

    # Add the email to the database
    new_subscription = Subscription(email=email)
    db.session.add(new_subscription)
    db.session.commit()

    # Send confirmation email to the client
    msg_client = Message("Thank you for subscribing!", recipients=[email])
    msg_client.html = create_client_email_body("Thank You for Subscribing!", "Subscriber", "", "You have successfully subscribed to our newsletter.")
    msg_client.sender = app.config['MAIL_DEFAULT_SENDER']  # Set the sender's email
    mail.send(msg_client)

    # Send notification email to yourself
    msg_notification = Message("New Subscription Notification",  recipients=[os.getenv("NOTIFICATION_EMAIL")])  # Replace with your email
    msg_notification.html = create_notification_email_body("Subscriber", "", email, "A new subscription has been made.")
    msg_notification.sender = app.config['MAIL_DEFAULT_SENDER']  # Set the sender's email
    mail.send(msg_notification)

    flash('Thank you for subscribing! A confirmation email has been sent.', 'success')
    return redirect(url_for('home'))

# Update the schedule_call route
@app.route('/schedule-call', methods=['POST'])
def schedule_call():
    first_name = request.form.get('ServiceFirstnameInput')
    last_name = request.form.get('serviceLastnameInput')
    email = request.form.get('serviceEmailInput')
    message = request.form.get('servieTextarea')

    # Validate form data
    if not first_name or not last_name or not email or not message:
        flash('Please fill out all fields.', 'error')
        return redirect(url_for('home'))

    # Add the scheduled call to the database
    new_call = ScheduledCall(first_name=first_name, last_name=last_name, email=email, message=message)
    db.session.add(new_call)
    db.session.commit()

    # Send confirmation email to the client
    msg_client = Message("Thank You for Scheduling a Call!", recipients=[email])
    msg_client.html = create_client_email_body("Thank You for Scheduling a Call!", first_name, last_name, "We appreciate your interest in our Structured On-The-Job Training (SOJT) programs designed to empower individuals and organizations to accelerate learning and enhance performance")
    msg_client.sender = app.config['MAIL_DEFAULT_SENDER']  # Set the sender's email
    mail.send(msg_client)

    # Send notification email to yourself
    msg_notification = Message("New Call Request Notification",  recipients=[os.getenv("NOTIFICATION_EMAIL")])  # Replace with your email
    msg_notification.html = create_notification_email_body(first_name, last_name , email, message)
    msg_notification.sender = app.config['MAIL_DEFAULT_SENDER']  # Set the sender's email
    mail.send(msg_notification)

    flash('Thank you for scheduling a call! A confirmation email has been sent.', 'success')
    return redirect(url_for('home'))

# Update the submit_contact route
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    first_name = request.form.get('contactFirstNameInput')
    last_name = request.form.get('contactLastNameInput')
    email = request.form.get('contactEmailInput')
    company_name = request.form.get('contactCompanyNameInput')
    phone = request.form.get('contactPhoneInput')
    message = request.form.get('contactTextarea')

    # Validate form data
    if not first_name or not last_name or not email or not company_name or not phone or not message:
        flash('Please fill out all fields.', 'error')
        return redirect(url_for('home'))

    # Create a new contact submission instance
    new_submission = ContactSubmission(
        first_name=first_name,
        last_name=last_name,
        email=email,
        company_name=company_name,
        phone=phone,
        message=message
    )
    
    # Add the submission to the database
    db.session.add(new_submission)
    db.session.commit()

    # Send confirmation email to the client
    msg_client = Message("Thank You for Contacting Us!", recipients=[email])
    msg_client.html = create_client_email_body("Thank You for Contacting Us!", first_name, last_name, "We appreciate your interest in our Structured On-The-Job Training (SOJT) programs designed to empower individuals and organizations to accelerate learning and enhance performance")
    msg_client.sender = app.config['MAIL_DEFAULT_SENDER']  # Set the sender's email
    mail.send(msg_client)

    # Send notification email to yourself
    msg_notification = Message("New Contact Request Notification",  recipients=[os.getenv("NOTIFICATION_EMAIL")])  # Replace with your email
    msg_notification.html = create_notification_email_body(first_name, last_name, email, message)
    msg_notification.sender = app.config['MAIL_DEFAULT_SENDER']  # Set the sender's email
    mail.send(msg_notification)

    flash('Thank you for contacting us! We will be in touch soon.', 'success')
    return redirect(url_for('home'))

# Error Handling
@app.errorhandler(404)
def page_not_found(e):
    """Render the 404 error page."""
    return render_template('404.html'), 404

# Information Pages
@app.route('/about')
def about():
    """Render the about page, describing the organization and its mission."""
    return render_template('about.html', current_year=get_current_year(), email=email)

@app.route('/contact')
def contact():
    """Render the contact page for inquiries."""
    return render_template('contact.html', current_year=get_current_year(),email=email)

@app.route('/privacy')
def privacy():
    """Render the privacy policy page."""
    return render_template('privacy.html', current_year=get_current_year())

@app.route('/terms')
def terms():
    """Render the terms and conditions page."""
    return render_template('terms.html', current_year=get_current_year())

# Programs and Careers
@app.route('/careers')
def careers():
    """Render the careers page, showcasing job opportunities and training programs."""
    return render_template('careers.html', current_year=get_current_year())

@app.route('/programs')
def programs():
    """Render the programs page, detailing the structured on-the-job training offerings."""
    return render_template('programs.html', current_year=get_current_year())

# Authentication Pages
# User Signup Route

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('signupEmailInput')
        password = request.form.get('formSignUpPassword')
        confirm_password = request.form.get('formSignUpConfirmPassword')
        terms = request.form.get('signupCheckTextCheckbox')  # Check if terms checkbox is checked

       # Validate form data
        if not email or not password or not confirm_password:
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('signup'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('signup'))

        if len(password) < 8:  # Example password strength requirement
            flash('Password must be at least 8 characters long.', 'error')
            return redirect(url_for('signup'))

        if not terms:  # Check if terms checkbox is not checked
            flash('You must agree to the terms and conditions.', 'error')
            return redirect(url_for('signup'))

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered.', 'info')
            return redirect(url_for('signup'))

        # Hash the password and create a new user
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Generate a token for email verification
        token = s.dumps(email, salt='email-confirm')
        verification_link = url_for('confirm_email', token=token, _external=True)
        msg = Message("Email Verification", recipients=[email])
        msg.body = f"Please click the link to verify your email: {verification_link}"
        mail.send(msg)

        flash('Account created successfully! Please check your email to verify your account.', 'success')
        return redirect(url_for('signin'))

    return render_template('signup.html', current_year=get_current_year())

# Email Confirmation Route
@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_verified = True
            db.session.commit()
            flash('Email verified successfully!', 'success')
            return redirect(url_for('signin'))
    except Exception as e:
        logging.error(f"Email confirmation error: {e}")
        flash('The confirmation link is invalid or has expired.', 'error')
    return redirect(url_for('signup'))

# User Signin Route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('signinEmailInput')
        password = request.form.get('formSignUpPassword')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.is_verified:
                session['user_id'] = user.id
                flash('Logged in successfully!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please verify your email before logging in.', ' warning')
                return redirect(url_for('signin'))
        flash('Invalid email or password.', 'error')
        return redirect(url_for('signin'))

    return render_template('signin.html', current_year=get_current_year())

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

# Password Reset Route
@app.route('/forget-password', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form.get('forgetEmailInput2')
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='password-reset')
            reset_link = url_for('reset_with_token', token=token, _external=True)
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Please click the link to reset your password: {reset_link}"
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'info')
            return redirect(url_for('signin'))
        flash('Email not found.', 'error')
        return redirect(url_for('forget_password'))

    return render_template('forget-password.html')

# Reset Password Route
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)
        if request.method == 'POST':
            new_password = request.form.get('newPassword')
            if len(new_password) < 8:  # Example password strength requirement
                flash('Password must be at least 8 characters long.', 'error')
                return redirect(url_for('reset_with_token', token=token))

            user = User.query.filter_by(email=email).first()
            if user:
                user.password = generate_password_hash(new_password)
                db.session.commit()
                flash('Your password has been updated!', 'success')
                return redirect(url_for('signin'))
    except Exception as e:
        logging.error(f"Password reset error: {e}")
        flash('The reset link is invalid or has expired.', 'error')
        return redirect(url_for('forget_password'))

    return render_template('reset-password.html')

# Verification and Questions
@app.route('/opt-verification')
def opt_verification():
    """Render the OTP verification page for user authentication."""
    return render_template('opt-verification.html')

@app.route('/questions')
def questions():
    """Render the frequently asked questions page."""
    return render_template('questions.html', current_year=get_current_year())

if __name__ == '__main__':
    app.run(debug=False)