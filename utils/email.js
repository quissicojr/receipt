import smtplib from 'smtplib';
import { MIMEMultipart, MIMEText } from 'email.mime';

const SENDER_EMAIL = process.env.SENDER_EMAIL;
const EMAIL_PASSWORD = process.env.EMAIL_PASSWORD;

export const sendEmail = async (session) => {
  const customerEmail = session.customer_details.email;
  const msg = MIMEMultipart();
  msg['From'] = SENDER_EMAIL;
  msg['To'] = customerEmail;
  msg['Subject'] = `We're processing your order #${session.payment_intent.id}`;

  const htmlContent = getHtmlConfirmation(session);
  msg.attach(MIMEText(htmlContent, 'html'));

  try {
    const server = smtplib.SMTP('smtp.secureserver.net', 587);
    server.starttls();
    server.login(SENDER_EMAIL, EMAIL_PASSWORD);
    server.sendMessage(msg);
    server.quit();
    console.log(`Email sent to ${customerEmail}`);
  } catch (error) {
    console.error(`Failed to send email: ${error}`);
  }
};