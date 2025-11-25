import { Injectable } from '@angular/core';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import { Area } from '../../../material-planning/model/area';
import { Layer } from '../../../material-planning/model/layer';
import { MaterialUnit } from '../../../material-planning/model/material.dto';

export interface MaterialReportInput {
  imageUrl: string; // Original oder bearbeitete Bild-URL
  areas: Area[];    // Enthält Flächen, Layer & Kosten-Basis
}

@Injectable({ providedIn: 'root' })
export class MaterialPdfService {
  async buildMaterialReport(input: MaterialReportInput): Promise<Blob> {
    const { imageUrl, areas } = input;
    const pdfDoc = await PDFDocument.create();
    const pageSize: [number, number] = [595.28, 841.89]; // A4
    const margin = 42;
    const pageWidth = pageSize[0];
    const pageHeight = pageSize[1];
    const contentWidth = pageWidth - margin * 2;
    const headerHeight = 110;
    const bottomSafe = 120; // Footer Sicherheitszone
    const sectionSpacing = 24;

    let page = pdfDoc.addPage(pageSize);
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const fontBold = font;
    const primaryColor = rgb(0.07, 0.36, 0.72);
    const now = new Date();
    const dateStr = now.toLocaleDateString('de-DE') + ' ' + now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });

    const drawHeader = (pg: any, index: number) => {
      pg.drawText('Material Kalkulation (KI / Demo)', { x: margin, y: pageHeight - 60, size: 20, font: fontBold, color: primaryColor });
      pg.drawText('AD Evolution', { x: margin, y: pageHeight - 82, size: 12, font, color: rgb(0,0,0)});
      pg.drawText('innovation@ad-evolution.de  |  ad-evolution.com', { x: margin, y: pageHeight - 98, size: 10, font, color: rgb(0.2,0.2,0.2)});
      const x = pageWidth - margin - font.widthOfTextAtSize(dateStr, 10);
      pg.drawText(dateStr, { x, y: pageHeight - 82, size: 10, font, color: rgb(0.25,0.25,0.25)});
      if (index > 0) pg.drawText('Fortsetzung', { x, y: pageHeight - 98, size: 9, font, color: rgb(0.4,0.4,0.4)});
    };

    const drawFooter = (pg: any, pageIndex: number, total?: number) => {
      pg.drawRectangle({ x: 0, y: 0, width: pageWidth, height: 60, color: rgb(1,1,1)});
      const left = 'AD Evolution – Material Planung (Showcase)';
      const right = `Seite ${pageIndex + 1}${total ? ' / ' + total : ''}`;
      pg.drawText(left, { x: margin, y: 24, size: 8.5, font, color: rgb(0.25,0.25,0.25)});
      const rx = pageWidth - margin - font.widthOfTextAtSize(right, 8.5);
      pg.drawText(right, { x: rx, y: 24, size: 8.5, font, color: rgb(0.35,0.35,0.35)});
    };

    const wrap = (text: string, maxWidth: number, size: number) => {
      const words = text.split(/\s+/); let line=''; const lines: string[]=[];
      for (const w of words) {
        const cand = line ? line + ' ' + w : w;
        if (font.widthOfTextAtSize(cand, size) > maxWidth && line) { lines.push(line); line = w; } else line = cand;
      }
      if (line) lines.push(line);
      return lines;
    };

    const ensure = (need: number, currentY: number): [number, any] => {
      if (currentY - need < bottomSafe) {
        drawFooter(page, pdfDoc.getPageCount()-1);
        page = pdfDoc.addPage(pageSize);
        drawHeader(page, pdfDoc.getPageCount()-1);
        return [pageHeight - headerHeight - 12, page];
      }
      return [currentY, page];
    };

    drawHeader(page, 0);
    let y = pageHeight - headerHeight - 12;

    const title = (t: string) => {
      page.drawText(t, { x: margin, y, size: 14, font: fontBold, color: primaryColor });
      y -= 8; page.drawRectangle({ x: margin, y, width: contentWidth, height: 2, color: primaryColor});
      y -= 14;
    };

    // Intro
    title('Über diese Kalkulation');
    const intro = 'Automatisch zusammengestellte Übersicht der erfassten Flächen, zugeordneten Materialien und geschätzten Kosten. Showcase für KI-gestützte Vorplanung / Mengenermittlung.';
    for (const l of wrap(intro, contentWidth, 11)) { page.drawText(l, { x: margin, y, size: 11, font, color: rgb(0.1,0.1,0.1)}); y -= 14; }
    y -= sectionSpacing;

    // Bild (unterstützt auch data: URLs mit bereits eingezeichneten Flächen)
    title('Planungsbild');
    try {
      let rawBytes: Uint8Array;
      if (imageUrl.startsWith('data:')) {
        const comma = imageUrl.indexOf(',');
        if (comma === -1) throw new Error('Ungültige data URL');
        const base64 = imageUrl.substring(comma + 1);
        const bin = atob(base64);
        const arr = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        rawBytes = arr;
      } else {
        const buf = await fetch(imageUrl).then(r=>r.arrayBuffer());
        rawBytes = new Uint8Array(buf);
      }
      let embedded: any;
      try { embedded = await pdfDoc.embedJpg(rawBytes as any); } catch { embedded = await pdfDoc.embedPng(rawBytes as any); }
      const dims = embedded.scale(1); const maxH = 260; const scale = Math.min(contentWidth/dims.width, maxH/dims.height, 1);
      const w = dims.width * scale; const h = dims.height * scale;
      if (y - h - 40 < bottomSafe) { [y] = ensure(h + 60, y); }
      const xImg = margin + (contentWidth - w)/2;
      page.drawImage(embedded, { x: xImg, y: y - h, width: w, height: h });
      y -= h + 12;
      page.drawText('Abbildung: Aktuelle Ansicht mit markierten Flächen (Screenshot).', { x: margin, y, size: 9, font, color: rgb(0.35,0.35,0.35)});
      y -= sectionSpacing;
    } catch {
      page.drawText('(Bild konnte nicht geladen werden)', { x: margin, y: y-14, size: 10, font, color: rgb(0.6,0,0)});
      y -= 14 + sectionSpacing;
    }

    // Flächen & Layer
    title('Flächen & Schichten');
    const headerFontSize = 11;
    const normalFont = 10;
    const lineGap = 13;

    const costOfLayer = (area: Area, layer: Layer): number => {
      if (!layer.material) return 0;
      switch (layer.material.unit) {
        case MaterialUnit.EURO_PER_CUBIC_METER:
          return area.size * layer.depth * layer.material.price;
        case MaterialUnit.EURO_PER_LITER:
          return area.size * layer.depth * 1000 * layer.material.price;
        default:
          return area.size * layer.material.price; // per m2 / per kilo / per square meter fallback
      }
    };

    areas.forEach((a, idx) => {
      const areaIntro = `Fläche ${idx+1}: ${a.name} (${a.size.toFixed(2)} m²)`;
      const lines = wrap(areaIntro, contentWidth, headerFontSize);
      const layersNeeded = a.layers.reduce((acc,l)=>acc + wrap(l.name + (l.material? ` (${l.material.unit})`:'') + ` – Tiefe: ${l.depth}m – Kosten: ${costOfLayer(a,l).toFixed(2)} €`, contentWidth - 12, normalFont).length, 0);
      const need = lines.length * lineGap + layersNeeded * lineGap + 18;
      [y] = ensure(need, y);
      lines.forEach(ln => { page.drawText(ln, { x: margin, y, size: headerFontSize, font: fontBold, color: rgb(0.1,0.1,0.1)}); y -= lineGap; });
      a.layers.forEach(l => {
        const text = `${l.name}${l.material? ' – ' + l.material.name: ''}` + (l.material? ` (${l.material.unit})`: '') + ` | Tiefe: ${l.depth}m | Kosten: ${costOfLayer(a,l).toFixed(2)} €`;
        const lns = wrap(text, contentWidth - 12, normalFont);
        lns.forEach(ln => { page.drawText(ln, { x: margin + 12, y, size: normalFont, font, color: rgb(0.15,0.15,0.15)}); y -= lineGap; });
      });
      const areaSum = a.layers.reduce((s,l)=> s + costOfLayer(a,l), 0);
      page.drawText(`Summe Fläche: ${areaSum.toFixed(2)} €`, { x: margin + 12, y, size: normalFont, font: fontBold, color: primaryColor });
      y -= lineGap + 6;
    });

    // Gesamtsumme
    const total = areas.reduce((acc,a)=> acc + a.layers.reduce((s,l)=> s + costOfLayer(a,l),0),0);
    [y] = ensure(60, y);
    title('Gesamtkosten (Schätzung)');
    const totalLine = `Summe aller Flächen & Schichten: ${total.toFixed(2)} €`;
    page.drawText(totalLine, { x: margin, y, size: 13, font: fontBold, color: primaryColor });
    y -= 20;
    const hint = 'Hinweis: Werte sind Demo-Schätzungen basierend auf hinterlegten Einheitspreisen. Keine Gewähr. Anpassung & Export als Grundlage für weitere Planung möglich.';
    for (const l of wrap(hint, contentWidth, 9)) { page.drawText(l, { x: margin, y, size: 9, font, color: rgb(0.3,0.3,0.3)}); y -= 12; }

    const pages = pdfDoc.getPages();
    pages.forEach((p,i)=> drawFooter(p,i,pages.length));
    const bytes = await pdfDoc.save();
    const out = new Uint8Array(bytes); // ensure ArrayBuffer
    return new Blob([out.buffer], { type: 'application/pdf'});
  }
}
