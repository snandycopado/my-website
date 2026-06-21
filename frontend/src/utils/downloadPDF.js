import { jsPDF } from 'jspdf';

export function downloadQuestionPaper(questions, title) {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 20;
  const maxWidth = pageWidth - margin * 2;
  let y = 20;

  const checkPageBreak = (needed) => {
    if (y + needed > 270) {
      doc.addPage();
      y = 20;
    }
  };

  // Title
  doc.setFontSize(18);
  doc.setFont('helvetica', 'bold');
  doc.text(title, pageWidth / 2, y, { align: 'center' });
  y += 10;

  // Date
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(`Date: ${new Date().toLocaleDateString()}`, pageWidth / 2, y, { align: 'center' });
  y += 5;

  // Instructions
  doc.setFontSize(10);
  doc.text('Total Questions: 10 | Choose the correct option (A, B, C, or D)', pageWidth / 2, y, { align: 'center' });
  y += 5;

  // Line
  doc.setDrawColor(100);
  doc.line(margin, y, pageWidth - margin, y);
  y += 8;

  // Name field
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  doc.text('Student Name: ___________________________    Class: _________    Roll No: _________', margin, y);
  y += 12;

  // Questions
  questions.forEach((q, idx) => {
    checkPageBreak(45);

    // Question
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    const qLines = doc.splitTextToSize(`Q${idx + 1}. ${q.question}`, maxWidth);
    doc.text(qLines, margin, y);
    y += qLines.length * 6 + 3;

    // Options in 2x2 grid
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    const letters = ['A', 'B', 'C', 'D'];
    const colWidth = maxWidth / 2;

    for (let i = 0; i < 4; i += 2) {
      checkPageBreak(8);
      const optA = `(${letters[i]})  ${q.options[i]}`;
      const optB = i + 1 < 4 ? `(${letters[i + 1]})  ${q.options[i + 1]}` : '';
      doc.text(doc.splitTextToSize(optA, colWidth - 5), margin + 5, y);
      if (optB) doc.text(doc.splitTextToSize(optB, colWidth - 5), margin + colWidth, y);
      y += 7;
    }

    // Answer box
    checkPageBreak(10);
    doc.setFontSize(10);
    doc.text(`Answer: [    ]`, margin + 5, y);
    y += 10;
  });

  // Footer
  checkPageBreak(20);
  y += 5;
  doc.setDrawColor(100);
  doc.line(margin, y, pageWidth - margin, y);
  y += 8;
  doc.setFontSize(10);
  doc.setFont('helvetica', 'italic');
  doc.text('*** End of Question Paper ***', pageWidth / 2, y, { align: 'center' });

  const filename = title.replace(/[^a-zA-Z0-9]/g, '_') + '.pdf';
  doc.save(filename);
}
