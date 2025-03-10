import stripe
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
from datetime import datetime
from flask import Flask, request
import random
import os
import pandas as pd
import schedule
import time
import threading

# Configuration
STRIPE_API_KEY = "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"  # Your Stripe Secret Key
SENDER_EMAIL = "support@gadgetxafrica.store"  # Your Gmail address
EMAIL_PASSWORD = "Asd123jr!"  # Gmail App Password
STRIPE_WEBHOOK_SECRET = "whsec_Gg9HaREbzSadpAbhua7WBcO6uPK6tOhp"  # Your Stripe Webhook Secret

stripe.api_key = STRIPE_API_KEY
app = Flask(__name__)

# Global list to store orders
orders = []

def get_html_confirmation(session):
    """Generate HTML order confirmation email content based on Stripe Checkout Session data."""
    customer_name = session.customer_details.name or "Customer"
    customer_email = session.customer_details.email
    customer_phone = session.customer_details.phone or ""
    transaction_id = session.payment_intent.id
    product_name = session.line_items.data[0].description  # Assumes single item for simplicity
    amount_paid = session.amount_total / 100  # Convert cents to dollars
    order_date = datetime.now().strftime("%d %B, %Y")  # e.g., 19 June, 2024
    shipping_details = session.shipping_details or {}
    billing_details = session.payment_intent.charges.data[0].billing_details
    shipping_cost = session.shipping_cost.amount_total / 100 if session.shipping_cost else 0
    shipping_method = session.shipping_options[0]["shipping_rate"].replace("shr_", "Standard Shipping") if session.shipping_options else "Standard Shipping"
    delivery_date = (datetime.now().replace(day=datetime.now().day + 5)).strftime("%a %d/%m/%Y")  # Simulated delivery date
    
    # Retrieve product image from Stripe Product
    product_id = session.line_items.data[0].price.product
    product = stripe.Product.retrieve(product_id)
    product_image = product.images[0] if product.images else "https://via.placeholder.com/96"  # Fallback if no image

    # HTML Template with dynamic data, including product image
    html_content = f"""
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <meta content="Order Confirmation" property="og:title" />
        <title>Order Confirmation</title>
        <style type="text/css">
            @font-face {{
                font-family: 'SF UI Display Medium';
                src: local('SF UI Display Medium'), url('https://email.images.apple.com/rover/aos/moe/Fonts/SFUIDisplay-Medium.ttf');
            }}
            @font-face {{
                font-family: 'SF UI Text Regular';
                src: local('SF UI Text Regular'), url('https://email.images.apple.com/rover/aos/moe/Fonts/SFUIText-Regular.ttf');
            }}
            body {{
                width: 100% !important; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; background-color: #FFFFFF; margin: 0; padding: 0;
            }}
            img {{ outline: none; text-decoration: none; border: none; }}
            a img {{ border: none; }}
            p {{ margin: 1em 0; }}
            br {{ line-height: 12px; }}
            h1, h2, h3, h4, h5, h6 {{ color: #333333; margin: 0; padding: 0; border: 0; font-weight: normal; }}
            a {{ color: #0070C9; text-decoration: none; }}
            a:hover, a:focus {{ text-decoration: underline; }}
            ul {{ padding-left: 20px; padding-top: 6px; padding-bottom: 0; margin-bottom: 5px; }}
            li {{ padding-left: 0 !important; padding-bottom: 9px !important; }}
            table td {{ border-collapse: collapse; }}
            #outlook a {{ padding: 0; }}
            .ExternalClass {{ width: 100%; }}
            .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {{ line-height: 100%; }}
            .main-table {{ width: 660px; margin: 0 auto; }}
            .header-logo-img {{ display: block; height: 25px; width: auto; }}
            .heading-email {{ font-family: 'SF UI Display Medium', system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 34px; line-height: 37px; color: #333333; }}
            .sub-heading {{ font-size: 17px; line-height: 24px; color: #333333; }}
            .order-num {{ font-size: 14px; line-height: 21px; color: #333333; }}
            .order-num .bold {{ font-weight: 600; }}
            .sectionHeading {{ font-family: 'SF UI Display Medium', system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-weight: 500; font-size: 22px; line-height: 27px; color: #333333; }}
            .subsec-heading {{ font-weight: 600; font-size: 17px; line-height: 26px; color: #333333; }}
            .gen-txt {{ font-size: 17px; line-height: 26px; color: #333333; }}
            .product-name-td {{ font-weight: 600; font-size: 17px; line-height: 26px; }}
            .base-price-td, .product-quantity, .total-price {{ font-size: 17px; line-height: 26px; }}
            .total-price {{ font-weight: 600; }}
            .amt-label-td, .amt-value-td {{ font-size: 17px; line-height: 24px; }}
            .amt-label-td.bold, .amt-value-td.bold {{ font-weight: 600; }}
            .footer-copyright-td, .footer-links-div {{ font-size: 11px; line-height: 16px; color: #888888; }}
            .footer-menu-item-td {{ font-size: 12px; line-height: 18px; color: #888888; }}
            .footer-links-a {{ color: #555555; }}
            .moe-line-col div {{ background-color: #D6D6D6; height: 1px; font-size: 1px; }}
            .aapl-link {{ color: #0070C9; }}
            @media only screen and (min-width: 50px) and (max-width: 768px) {{
                .main-table {{ width: 100% !important; padding-bottom: 20px !important; }}
                .apple-logo-td {{ padding-top: 15px !important; padding-left: 20px !important; }}
                .header-logo-img {{ height: 23px !important; width: auto !important; }}
                .greeting-td {{ padding: 41px 20px 25px !important; }}
                .heading-email {{ font-size: 28px !important; line-height: 31px !important; }}
                .sub-heading {{ line-height: 26px !important; padding-top: 10px !important; }}
                .order-num-td {{ padding: 0 20px 27px !important; }}
                .section-heading-table, .section-details-table, .product-list-table, .amt-row-table {{ width: 100% !important; padding: 0 20px !important; }}
                .section-items-heading-td {{ padding-bottom: 14px !important; }}
                .render-lineitems-table {{ padding-top: 39px !important; }}
                .product-image-td {{ padding-left: 20px !important; padding-right: 7px !important; }}
                .product-image-img {{ width: 86px !important; height: 86px !important; }}
                .payment-section-td {{ padding: 39px 20px 32px !important; }}
                .footer-container-table {{ padding: 1px 20px !important; }}
                .footer-menu-item-table {{ width: 100% !important; display: block !important; padding: 13px 0 11px !important; border-bottom: 1px solid #D6D6D6 !important; }}
                .hide-line {{ display: none !important; }}
            }}
        </style>
    </head>
    <body style="-webkit-font-smoothing: antialiased; background-color: #FFFFFF;">
        <center>
            <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td align="center">
                        <table class="main-table" align="center" width="660" border="0" cellpadding="0" cellspacing="0">
                            <tr>
                                <td class="apple-logo-td" style="padding-top: 32px;" align="left" valign="top">
                                    <img class="header-logo-img" src="https://email.images.apple.com/rover/aos/moe/apple_icon_2x.png" alt="Apple" border="0">
                                </td>
                            </tr>
                            <tr>
                                <td class="greeting-td" style="padding: 75px 0 51px;" align="left" valign="top">
                                    <h1 class="heading-email">Thank you for your order.</h1>
                                    <p class="sub-heading" style="padding-top: 13px;">We'll let you know when your items are on their way.</p>
                                </td>
                            </tr>
                            <tr>
                                <td class="order-num-td" style="padding-bottom: 14px;">
                                    <div class="order-num">
                                        <span class="bold">Order Number: </span>
                                        <span><a href="#" class="aapl-link" aria-label="Order Number {transaction_id}">{transaction_id}</a></span>
                                    </div>
                                    <div class="order-num">
                                        <span class="bold">Ordered on: </span>
                                        <span>{order_date}</span>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td class="moe-line-col" style="background-color: #D6D6D6;" height="1" align="left" valign="top">
                                    <div></div>
                                </td>
                            </tr>
                            <tr>
                                <td align="center" valign="top">
                                    <table class="render-lineitems-table" width="100%" border="0" cellpadding="0" cellspacing="0" style="padding-top: 43px;">
                                        <tr>
                                            <td>
                                                <table class="section-heading-table" width="29%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="section-items-heading-td" align="left" valign="top">
                                                            <h2 class="sectionHeading">Items to be Shipped</h2>
                                                        </td>
                                                    </tr>
                                                </table>
                                                <table class="product-list-table" width="66.5%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="pad-lr" align="left" valign="top" style="padding: 0 20px;">
                                                            <div style="font-weight: 600; font-size: 17px; line-height: 26px; padding-bottom: 3px;">Shipment 1</div>
                                                            <div class="gen-txt">
                                                                <span style="font-weight: 600;">Ships:</span> 1 business day
                                                            </div>
                                                            <div class="gen-txt">
                                                                <span style="font-weight: 600;">Delivers:</span> {delivery_date} by {shipping_method}
                                                            </div>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td align="left" valign="top">
                                                            <table width="100%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                                <tr>
                                                                    <td class="pad-lr" align="left" valign="top" style="padding: 0 20px;">
                                                                        <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0">
                                                                            <tr>
                                                                                <td style="height: 21px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="21" width="1" style="display: block;"></td>
                                                                            </tr>
                                                                            <tr>
                                                                                <td class="moe-line-col" style="background-color: #D6D6D6;" height="1">
                                                                                    <div></div>
                                                                                </td>
                                                                            </tr>
                                                                            <tr>
                                                                                <td style="height: 28px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="28" width="1" style="display: block;"></td>
                                                                            </tr>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                            <table class="line-item-table" width="100%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                                <tr>
                                                                    <td class="product-image-td" align="center" width="96" style="padding-right: 10px;">
                                                                        <img class="product-image-img" src="{product_image}" alt="{product_name}" style="display: block;" width="96" height="96">
                                                                    </td>
                                                                    <td align="left" valign="top">
                                                                        <table class="item-details-table" width="100%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                                            <tr>
                                                                                <td class="product-name-td">{product_name}</td>
                                                                            </tr>
                                                                            <tr>
                                                                                <td class="base-price-td" style="padding-top: 6px;">${amount_paid - shipping_cost:.2f}</td>
                                                                            </tr>
                                                                            <tr>
                                                                                <td class="qty-price-divider" style="padding-top: 6px;">
                                                                                    <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0" style="height: 1px;">
                                                                                        <tr>
                                                                                            <td class="moe-line-col" style="background-color: #D6D6D6;" height="1">
                                                                                                <div></div>
                                                                                            </td>
                                                                                        </tr>
                                                                                    </table>
                                                                                </td>
                                                                            </tr>
                                                                            <tr>
                                                                                <td class="qty-price-td" style="padding-top: 6px;">
                                                                                    <table class="product-quantity-table" width="45%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                                                        <tr>
                                                                                            <td class="product-quantity"><nobr>Qty 1</nobr></td>
                                                                                        </tr>
                                                                                    </table>
                                                                                    <table class="total-price-table" width="50%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                                                        <tr>
                                                                                            <td class="total-price">${amount_paid - shipping_cost:.2f}</td>
                                                                                        </tr>
                                                                                    </table>
                                                                                </td>
                                                                            </tr>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td>
                                                <table class="section-details-table" width="66.5%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="section-details-td" align="left" valign="top" style="padding: 0 20px;">
                                                            <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0">
                                                                <tr>
                                                                    <td style="height: 30px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="30" width="1" style="display: block;"></td>
                                                                </tr>
                                                                <tr>
                                                                    <td class="moe-line-col" style="background-color: #D6D6D6;" height="1">
                                                                        <div></div>
                                                                    </td>
                                                                </tr>
                                                                <tr>
                                                                    <td style="height: 30px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="30" width="1" style="display: block;"></td>
                                                                </tr>
                                                            </table>
                                                            <h3 class="subsec-heading">Shipping Address:</h3>
                                                            <div class="gen-txt">{shipping_details.get('name', customer_name)}</div>
                                                            <div class="gen-txt">{shipping_details.address.line1}</div>
                                                            {"<div class='gen-txt'>{shipping_details.address.line2}</div>" if shipping_details.address.line2 else ""}
                                                            <div class="gen-txt">{shipping_details.address.city}</div>
                                                            <div class="gen-txt">{shipping_details.address.state} {shipping_details.address.postal_code}</div>
                                                            <div class="gen-txt">{shipping_details.address.country}</div>
                                                            <h3 class="subsec-heading" style="padding-top: 23px;">Shipment Notifications:</h3>
                                                            <div class="gen-txt" style="word-wrap: break-word; word-break: break-all;">{customer_email}</div>
                                                            <div class="gen-txt">•••••••••{customer_phone[-2:] if customer_phone else 'N/A'}</div>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                    <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="height: 45px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="45" width="1" style="display: block;"></td>
                                        </tr>
                                        <tr>
                                            <td class="moe-line-col" style="background-color: #D6D6D6;" height="1">
                                                <div></div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="height: 1px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="1" width="1" style="display: block;"></td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td class="payment-section-td" style="padding: 43px 0 32px;">
                                    <table class="section-heading-table" width="29%" align="left" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td class="section-items-heading-td" align="left" valign="top">
                                                <h2 class="sectionHeading">Payment Details</h2>
                                            </td>
                                        </tr>
                                    </table>
                                    <table class="section-details-table" width="66.5%" align="right" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td class="section-details-td" align="left" valign="top" style="padding: 0 20px;">
                                                <h3 class="subsec-heading">Paid with:</h3>
                                                <table class="payment-logo-table" width="100%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td align="left" style="padding: 5px 0 23px;">
                                                            <div style="white-space: nowrap;">
                                                                <img alt="{session.payment_intent.payment_method_types[0].capitalize()}" src="https://via.placeholder.com/45" height="auto" width="45" border="0" style="vertical-align: middle;">
                                                                <span style="font-size: 14px; line-height: 21px; vertical-align: middle;">••••{session.payment_intent.charges.data[0].payment_method_details.card.last4}</span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </table>
                                                <h3 class="subsec-heading" style="padding-top: 23px;">Bills to:</h3>
                                                <div class="gen-txt">
                                                    <div>{billing_details.name or customer_name}</div>
                                                    <div>{billing_details.address.line1}</div>
                                                    {"<div class='gen-txt'>{billing_details.address.line2}</div>" if billing_details.address.line2 else ""}
                                                    <div>{billing_details.address.city}</div>
                                                    <div>{billing_details.address.state} {billing_details.address.postal_code}</div>
                                                    <div>{billing_details.address.country}</div>
                                                </div>
                                                <h3 class="subsec-heading" style="padding-top: 23px;">Contact information:</h3>
                                                <div class="gen-txt" style="word-wrap: break-word; word-break: break-all;">{customer_email}</div>
                                                <div class="gen-txt">•••••••••{customer_phone[-2:] if customer_phone else 'N/A'}</div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td class="amts-section-td" style="padding-bottom: 41px;" align="center">
                                    <table class="amt-row-table" width="66.5%" align="right" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td align="center">
                                                <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td style="height: 1px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="1" width="1" style="display: block;"></td>
                                                    </tr>
                                                    <tr>
                                                        <td class="moe-line-col" style="background-color: #D6D6D6;" height="1">
                                                            <div></div>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="height: 18px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="18" width="1" style="display: block;"></td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="amt-row-td" style="padding-top: 4px;">
                                                <table class="amt-label-table" width="49%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="amt-label-td">Subtotal</td>
                                                    </tr>
                                                </table>
                                                <table class="amt-value-table" width="49%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="amt-value-td" style="white-space: nowrap;">${amount_paid - shipping_cost:.2f}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="amt-row-td" style="padding-top: 4px;">
                                                <table class="amt-label-table" width="49%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="amt-label-td">Shipping</td>
                                                    </tr>
                                                </table>
                                                <table class="amt-value-table" width="49%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="amt-value-td" style="white-space: nowrap;">${shipping_cost:.2f}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="amt-row-td">
                                                <table class="amt-divider-table" width="100%" align="right" border="0" cellpadding="0" cellspacing="0" style="margin-top: 11px;">
                                                    <tr>
                                                        <td style="background-color: #D6D6D6;" height="1"></td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="amt-row-td" style="padding-top: 4px;">
                                                <table class="amt-label-table" width="49%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="amt-label-td bold">Total</td>
                                                    </tr>
                                                </table>
                                                <table class="amt-value-table" width="49%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="amt-value-td bold" style="white-space: nowrap;">${amount_paid:.2f}</td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <table width="100%" align="center" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td style="height: 1px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="1" width="1" style="display: block;"></td>
                                        </tr>
                                        <tr>
                                            <td class="moe-line-col" style="background-color: #D6D6D6;" height="1">
                                                <div></div>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="height: 43px;"><img src="https://email.images.apple.com/dm/groups/aos/om/global/cmon/spacer.gif" alt="" border="0" height="43" width="1" style="display: block;"></td>
                                        </tr>
                                    </table>
                                    <table class="qa-table" width="100%" border="0" cellpadding="0" cellspacing="0" style="padding-bottom: 10px;">
                                        <tr>
                                            <td>
                                                <table class="section-heading-table" width="29%" align="left" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="section-items-heading-td" align="left" valign="top">
                                                            <h2 class="sectionHeading">Questions</h2>
                                                        </td>
                                                    </tr>
                                                </table>
                                                <table class="answers-table" width="66.5%" align="right" border="0" cellpadding="0" cellspacing="0">
                                                    <tr>
                                                        <td class="answers-td" align="left" valign="top" style="padding: 0 20px;">
                                                            <h3 class="subsec-heading">When will I get my items?</h3>
                                                            <div style="padding-bottom: 23px;">
                                                                The shipping estimates above tell you when your items are expected to arrive. As each item leaves our warehouse, we’ll email you with carrier and tracking information.
                                                                <div style="padding-top: 12px;">Ordered more than one item? You’ll get a separate email as each item ships. There are no additional shipping fees for these items.</div>
                                                            </div>
                                                            <h3 class="subsec-heading">How do I view or change my order?</h3>
                                                            <div style="padding-bottom: 23px;">
                                                                Visit online <a href="#" class="aapl-link">Order Status</a> to view the most up-to-date status and make changes to your order. To learn more about shipping, changing your order or returns, please visit online <a href="#" class="aapl-link" style="color: #0085cf;">Help</a>.
                                                                <div style="padding-top: 12px;">You can also call Customer Service on 1800-80-6419, Monday to Friday from 9:00 am to 6:00 pm. Please have your order number available.</div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                        <table class="footer-container-table" width="100%" align="center" border="0" cellpadding="0" cellspacing="0" bgcolor="#F2F2F2" style="padding: 19px 0 13px;">
                            <tr>
                                <td align="center">
                                    <table class="footer-section-table" align="center" width="660" bgcolor="#F2F2F2" border="0" cellpadding="0" cellspacing="0">
                                        <tr>
                                            <td class="footer-copyright-td" style="padding: 0 16px;">
                                                <table class="footer-menu-table" width="100%" align="center" border="0" cellpadding="0" cellspacing="0" style="padding-bottom: 14px; border-bottom: 1px solid #D6D6D6;">
                                                    <tr>
                                                        <td align="center" valign="top">
                                                            <table class="footer-menu-item-table" width="auto" border="0" cellpadding="0" cellspacing="0" style="display: inline-table;">
                                                                <tr>
                                                                    <td class="footer-menu-item-td">
                                                                        <a href="#">Shop Online</a>
                                                                        <span class="hide-line" style="color: #D6D6D6;" aria-hidden="true">  |  </span>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                            <table class="footer-menu-item-table" width="auto" border="0" cellpadding="0" cellspacing="0" style="display: inline-table;">
                                                                <tr>
                                                                    <td class="footer-menu-item-td">
                                                                        <a href="#">Find a Store</a>
                                                                        <span class="hide-line" style="color: #D6D6D6;" aria-hidden="true">  |  </span>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                            <table class="footer-menu-item-table" width="auto" border="0" cellpadding="0" cellspacing="0" style="display: inline-table;">
                                                                <tr>
                                                                    <td class="footer-menu-item-td">
                                                                        <span style="white-space: nowrap;">1800 806 419</span>
                                                                        <span class="hide-line" style="color: #D6D6D6;" aria-hidden="true">  |  </span>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                            <table class="footer-menu-item-table" width="auto" border="0" cellpadding="0" cellspacing="0" style="display: inline-table;">
                                                                <tr>
                                                                    <td class="footer-menu-item-td">
                                                                        <a href="#">Get the Store App</a>
                                                                    </td>
                                                                </tr>
                                                            </table>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td class="footer-copyright-td" style="padding: 19px 16px 0;" align="left" valign="top">
                                                <div>Copyright © 2024 Your Store Inc. All rights reserved.</div>
                                                <div class="footer-links-div" style="padding-top: 16px;">
                                                    <a class="footer-links-a" href="#" target="_blank">Terms of Use</a>
                                                     <span aria-hidden="true">|</span> 
                                                    <a class="footer-links-a" href="#" target="_blank">Privacy Policy</a>
                                                     <span aria-hidden="true">|</span> 
                                                    <a class="footer-links-a" href="#" target="_blank">Sales and Refunds</a>
                                                </div>
                                            </td>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </center>
    </body>
    </html>
    """
    return html_content

def generate_receipt_pdf(session):
    """Generate a receipt PDF based on the Apple invoice template."""
    customer_name = session.customer_details.name or "Customer"
    customer_email = session.customer_details.email
    transaction_id = session.payment_intent.id
    product_name = session.line_items.data[0].description
    amount_paid = session.amount_total / 100  # In dollars (adjust currency as needed)
    invoice_date = datetime.now().strftime("%d.%m.%Y")  # e.g., 19.06.2024
    order_date = datetime.now().strftime("%d.%m.%Y")
    shipping_details = session.shipping_details or {}
    billing_details = session.payment_intent.charges.data[0].billing_details
    shipping_cost = session.shipping_cost.amount_total / 100 if session.shipping_cost else 0
    invoice_number = f"MA{random.randint(10000000, 99999999)}"  # Simulated invoice number
    document_number = f"05{random.randint(1000000, 9999999)}"  # Simulated document number
    apple_order_number = f"ADC{random.randint(10000000, 99999999)}"  # Simulated Apple order number
    web_order_number = transaction_id  # Using Stripe PaymentIntent ID
    customer_number = f"9{random.randint(10000, 99999)}"  # Simulated customer number
    purchase_order_number = f"06{random.randint(10000000, 99999999)}"  # Simulated PO number
    card_last4 = session.payment_intent.charges.data[0].payment_method_details.card.last4

    pdf = FPDF()
    
    # Page 1
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Invoice/Receipt", ln=True, align="L")
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, "Apple Fifth Avenue", ln=True)  # Replace with your company name
    pdf.cell(0, 5, "796 Fifth Avenue", ln=True)  # Replace with your address
    pdf.cell(0, 5, "New York, NY 10153", ln=True)
    pdf.cell(0, 5, "fifthavenue@apple.com", ln=True)
    pdf.cell(0, 5, "212-336-1440", ln=True)
    pdf.cell(0, 5, "www.apple.com/retail/fifthavenue", ln=True)
    pdf.ln(10)
    
    # Invoice Details
    pdf.cell(0, 5, f"Invoice Number: {invoice_number}", ln=True)
    pdf.cell(0, 5, f"Document No: {document_number}", ln=True)
    pdf.cell(0, 5, f"Order Number: {apple_order_number}", ln=True)
    pdf.cell(0, 5, f"Invoice Date: {invoice_date}", ln=True)
    pdf.cell(0, 5, f"Web Order Number: {web_order_number}", ln=True)
    pdf.cell(0, 5, f"Customer Number: {customer_number}", ln=True)
    pdf.ln(10)
    
    # Sold To
    pdf.cell(0, 5, "Sold To", ln=True)
    pdf.cell(0, 5, f"{customer_name}", ln=True)
    pdf.cell(0, 5, f"{billing_details.address.line1}", ln=True)
    if billing_details.address.line2:
        pdf.cell(0, 5, f"{billing_details.address.line2}", ln=True)
    pdf.cell(0, 5, f"{billing_details.address.city}", ln=True)
    pdf.cell(0, 5, f"{billing_details.address.state} {billing_details.address.postal_code}", ln=True)
    pdf.cell(0, 5, f"{billing_details.address.country}", ln=True)
    pdf.ln(5)
    
        # Ship To (continued)
    if shipping_details.address.line2:
        pdf.cell(0, 5, f"{shipping_details.address.line2}", ln=True)
    pdf.cell(0, 5, f"{shipping_details.address.city}", ln=True)
    pdf.cell(0, 5, f"{shipping_details.address.state} {shipping_details.address.postal_code}", ln=True)
    pdf.cell(0, 5, f"{shipping_details.address.country}", ln=True)
    pdf.ln(5)
    
    # Purchase Order
    pdf.cell(0, 5, f"Purchase Order Number: {purchase_order_number}", ln=True)
    pdf.cell(0, 5, f"Date Ordered: {order_date}", ln=True)
    pdf.ln(10)
    
    # Item Table
    pdf.set_font("Arial", "B", 10)
    pdf.cell(20, 10, "Item Number", border=1)
    pdf.cell(30, 10, "Product Number", border=1)
    pdf.cell(50, 10, "Product Description", border=1)
    pdf.cell(25, 10, "Qty Shipped", border=1)
    pdf.cell(25, 10, "Value Per Unit", border=1)
    pdf.cell(25, 10, "Extended Value", border=1)
    pdf.cell(15, 10, "ST %", border=1)
    pdf.cell(25, 10, "ST Amount", border=1, ln=True)
    
    pdf.set_font("Arial", size=10)
    for i, item in enumerate(session.line_items.data):
        item_number = f"{(i + 1):06d}"  # e.g., 000010, 000020
        product_id = item.price.product  # Stripe Product ID
        product_description = item.description[:20]  # Truncated for space
        quantity = item.quantity
        value_per_unit = item.amount_total / (item.quantity * 100)  # Unit price in dollars
        extended_value = item.amount_total / 100  # Total price for this line item
        st_percent = 0.00  # Assuming no service tax; adjust if needed
        st_amount = extended_value * (st_percent / 100)

        pdf.cell(20, 10, item_number, border=1)
        pdf.cell(30, 10, product_id, border=1)
        pdf.cell(50, 10, product_description, border=1)
        pdf.cell(25, 10, str(quantity), border=1, align="C")
        pdf.cell(25, 10, f"${value_per_unit:.2f}", border=1, align="R")
        pdf.cell(25, 10, f"${extended_value:.2f}", border=1, align="R")
        pdf.cell(15, 10, f"{st_percent:.2f}", border=1, align="R")
        pdf.cell(25, 10, f"${st_amount:.2f}", border=1, align="R", ln=True)
    
    # Additional Information
    pdf.ln(10)
    pdf.cell(0, 5, f"Additional Information:", ln=True)
    pdf.cell(0, 5, f"Your {session.payment_intent.payment_method_types[0].capitalize()} ending in {card_last4} has been charged ${amount_paid:.2f}", ln=True)
    pdf.ln(5)
    
    # Terms and Conditions
    pdf.cell(0, 5, "Terms and Conditions", ln=True)
    pdf.cell(0, 5, "This order is subject to the terms of your purchase agreement with Apple Inc.", ln=True)
    pdf.cell(0, 5, "This is a computer-generated invoice which does not require any signature.", ln=True)
    pdf.ln(10)
    
    # Totals
    pdf.cell(0, 5, f"Total Value (Excl ST)    ${amount_paid - shipping_cost:.2f}", ln=True)
    pdf.cell(0, 5, f"Shipping                 ${shipping_cost:.2f}", ln=True)
    pdf.cell(0, 5, f"ST at {st_percent:.2f}%         ${st_amount:.2f}", align="R", ln=True)
    pdf.cell(0, 5, f"Total Value (Incl ST)    ${amount_paid:.2f}", ln=True)
    pdf.ln(5)
    pdf.cell(0, 5, "Page 1 of 1", ln=True, align="R")
    
    pdf_file = f"receipt_{transaction_id}.pdf"
    pdf.output(pdf_file)
    return pdf_file

def send_email(session):
    """Send an HTML order confirmation email."""
    customer_email = session.customer_details.email

    # Email setup
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = customer_email
    msg["Subject"] = f"We're processing your order #{session.payment_intent.id}"

    # Attach HTML content
    html_content = get_html_confirmation(session)
    msg.attach(MIMEText(html_content, "html"))

    # Send email
    try:
        with smtplib.SMTP("smtp.secureserver.net", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Order confirmation email sent successfully to {customer_email}")
    except Exception as e:
        print(f"Failed to send order confirmation email: {e}")

def send_receipt_email(session, pdf_file):
    """Send a receipt email with PDF attachment."""
    customer_email = session.customer_details.email
    customer_name = session.customer_details.name or "Customer"
    amount_paid = session.amount_total / 100
    transaction_id = session.payment_intent.id

    # Email setup
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = customer_email
    msg["Subject"] = f"Your Purchase Receipt #{transaction_id}"

    body = f"""
    Dear {customer_name},

    Thank you for your purchase! Attached is your receipt for the following transaction:

    Amount Paid: ${amount_paid:.2f}
    Order Number: {transaction_id}
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    If you have any questions, feel free to contact us.

    Best regards,
    GadgetX Africa Ltd.
    """
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF
    with open(pdf_file, "rb") as f:
        pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
        pdf_attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_file))
        msg.attach(pdf_attachment)

    # Send email
    try:
        with smtplib.SMTP("smtp.secureserver.net", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Receipt email sent successfully to {customer_email}")
    except Exception as e:
        print(f"Failed to send receipt email: {e}")

def handle_checkout_session(checkout_session_id):
    """Handle a successful purchase from a Stripe Checkout Session."""
    try:
        session = stripe.checkout.Session.retrieve(
            checkout_session_id,
            expand=['payment_intent', 'line_items', 'shipping_options', 'shipping_cost']
        )
        if session.payment_status == "paid":
            customer_name = session.customer_details.name or "Customer"
            customer_email = session.customer_details.email
            customer_phone = session.customer_details.phone or None
            amount_paid = session.amount_total / 100
            product_name = session.line_items.data[0].description
            transaction_id = session.payment_intent.id
            order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            shipping_details = session.shipping_details or {}
            billing_details = session.payment_intent.charges.data[0].billing_details

            # Store order details
            shipping_address = f"{shipping_details.get('name', customer_name)}, {shipping_details.address.line1}, " \
                              f"{shipping_details.address.line2 or ''}, {shipping_details.address.city}, " \
                              f"{shipping_details.address.state} {shipping_details.address.postal_code}, {shipping_details.address.country}"
            billing_address = f"{billing_details.name or customer_name}, {billing_details.address.line1}, " \
                             f"{billing_details.address.line2 or ''}, {billing_details.address.city}, " \
                             f"{billing_details.address.state} {billing_details.address.postal_code}, {billing_details.address.country}"
            orders.append({
                "transaction_id": transaction_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone or "N/A",
                "product_name": product_name,
                "amount_paid": amount_paid,
                "order_date": order_date,
                "shipping_address": shipping_address,
                "billing_address": billing_address
            })

            # Send HTML order confirmation email
            send_email(session)
            
            # Generate and send receipt PDF email
            pdf_file = generate_receipt_pdf(session)
            send_receipt_email(session, pdf_file)
            os.remove(pdf_file)  # Clean up PDF file

            print(f"Successfully processed order for {customer_name}: ${amount_paid}")
        else:
            print(f"Checkout session {checkout_session_id} is not paid: {session.payment_status}")
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
    except Exception as e:
        print(f"Error processing checkout session: {e}")

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Webhook endpoint for Stripe events."""
    event = None
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        print(f"Invalid payload: {e}")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Invalid signature: {e}")
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        checkout_session_id = event["data"]["object"]["id"]
        handle_checkout_session(checkout_session_id)
    
    return "Success", 200

if __name__ == "__main__":
    # Run the webhook server
    app.run(host="0.0.0.0", port=5000, debug=True)