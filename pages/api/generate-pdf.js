import { generateReceiptPDF } from '../../utils/pdf';

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { session } = req.body;
    try {
      const pdfFile = await generateReceiptPDF(session);
      res.status(200).json({ pdfFile });
    } catch (error) {
      res.status(500).json({ error: error.message });
    }
  } else {
    res.setHeader('Allow', 'POST');
    res.status(405).end('Method Not Allowed');
  }
}