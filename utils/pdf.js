import { FPDF } from 'fpdf';

export const generateReceiptPDF = (session) => {
  const pdf = new FPDF();
  pdf.addPage();
  pdf.setFont('Arial', 'B', 16);
  pdf.cell(40, 10, 'Receipt');
  pdf.output('receipt.pdf');
  return 'receipt.pdf';
};