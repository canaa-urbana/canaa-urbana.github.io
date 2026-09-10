// Conversor genérico markdown -> DOCX com a identidade Ardósia. Reutilizado
// pelos três artigos (plano §9): lê texto.md, aplica os estilos nomeados de
// ardosia_docx.js, insere as figuras nos pontos marcados com
// `<!-- fig: caminho/relativo/figura.png | Legenda da figura -->` e escreve
// o .docx pronto para conversão a PDF via `soffice --headless --convert-to pdf`.
//
// Uso:
//   node md_to_docx.js <entrada.md> <saida.docx> [--pasta-base=/caminho]
//
// Suporta: #/##/###, parágrafos com **negrito**/*itálico*, tabelas em pipe,
// `---` como quebra de seção (filete), marcadores de figura, e trata a
// primeira linha "# Título" como TituloDoc (capa/topo) em vez de Titulo1.

const fs = require("fs");
const path = require("path");
const docx = require("docx");
const {
  Document, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  AlignmentType, WidthType, BorderStyle, ShadingType, VerticalAlign,
} = docx;

const A = require("./ardosia_docx.js");

const [, , ENTRADA, SAIDA, ...flags] = process.argv;
if (!ENTRADA || !SAIDA) {
  console.error("Uso: node md_to_docx.js <entrada.md> <saida.docx> [--pasta-base=/caminho]");
  process.exit(1);
}
const pastaBaseFlag = flags.find((f) => f.startsWith("--pasta-base="));
const PASTA_BASE = pastaBaseFlag ? pastaBaseFlag.split("=")[1] : path.dirname(ENTRADA);

const md = fs.readFileSync(ENTRADA, "utf-8");
const linhas = md.split("\n");

// --------------------------------------------------------------------
// Inline: **negrito**, *itálico* -> TextRun[]
// --------------------------------------------------------------------
function inline(texto, baseProps = {}) {
  const runs = [];
  const re = /(\*\*.+?\*\*|\*.+?\*)/g;
  let ultimo = 0;
  let m;
  while ((m = re.exec(texto)) !== null) {
    if (m.index > ultimo) runs.push(new TextRun({ text: texto.slice(ultimo, m.index), ...baseProps }));
    const tok = m[0];
    if (tok.startsWith("**")) {
      runs.push(new TextRun({ text: tok.slice(2, -2), bold: true, ...baseProps }));
    } else {
      runs.push(new TextRun({ text: tok.slice(1, -1), italics: true, ...baseProps }));
    }
    ultimo = re.lastIndex;
  }
  if (ultimo < texto.length) runs.push(new TextRun({ text: texto.slice(ultimo), ...baseProps }));
  return runs.length ? runs : [new TextRun({ text: "", ...baseProps })];
}

function celula(texto, { cabecalho = false, alinhar = "left" } = {}) {
  return new TableCell({
    children: [new Paragraph({
      style: cabecalho ? "TabelaCab" : "Tabela",
      alignment: alinhar === "right" ? AlignmentType.RIGHT : alinhar === "center" ? AlignmentType.CENTER : AlignmentType.LEFT,
      children: inline(texto.trim()),
    })],
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
  });
}

function tabelaMd(linhasTabela) {
  const cabecalho = linhasTabela[0].split("|").map((c) => c.trim()).filter((c, i, arr) => !(i === 0 && c === "") && !(i === arr.length - 1 && c === ""));
  const corpo = linhasTabela.slice(2); // pula o separador |---|---|
  const alinhamentos = linhasTabela[1].split("|").map((c) => c.trim()).filter((c) => c.length)
    .map((c) => (c.endsWith(":") && c.startsWith(":") ? "center" : c.endsWith(":") ? "right" : "left"));

  const rows = [
    new TableRow({
      tableHeader: true,
      children: cabecalho.map((c, i) => celula(c, { cabecalho: true, alinhar: alinhamentos[i] || "left" })),
    }),
  ];
  for (const linha of corpo) {
    const cels = linha.split("|").map((c) => c.trim()).filter((c, i, arr) => !(i === 0 && c === "") && !(i === arr.length - 1 && c === ""));
    if (!cels.length || cels.every((c) => c === "")) continue;
    rows.push(new TableRow({ children: cels.map((c, i) => celula(c, { alinhar: alinhamentos[i] || "left" })) }));
  }
  return new Table({
    rows,
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: A.tableHeaderBorders,
  });
}

// Lê largura/altura de um PNG direto do cabeçalho IHDR (bytes 16-23) — sem
// dependência externa. Necessário porque o ImageRun do docx-js NÃO preserva
// a proporção sozinho: se `transformation` recebe um width/height fixos que
// não batem com a proporção real do PNG, a imagem sai ESTICADA/ACHATADA no
// Word/PDF — bug já visto uma vez (mapas quadrados saíam achatados, forçados
// numa caixa 560×347 pensada para gráficos retangulares 9:6).
function dimensoesPng(buffer) {
  if (buffer.toString("ascii", 1, 4) !== "PNG") return null;
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

function figuraParagrafo(relPath, legenda) {
  const abs = path.resolve(PASTA_BASE, relPath);
  if (!fs.existsSync(abs)) {
    console.warn(`  aviso: figura não encontrada, pulando: ${abs}`);
    return [];
  }
  const buffer = fs.readFileSync(abs);
  // largura útil da página A4 com as margens de ardosia_docx.js (~17cm) —
  // altura máxima para não estourar a página em figuras muito "altas".
  const LARGURA_MAX_PX = 560;
  const ALTURA_MAX_PX = 620;
  const dim = dimensoesPng(buffer);
  let larguraFinal = LARGURA_MAX_PX;
  let alturaFinal = LARGURA_MAX_PX * 0.62; // fallback só se não conseguir ler o PNG
  if (dim && dim.width > 0 && dim.height > 0) {
    const razao = dim.height / dim.width;
    larguraFinal = LARGURA_MAX_PX;
    alturaFinal = larguraFinal * razao;
    if (alturaFinal > ALTURA_MAX_PX) {
      alturaFinal = ALTURA_MAX_PX;
      larguraFinal = alturaFinal / razao;
    }
  } else {
    console.warn(`  aviso: não foi possível ler as dimensões de ${relPath} (não é PNG?) — usando proporção padrão`);
  }
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 40 },
      children: [new ImageRun({ data: buffer, type: "png", transformation: { width: larguraFinal, height: alturaFinal } })],
    }),
    new Paragraph({ style: "Legenda", alignment: AlignmentType.CENTER, children: inline(legenda || "") }),
  ];
}

// --------------------------------------------------------------------
// Parser principal
// --------------------------------------------------------------------
const children = [];
let i = 0;
let primeiroH1 = true;
let tituloDoc = null; // capturado do primeiro "# " do markdown, usado no rodapé (nunca hardcoded)

while (i < linhas.length) {
  const linha = linhas[i];

  if (linha.trim() === "" ) { i++; continue; }
  if (linha.trim() === "---") { i++; continue; } // filetes de separação viram espaço em branco implícito

  // figura: <!-- fig: caminho | legenda -->
  const mFig = linha.match(/^<!--\s*fig:\s*(.+?)\s*\|\s*(.+?)\s*-->$/);
  if (mFig) {
    children.push(...figuraParagrafo(mFig[1], mFig[2]));
    i++; continue;
  }

  // tabela markdown: linha com | seguida de linha separadora ---|---
  if (linha.includes("|") && linhas[i + 1] && /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$/.test(linhas[i + 1])) {
    const bloco = [linha, linhas[i + 1]];
    let j = i + 2;
    while (j < linhas.length && linhas[j].includes("|") && linhas[j].trim() !== "") {
      bloco.push(linhas[j]);
      j++;
    }
    children.push(tabelaMd(bloco));
    children.push(new Paragraph({ text: "", spacing: { after: 120 } }));
    i = j; continue;
  }

  if (linha.startsWith("# ")) {
    const texto = linha.slice(2).trim();
    if (tituloDoc === null) tituloDoc = texto; // só o primeiro H1 vira o título do rodapé
    children.push(new Paragraph({ style: primeiroH1 ? "TituloDoc" : "Titulo1", pageBreakBefore: false, children: inline(texto) }));
    primeiroH1 = false;
    i++; continue;
  }
  if (linha.startsWith("## ")) {
    children.push(new Paragraph({ style: "Titulo1", children: inline(linha.slice(3).trim()) }));
    i++; continue;
  }
  if (linha.startsWith("### ")) {
    children.push(new Paragraph({ style: "Titulo2", children: inline(linha.slice(4).trim()) }));
    i++; continue;
  }

  if (linha.startsWith("**") && linha.trim().endsWith("**") && linha.trim().length < 60 && linha.trim().split(" ").length <= 4) {
    // heurística: linha curta toda em negrito isolada = kicker/etiqueta (ex.: **[NOME DO AUTOR]**)
    children.push(new Paragraph({ style: "Destaque", children: inline(linha.trim()) }));
    i++; continue;
  }

  // parágrafo comum: acumula linhas até uma em branco/estrutural
  let bloco = [linha];
  let j = i + 1;
  while (j < linhas.length && linhas[j].trim() !== "" && !linhas[j].startsWith("#") && linhas[j].trim() !== "---" && !linhas[j].match(/^<!--\s*fig:/)) {
    bloco.push(linhas[j]);
    j++;
  }
  const textoBloco = bloco.join(" ").replace(/\s+/g, " ").trim();
  if (textoBloco) {
    children.push(new Paragraph({ style: "Corpo", children: inline(textoBloco) }));
  }
  i = j;
}

const doc = new Document({
  styles: A.styles,
  sections: [{
    properties: A.pageProps,
    headers: A.headers(docx, path.basename(SAIDA, ".docx")),
    // ATENÇÃO: era hardcoded ao título de um artigo de outro projeto
    // ("Migração e desigualdade inter-regional no Brasil, 2000-2022") --
    // bug pré-existente herdado do projeto irmão, achado nesta sessão.
    // Agora deriva do primeiro "# " do próprio markdown, nunca fixo.
    footers: A.footers(docx, tituloDoc || path.basename(SAIDA, ".docx")),
    children,
  }],
});

docx.Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(SAIDA, buffer);
  console.log(`Gravado ${SAIDA} (${children.length} blocos)`);
});
