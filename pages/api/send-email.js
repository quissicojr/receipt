import { sendEmail } from '../../utils/email';

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { session } = req.body;
    try {
      await sendEmail(session);
      res.status(200).json({ success: true });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  } else {
    res.setHeader('Allow', 'POST');
    res.status(405).end('Method Not Allowed');
  }
}