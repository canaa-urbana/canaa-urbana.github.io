# Checklist de publicação

Checklist para o **titular do acesso aos microdados** (Daniel Pessini Sobreira) assinar (marcar e
datar) antes do **primeiro push** para o repositório público e a cada **atualização de dados**.
Modelo: `atlas-migração/docs/CHECKLIST_PUBLICACAO.md`. Ver `CLAUDE.md` e `docs/METODOLOGIA.md`
(seção "Conformidade com a política de acesso controlado do IBGE").

Marcar um item como concluído é uma declaração do titular. As notas "Verificado pela sessão"
registram o que a sessão do Claude Code conferiu por conta própria; itens que dependem de
documento ou decisão que só o titular possui continuam abertos até ele marcar.

## Antes do primeiro push (o repositório se torna público)

- [x] **Finalidade declarada ao IBGE cobre divulgação pública de agregados.** O Termo de
      Compromisso de Confidencialidade e Responsabilidade dos microdados da amostra do Censo 2022
      (finalidade "pesquisa acadêmica", área "migrações") trata do **arquivo de microdados**, nunca
      publicado por este projeto; é omisso sobre divulgação em site público, dataset sob licença
      aberta e depósito com DOI — não veda, mas não autoriza explicitamente. A consulta ao IBGE
      sobre a divulgação de agregados (registrada no plano) segue **pendente de resposta**; o mesmo
      ponto está aberto no atlas-migração. Decisão do titular antes do push: publicar com base na
      finalidade acadêmica e no controle de revelação, ou aguardar a resposta.
      **Decisão do titular em 2026-09-10:** publicar com base na finalidade acadêmica e no controle
      de revelação (gate R1–R8), sem aguardar a resposta do IBGE.
- [x] **Termos arquivados fora do repositório.** Cópias do Termo e da concessão guardadas
      localmente (nunca commitadas; `docs/termos/` está no `.gitignore`).
      **Declarado pelo titular em 2026-09-10.**
- [x] **Gate de revelação aprovado e relatório arquivado.**
      **Verificado pela sessão em 2026-09-10:** `disclosure_check.py --versao 2026-09-10-e8` —
      "GATE APROVADO" (R1–R8, 20.458 células recontadas, 5.951 rurais implícitas), carimbo com
      259 arquivos; `docs/relatorio_revelacao_2026-09-10-e8.md` gerado.
- [x] **`verify_gate.py` verde** (também em `--clone`, como no CI).
- [x] **Auditoria de dados pessoais e sigilo verde.** `pipeline/auditoria_publicacao.py` sobre o
      conteúdo decodificado de todos os arquivos versionados (texto, parquet, DOCX, PDF, imagens):
      nenhum e-mail pessoal, CPF, telefone, caminho local, URL assinada, chave ou arquivo de
      microdados. **Verificado pela sessão em 2026-09-10**, depois de: remover 4 e-mails de terceiros
      dos resumos de `bibliografia/candidatos.parquet` (e incluir a remoção no `30_bibliografia.py`);
      tirar da documentação o nº de protocolo da consulta ao IBGE, a localização do termo e os
      caminhos do disco local; trocar o nome da pasta de entrega dos microdados de 2022 (com data e
      hora da entrega) por busca por padrão no código; redigir tamanhos amostrais e arredondar a 10
      os totais ponderados não oficiais do QA da E2; deixar `PLANO.docx`/`PLANO.pdf` fora do
      repositório. Metadados do DOCX e do PDF sem nome de usuário ("Un-named").
- [x] **`gitleaks` verde no histórico completo** (`gitleaks git --redact`; a exceção em
      `.gitleaks.toml` cobre só os SHA-256 do gate e do manifesto do painel, restrita por caminho).
- [x] **Nenhum arquivo de `data/raw`/`data/interim`/CSV no histórico do git** (o CI repete a
      checagem a cada push).
- [x] **E-mail no-reply nos commits.** Autor e committer:
      `Damnielps <129672935+Damnielps@users.noreply.github.com>` (configurado só neste repositório).
- [x] **Licenças no lugar.** `LICENSE` (MIT, código), `LICENSE-DADOS.md` (CC BY 4.0 + exceções de
      terceiros), `CITATION.cff`, `.zenodo.json` — escolhas confirmadas pelo titular em 2026-09-10.
- [x] **Atribuição de fontes** no rodapé do painel, na aba Metodologia (camadas com atribuição e
      licença) e nas figuras do artigo.
- [x] **Organização e repositório criados pelo titular** (2026-09-10): organização `canaa-urbana` e repositório
      `canaa-urbana/canaa-urbana.github.io`. Recomendação: criar **privado**, fazer o primeiro push,
      conferir o job `verificar` do CI verde e só então tornar público e ativar o Pages
      (Settings → Pages → Source: GitHub Actions).

## Depois do primeiro deploy

- [x] Site respondendo em `https://canaa-urbana.github.io` com HTTPS.
      **Verificado pela sessão em 2026-09-10:** workflow `Publicar` verde (verificar, construir,
      publicar); página inicial, `robots.txt`, `sitemap.xml`, manifesto do painel e
      `artigo/artigo.pdf` com HTTP 200; mapa da aba Mancha urbana renderizado, console sem erros.
- [x] Descrição, `homepage` e tópicos do repositório (engrenagem "About") — preenchidos pelo
      titular em 2026-09-10 (conferido na API do GitHub).
- [x] **DOI no Zenodo** (2026-09-10): release `v1.0.0` arquivada; DOI conceitual
      **10.5281/zenodo.22699960**, DOI da versão 10.5281/zenodo.22699961 (registro de software,
      CC BY 4.0, autoria e ORCID conferidos na API do Zenodo). Propagado ao `CITATION.cff`
      (versão `1.0.0`), `README.md` (selo e "Como citar"), `web/src/lib/publicacao.ts`,
      JSON-LD do `web/index.html` e ao artigo; `.zenodo.json` sem DOI (o Zenodo o atribui).
      Procedimento original: conectar o repositório em zenodo.org (Account → GitHub → ativar
      `canaa-urbana/canaa-urbana.github.io`) **antes** de criar a release `v1.0.0`; o Zenodo
      arquiva a release e gera o DOI conceitual e o da versão. Depois, propagar o DOI a:
      `CITATION.cff` (`identifiers` e `preferred-citation.doi`), `README.md`, `.zenodo.json` (se
      quiser o DOI no próprio registro), `web/src/lib/publicacao.ts` (`DOI`) e à seção
      "Disponibilidade de dados e código" do artigo (`artigo/texto.md` → `pipeline/50_artigo.py`),
      e rodar de novo `pipeline/60_dados_web.py` e o build.
- [x] **Release `v1.0.1`** (2026-09-11): versão de apresentação, dados inalterados
      (`2026-09-10-e8`). Título da obra passa a "cidade mineradora"; pirâmides etárias do painel
      alinhadas como na figura 7; fundo de figura `#FAFAF9`; tooltips dos mapas consolidados em
      `app.css` e tooltip de volume no mapa de fluxos. DOI da versão
      **10.5281/zenodo.22709148** (conceitual inalterado), propagado a `CITATION.cff` e
      `README.md`. O artigo passou a citar só o DOI conceitual, para não precisar ser regerado a
      cada release.
- [ ] Google Search Console / Bing Webmaster (opcional): verificar a propriedade e enviar
      `sitemap.xml`.

## Procedimento de atualização de dados (a cada nova versão)

1. Rodar as etapas afetadas do pipeline na máquina com acesso aos microdados.
2. `python pipeline/disclosure_check.py --versao <AAAA-MM-DD-xx>` → "GATE APROVADO".
3. `python pipeline/60_dados_web.py` (verifica o carimbo e reexporta o painel).
4. `python pipeline/validate.py --e7` e `python pipeline/auditoria_publicacao.py`.
5. Commit (o hook `.githooks/pre-commit` roda o gate e a auditoria) e push para `main` — o
   workflow `publicar.yml` verifica, constrói e publica.
6. Atualizar `version` em `CITATION.cff` e `VERSAO` em `web/src/lib/publicacao.ts`; criar nova
   release para nova versão com DOI.

---

Assinatura do titular do acesso: **Daniel Pessini Sobreira** — data: 10/09/2026
