import stripe from 'stripe';
import { sendEmail } from './email';
import { generateReceiptPDF } from './pdf';

const stripeClient = stripe(process.env.STRIPE_API_KEY);

export const handleCheckoutSession = async (session) => {
  if (session.payment_status === 'paid') {
    await sendEmail(session);
    const pdfFile = await generateReceiptPDF(session);
    console.log(`Order processed for ${session.customer_details.email}`);
  }
};