# -*- coding: utf-8 -*-
"""Gera a documentacao do trabalho em PDF."""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, KeepTogether,
                                NextPageTemplate)
from reportlab.graphics.shapes import Drawing, Rect, String, Line

# ----------------------------------------------------------------- nome
# Escreva seu nome aqui e rode:  py scripts\gerar_pdf.py
AUTOR = "Kayruan da Cruz Soares"

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(_RAIZ, "docs", "Documentacao_Trabalho.pdf")

# --------------------------------------------------------------- paleta
AZUL     = colors.HexColor("#1F3A5F")
TEAL     = colors.HexColor("#2A9D8F")
LARANJA  = colors.HexColor("#E07A3F")
CINZA    = colors.HexColor("#5A6472")
CINZA_CL = colors.HexColor("#EDEFF2")
CODIGO_B = colors.HexColor("#F5F6F8")
BORDA    = colors.HexColor("#D5D9E0")

# --------------------------------------------------------------- fontes
def reg(nome, arquivo):
    caminho = os.path.join(r"C:\Windows\Fonts", arquivo)
    if os.path.exists(caminho):
        pdfmetrics.registerFont(TTFont(nome, caminho))
        return True
    return False

TEM_TTF = all([
    reg("Corpo",   "calibri.ttf"),  reg("Corpo-B",  "calibrib.ttf"),
    reg("Corpo-I", "calibrii.ttf"), reg("Mono",     "consola.ttf"),
    reg("Mono-B",  "consolab.ttf"),
])

if TEM_TTF:
    pdfmetrics.registerFontFamily("Corpo", normal="Corpo", bold="Corpo-B",
                                  italic="Corpo-I", boldItalic="Corpo-B")
    F, FB, FI, M, MB = "Corpo", "Corpo-B", "Corpo-I", "Mono", "Mono-B"
else:
    F, FB, FI, M, MB = ("Helvetica", "Helvetica-Bold", "Helvetica-Oblique",
                        "Courier", "Courier-Bold")

# --------------------------------------------------------------- estilos
def st(nome, **kw):
    base = dict(name=nome, fontName=F, fontSize=10.5, leading=15.5,
                textColor=colors.HexColor("#22262B"))
    base.update(kw)
    return ParagraphStyle(**base)

S = {
    "corpo":    st("corpo", alignment=TA_JUSTIFY, spaceAfter=7),
    "h1":       st("h1", fontName=FB, fontSize=17, leading=21, textColor=AZUL,
                   spaceBefore=16, spaceAfter=10, keepWithNext=1),
    "h2":       st("h2", fontName=FB, fontSize=12.5, leading=16, textColor=AZUL,
                   spaceBefore=13, spaceAfter=5, keepWithNext=1),
    "h3":       st("h3", fontName=FB, fontSize=11, leading=14.5,
                   textColor=TEAL, spaceBefore=10, spaceAfter=4, keepWithNext=1),
    "cod":      st("cod", fontName=M, fontSize=8.4, leading=11.6,
                   textColor=colors.HexColor("#1B1F24")),
    "cod_leg":  st("cod_leg", fontSize=8.6, leading=11.5, textColor=CINZA,
                   fontName=FI, spaceBefore=3),
    "tab":      st("tab", fontSize=9.2, leading=12.6),
    "tab_cod":  st("tab_cod", fontName=M, fontSize=8.2, leading=11.4),
    "tab_cab":  st("tab_cab", fontName=FB, fontSize=9.2, leading=12.6,
                   textColor=colors.white),
    "nota":     st("nota", fontSize=9.4, leading=13.4, textColor=CINZA),
    "capa_tit": st("capa_tit", fontName=FB, fontSize=27, leading=33,
                   textColor=AZUL, alignment=TA_CENTER),
    "capa_sub": st("capa_sub", fontSize=13.5, leading=19, textColor=CINZA,
                   alignment=TA_CENTER),
    "capa_txt": st("capa_txt", fontSize=11.5, leading=17, alignment=TA_CENTER),
}

def P(txt, estilo="corpo"):
    return Paragraph(txt, S[estilo])

# ------------------------------------------------------- blocos de codigo
def codigo(linhas, legenda=None):
    """Bloco de codigo com fundo e barra lateral."""
    txt = "<br/>".join(
        l.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
         .replace(" ", "&nbsp;") or "&nbsp;"
        for l in linhas.strip("\n").split("\n"))
    t = Table([[Paragraph(txt, S["cod"])]], colWidths=[16.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CODIGO_B),
        ("BOX",           (0, 0), (-1, -1), 0.6, BORDA),
        ("LINEBEFORE",    (0, 0), (0, -1), 2.4, TEAL),
        ("LEFTPADDING",   (0, 0), (-1, -1), 9),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    itens = [t]
    if legenda:
        itens.append(P(legenda, "cod_leg"))
    itens.append(Spacer(1, 7))
    return KeepTogether(itens)

def tabela(cabecalho, linhas, larguras, mono_cols=()):
    dados = [[Paragraph(c, S["tab_cab"]) for c in cabecalho]]
    for ln in linhas:
        dados.append([
            Paragraph(c, S["tab_cod"] if i in mono_cols else S["tab"])
            for i, c in enumerate(ln)])
    t = Table(dados, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND",    (0, 0), (-1, 0), AZUL),
        ("GRID",          (0, 0), (-1, -1), 0.5, BORDA),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(dados)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), CINZA_CL))
    t.setStyle(TableStyle(estilo))
    return t

# ------------------------------------------------------ diagrama temporal
def diagrama_linha_tempo():
    L, A = 16.4 * cm, 5.95 * cm
    d = Drawing(L, A)
    x0, x1 = 2.6 * cm, L - 0.4 * cm
    tmax = 10.0
    def px(t):
        return x0 + (x1 - x0) * (t / tmax)

    topo, alt, gap = A - 0.75 * cm, 0.52 * cm, 0.26 * cm

    for i in range(5):
        y = topo - i * (alt + gap) - alt
        ini = i * 2.0
        d.add(String(0.1 * cm, y + 0.14 * cm, "Cliente %d" % (i + 1),
                     fontName=F, fontSize=8.6,
                     fillColor=colors.HexColor("#22262B")))
        if ini > 0:   # faixa de espera no semaforo
            d.add(Rect(px(0), y, px(ini) - px(0), alt,
                       fillColor=CINZA_CL, strokeColor=BORDA, strokeWidth=0.4))
            d.add(String((px(0) + px(ini)) / 2, y + 0.16 * cm,
                         "esperando", fontName=F, fontSize=7.4,
                         fillColor=CINZA, textAnchor="middle"))
        # faixa de atendimento (segurando o semaforo)
        d.add(Rect(px(ini), y, px(ini + 2) - px(ini), alt,
                   fillColor=TEAL, strokeColor=colors.HexColor("#1F7A6F"),
                   strokeWidth=0.4))
        d.add(String((px(ini) + px(ini + 2)) / 2, y + 0.16 * cm,
                     "atendido + lock 2 s", fontName=F, fontSize=7.4,
                     fillColor=colors.white, textAnchor="middle"))

    # eixo do tempo
    ye = topo - 5 * (alt + gap) - 0.34 * cm
    d.add(Line(px(0), ye, px(tmax), ye, strokeColor=CINZA, strokeWidth=0.7))
    for t in range(0, 11, 2):
        d.add(Line(px(t), ye, px(t), ye - 0.12 * cm,
                   strokeColor=CINZA, strokeWidth=0.7))
        d.add(String(px(t), ye - 0.46 * cm, "%d s" % t, fontName=F,
                     fontSize=7.6, fillColor=CINZA, textAnchor="middle"))
    return d

# ------------------------------------------------ cabecalho / rodape
def moldura(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setFont(F, 8)
        canvas.setFillColor(CINZA)
        canvas.drawString(2 * cm, A4[1] - 1.25 * cm,
                          "Semaforo rudimentar sobre sockets TCP")
        canvas.setStrokeColor(BORDA)
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, A4[1] - 1.45 * cm, A4[0] - 2 * cm, A4[1] - 1.45 * cm)
        canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
        canvas.drawRightString(A4[0] - 2 * cm, 1.05 * cm, str(doc.page))
        canvas.drawString(2 * cm, 1.05 * cm,
                          "Sistemas Distribuidos - Comunicacao e Concorrencia")
    canvas.restoreState()

def capa_fundo(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(AZUL)
    canvas.rect(0, A4[1] - 4.2 * cm, A4[0], 4.2 * cm, stroke=0, fill=1)
    canvas.setFillColor(TEAL)
    canvas.rect(0, A4[1] - 4.45 * cm, A4[0], 0.25 * cm, stroke=0, fill=1)
    canvas.setFillColor(AZUL)
    canvas.rect(0, 0, A4[0], 1.1 * cm, stroke=0, fill=1)
    canvas.restoreState()

# ----------------------------------------------------------- conteudo
def construir():
    h = []

    # ---------------------------------------------------------- CAPA
    h.append(Spacer(1, 5.2 * cm))
    h.append(P("Semáforo rudimentar<br/>sobre sockets TCP", "capa_tit"))
    h.append(Spacer(1, 0.5 * cm))
    h.append(P("Controle de acesso concorrente a um recurso distribuído",
               "capa_sub"))
    h.append(Spacer(1, 2.6 * cm))

    cap = Table([
        [Paragraph("<b>Disciplina</b>", S["tab"]),
         Paragraph("Sistemas Distribuídos — Comunicação e Concorrência", S["tab"])],
        [Paragraph("<b>Trabalho</b>", S["tab"]),
         Paragraph("Implementação de um semáforo rudimentar para controlar "
                   "o acesso a recursos distribuídos de forma concorrente", S["tab"])],
        [Paragraph("<b>Aluno</b>", S["tab"]), Paragraph(AUTOR, S["tab"])],
        [Paragraph("<b>Linguagem</b>", S["tab"]),
         Paragraph("C (sockets TCP, threads e semáforos)", S["tab"])],
        [Paragraph("<b>Plataformas</b>", S["tab"]),
         Paragraph("Windows (Winsock2) e Linux (BSD sockets + pthreads)", S["tab"])],
    ], colWidths=[3.4 * cm, 12.2 * cm])
    cap.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    h.append(cap)
    h.append(NextPageTemplate("miolo"))
    h.append(PageBreak())

    # ------------------------------------------------------ 1. OBJETIVO
    h.append(P("1. Objetivo", "h1"))
    h.append(P(
        "Implementar um semáforo rudimentar para controlar o acesso a um "
        "recurso distribuído de forma concorrente. Em termos práticos: "
        "<b>N clientes</b> se conectam simultaneamente a um servidor e "
        "solicitam a hora local dele. O servidor atende um cliente por vez "
        "e, após cada atendimento, mantém o recurso bloqueado por "
        "<b>2 segundos</b> — de modo que o 2º cliente só seja atendido "
        "dois segundos após o 1º, o 3º dois segundos após o 2º, e assim "
        "sucessivamente."))
    h.append(P(
        "O ponto central é que os clientes chegam <i>ao mesmo tempo</i>, mas "
        "são servidos <i>em fila</i>. Quem impõe essa ordem é o semáforo."))

    h.append(P("1.1 O que é o \"recurso\"", "h2"))
    h.append(P(
        "O recurso protegido é o relógio do servidor — a leitura da hora "
        "local que será devolvida ao cliente. Não é um recurso caro de "
        "verdade; ele cumpre, no trabalho, o papel de qualquer seção crítica "
        "que não possa ser acessada por dois processos ao mesmo tempo."))

    h.append(P("1.2 Comportamento esperado", "h2"))
    h.append(Spacer(1, 3))
    h.append(diagrama_linha_tempo())
    h.append(P(
        "Cinco clientes disparados simultaneamente. As faixas cinzas são a "
        "espera no semáforo; as faixas verdes, o atendimento somado aos "
        "2 s em que o recurso segue bloqueado.", "nota"))

    # --------------------------------------------------- 2. ESTRUTURA
    h.append(P("2. Estrutura do projeto", "h1"))
    h.append(codigo("""
Trabalho CP/
|-- src/
|   |-- servidor.c          servidor multithread com semaforo
|   |-- cliente.c           cliente de tempo
|-- scripts/
|   |-- compilar.ps1        compila src/ -> bin/ (Windows)
|   |-- rodar_demo.ps1      sobe o servidor e dispara N clientes
|   |-- gerar_pdf.py        gera esta documentacao
|-- docs/
|   |-- Documentacao_Trabalho.pdf   esta documentacao
|   |-- Trabalho.md                 enunciado do trabalho
|-- bin/                    binarios gerados pela compilacao
|-- Makefile                build e demo no Linux/WSL
|-- LEIAME.md               documentacao resumida
"""))
    h.append(P(
        "Apenas dois arquivos-fonte. O servidor tem cerca de 330 linhas e o "
        "cliente, 200 — ambos comentados. Cada um compila de forma "
        "independente nas duas plataformas, sem biblioteca externa alguma."))

    # -------------------------------------------------- 3. COMO USAR
    h.append(P("3. Como compilar e executar", "h1"))
    h.append(P(
        "O projeto compila em Windows e em Linux a partir do "
        "<b>mesmo código-fonte</b>, sem alteração manual nenhuma. A "
        "seleção da API acontece em tempo de compilação, por diretivas "
        "<font face=\"%s\">#ifdef _WIN32</font>." % M))

    h.append(P("3.1 Windows", "h2"))
    h.append(codigo("""
.\\scripts\\compilar.ps1          # gera bin\\servidor.exe e bin\\cliente.exe
.\\scripts\\rodar_demo.ps1 -N 5   # sobe o servidor e dispara 5 clientes
""", "No VS Code: Ctrl+Shift+B compila; a tarefa \"Rodar demo (5 clientes)\" "
     "executa a demonstração completa."))
    h.append(P("Para rodar manualmente, em duas janelas separadas:", "corpo"))
    h.append(codigo("""
# janela 1 -- servidor
.\\bin\\servidor.exe

# janela 2 -- cinco clientes ao mesmo tempo
1..5 | ForEach-Object { Start-Process -NoNewWindow .\\bin\\cliente.exe -ArgumentList $_ }
"""))

    h.append(P("3.2 Linux / WSL", "h2"))
    h.append(codigo("""
make                 # compila para bin/
make servidor        # roda o servidor (em um terminal)
make demo N=5        # dispara 5 clientes  (em outro terminal)
make clean           # remove bin/
"""))

    h.append(P("3.3 Argumentos do cliente", "h2"))
    h.append(P(
        "O cliente aceita três argumentos opcionais, úteis para testar "
        "entre máquinas diferentes:", "corpo"))
    h.append(codigo("""
cliente [rotulo] [host] [porta]

cliente 3                      # rotulo "3", conecta em 127.0.0.1:6090
cliente A 192.168.0.10 6090    # conecta em outra maquina da rede
""", "Sem argumentos, assume rótulo \"1\" e o servidor em 127.0.0.1:6090."))

    # ------------------------------------------------ 4. COMO FUNCIONA
    h.append(P("4. Como funciona", "h1"))

    h.append(P("4.1 Visão geral", "h2"))
    h.append(P(
        "O servidor é <b>concorrente</b>: o laço principal aceita conexões "
        "sem nunca bloquear e entrega cada uma a uma thread dedicada. Toda a "
        "serialização fica por conta do semáforo, dentro da thread."))
    h.append(codigo("""
thread principal                    thread de atendimento (uma por cliente)
----------------                    ----------------------------------------
accept()  ..... conexao 1 ------->  sem_descer()   <-- bloqueia aqui
accept()  ..... conexao 2 ------->  sem_descer()       se o recurso
accept()  ..... conexao 3 ------->  sem_descer()       estiver ocupado
accept()  ..... conexao 4 ------->  sem_descer()
   (nunca espera 2 s)                  |
                                       +--> le a hora, responde ao cliente
                                       +--> sleep 2 s  (recurso retido)
                                       +--> sem_subir()  libera o proximo
"""))

    h.append(P("4.2 O semáforo", "h2"))
    h.append(P(
        "O semáforo é criado com valor inicial <b>1</b>: exatamente um "
        "atendimento por vez. A região crítica fica na função "
        "<font face=\"%s\">atende_cliente()</font>, em "
        "<font face=\"%s\">src/servidor.c</font>:" % (M, M)))
    h.append(codigo("""
/* ===================== REGIAO CRITICA ===================== */
sem_descer(&recurso);            /* P()  -- so uma thread passa     */

    ... le o relogio local e responde ao cliente ...

/* O cliente ja foi atendido, mas o recurso segue retido por 2 s.
   So entao o proximo passa pelo sem_descer. */
sleep_ms(TEMPO_LOCK_MS);         /* 2000 ms                         */

sem_subir(&recurso);             /* V()  -- libera o proximo        */
/* =================== FIM DA REGIAO CRITICA ================= */
"""))
    h.append(P(
        "A chamada de <font face=\"%s\">sleep</font> fica <b>dentro</b> da "
        "região crítica, antes do <font face=\"%s\">sem_subir()</font>. É "
        "isso que produz o espaçamento de 2 em 2 segundos: não é o "
        "atendimento que demora, é o recurso que permanece bloqueado." % (M, M)))

    h.append(P("4.3 Por que threads, e não um laço accept() sequencial?", "h2"))
    h.append(P(
        "Um servidor iterativo — como o do material da disciplina — também "
        "atenderia um cliente por vez. Mas essa serialização seria um "
        "<i>acidente da arquitetura</i>: não haveria semáforo nenhum, e o "
        "trabalho pede justamente um semáforo."))
    h.append(P(
        "Com uma thread por conexão existe concorrência real: as cinco "
        "threads tentam entrar na região crítica ao mesmo tempo. A exclusão "
        "mútua passa a ser, de fato, responsabilidade do semáforo — que é o "
        "objeto de estudo. O material cobre esse modelo no slide "
        "<i>\"Sockets Multithread\"</i>."))

    h.append(P("4.4 Implementação do semáforo nas duas plataformas", "h2"))
    h.append(tabela(
        ["Operação", "Windows (Win32)", "Linux (POSIX)"],
        [["Criar (valor 1)", "CreateSemaphore", "sem_init"],
         ["Descer — P() / wait", "WaitForSingleObject", "sem_wait"],
         ["Subir — V() / post", "ReleaseSemaphore", "sem_post"],
         ["Criar thread", "CreateThread", "pthread_create"],
         ["Pausa de 2 s", "Sleep(2000)", "usleep(2000000)"]],
        [4.6 * cm, 5.9 * cm, 5.9 * cm], mono_cols=(1, 2)))
    h.append(Spacer(1, 6))
    h.append(P(
        "Os dois conjuntos ficam atrás das mesmas três funções "
        "(<font face=\"%s\">sem_criar</font>, "
        "<font face=\"%s\">sem_descer</font>, "
        "<font face=\"%s\">sem_subir</font>), de modo que o restante do "
        "código não sabe em qual sistema está rodando." % (M, M, M), "nota"))

    # ----------------------------------------------- 5. PROTOCOLO
    h.append(P("5. Protocolo de comunicação", "h1"))
    h.append(P(
        "Cliente e servidor trocam <b>8 bytes</b> em cada sentido: segundos "
        "e microssegundos desde 1º de janeiro de 1970, ambos em "
        "<i>network byte order</i> (big-endian), conforme a seção "
        "\"Ordenação de Bytes\" do material."))
    h.append(codigo("""
struct wire_time {
    uint32_t sec;    /* segundos desde 01/01/1970        */
    uint32_t usec;   /* microssegundos dentro do segundo */
};
"""))
    h.append(P(
        "O código original enviava a <font face=\"%s\">struct timeval</font> "
        "diretamente, aplicando <font face=\"%s\">htonl()</font> sobre "
        "<font face=\"%s\">tv_sec</font>. Isso tem dois defeitos: "
        "<font face=\"%s\">time_t</font> tem 64 bits nas plataformas atuais "
        "e <font face=\"%s\">htonl()</font> converte apenas 32 deles, "
        "corrompendo o valor; e o tamanho de "
        "<font face=\"%s\">struct timeval</font> difere entre Windows e "
        "Linux, o que impediria a comunicação entre sistemas diferentes." %
        (M, M, M, M, M, M)))
    h.append(P(
        "A struct explícita de dois <font face=\"%s\">uint32_t</font> resolve "
        "os dois problemas de uma vez — e isso foi comprovado na prática "
        "(seção 7.3)." % M))

    h.append(P("5.1 Sequência de chamadas", "h2"))
    h.append(codigo("""
SERVIDOR                              CLIENTE
--------                              -------
socket()                              socket()
setsockopt(SO_REUSEADDR)
bind()
listen()
accept()      <--- conexao TCP -----  connect()
                                      send()    envia a hora local
recv()        <--- 8 bytes ---------
  [ semaforo: P() ]
  le o relogio local
send()        ---- 8 bytes --------->  recv()    recebe a hora do servidor
  [ sleep 2 s; semaforo: V() ]
close()                               close()
"""))

    # ----------------------------------------------- 6. CORRECOES
    h.append(P("6. Correções em relação ao código original", "h1"))
    h.append(P(
        "O código fornecido no Moodle, reproduzido nos slides da disciplina, "
        "não compilava no Windows e tinha defeitos que impediriam o trabalho "
        "de funcionar mesmo em Linux. Segue o que foi corrigido:"))
    h.append(Spacer(1, 3))
    h.append(tabela(
        ["#", "Problema no original", "Correção"],
        [["1", "Código POSIX puro; não compila no Windows",
          "camada <font face=\"%s\">#ifdef _WIN32</font> com Winsock2" % M],
         ["2", "<font face=\"%s\">for (j=0;j&lt;1000000;j++);</font> não dá "
               "2 s e é eliminado pelo otimizador do gcc" % M,
          "<font face=\"%s\">Sleep(2000)</font> / "
          "<font face=\"%s\">usleep(2000000)</font>" % (M, M)],
         ["3", "Servidor iterativo: sem concorrência e sem semáforo",
          "uma thread por conexão + semáforo de contagem 1"],
         ["4", "<font face=\"%s\">htonl()</font> sobre "
               "<font face=\"%s\">time_t</font> de 64 bits truncava o valor" % (M, M),
          "struct <font face=\"%s\">wire_time</font> com dois "
          "<font face=\"%s\">uint32_t</font>" % (M, M)],
         ["5", "<font face=\"%s\">accept(..., (int *)0)</font> — tipo errado "
               "(<font face=\"%s\">socklen_t *</font>)" % (M, M),
          "<font face=\"%s\">accept()</font> com "
          "<font face=\"%s\">struct sockaddr_in</font> real" % (M, M)],
         ["6", "Sem <font face=\"%s\">SO_REUSEADDR</font>: \"Address already "
               "in use\" ao reiniciar" % M,
          "<font face=\"%s\">setsockopt(SO_REUSEADDR)</font>" % M],
         ["7", "<font face=\"%s\">read</font>/<font face=\"%s\">write</font> "
               "podiam transferir menos bytes que o pedido" % (M, M),
          "laços <font face=\"%s\">recebe_tudo</font> / "
          "<font face=\"%s\">envia_tudo</font>" % (M, M)],
         ["8", "<font face=\"%s\">bzero</font> e "
               "<font face=\"%s\">&lt;strings.h&gt;</font> (obsoletos)" % (M, M),
          "<font face=\"%s\">memset</font> e "
          "<font face=\"%s\">&lt;string.h&gt;</font>" % (M, M)],
         ["9", "<font face=\"%s\">for (i=1; i&lt;=50000; i++)</font> — limite "
               "arbitrário" % M,
          "laço infinito; encerra com Ctrl+C"]],
        [0.8 * cm, 8.0 * cm, 7.6 * cm]))

    h.append(Spacer(1, 8))
    h.append(P(
        "O item 2 merece destaque numa apresentação: o laço vazio do código "
        "original é removido pelo compilador com <font face=\"%s\">-O1</font> "
        "ou maior, porque não produz efeito observável. Mesmo sem otimização, "
        "um milhão de iterações vazias leva poucos milissegundos num "
        "processador atual — nunca 2 segundos." % M, "nota"))

    # ----------------------------------------------- 7. RESULTADOS
    h.append(P("7. Resultados dos testes", "h1"))
    h.append(P(
        "O projeto foi compilado e executado nos dois sistemas, sempre com "
        "<font face=\"%s\">-O2 -Wall</font> e <b>sem erros nem avisos</b>." % M))
    h.append(Spacer(1, 3))
    h.append(tabela(
        ["", "Windows", "Linux"],
        [["Compilador", "gcc 16.1.0 (MinGW-W64 UCRT)",
          "gcc 15.2.0 (Ubuntu 26.04 LTS, WSL2)"],
         ["API de sockets", "Winsock2 (-lws2_32)", "BSD sockets"],
         ["Threads", "CreateThread", "pthread_create (-pthread)"],
         ["Semáforo", "CreateSemaphore", "sem_init / sem_wait / sem_post"]],
        [3.5 * cm, 6.45 * cm, 6.45 * cm]))

    h.append(P("7.1 Windows — 5 clientes simultâneos", "h2"))
    h.append(codigo("""
[  3.363s] cliente 1 (127.0.0.1:55260) >>> RECURSO ADQUIRIDO
[  5.385s] cliente 2 (127.0.0.1:55261) >>> RECURSO ADQUIRIDO
[  7.393s] cliente 3 (127.0.0.1:55262) >>> RECURSO ADQUIRIDO
[  9.416s] cliente 4 (127.0.0.1:55263) >>> RECURSO ADQUIRIDO
[ 11.430s] cliente 5 (127.0.0.1:55264) >>> RECURSO ADQUIRIDO
""", "Intervalos de 2,022 / 2,008 / 2,023 / 2,014 s. Total: 9,95 s."))

    h.append(P("7.2 Linux — 5 clientes simultâneos", "h2"))
    h.append(codigo("""
[  1.044s] cliente 1 (127.0.0.1:48226) >>> RECURSO ADQUIRIDO
[  3.059s] cliente 2 (127.0.0.1:48230) >>> RECURSO ADQUIRIDO
[  5.060s] cliente 3 (127.0.0.1:48222) >>> RECURSO ADQUIRIDO
[  7.060s] cliente 4 (127.0.0.1:48242) >>> RECURSO ADQUIRIDO
[  9.061s] cliente 5 (127.0.0.1:48258) >>> RECURSO ADQUIRIDO

VALIDACAO
intervalo 1->2 : 2.015 s  [OK]
intervalo 2->3 : 2.001 s  [OK]
intervalo 3->4 : 2.000 s  [OK]
intervalo 4->5 : 2.001 s  [OK]
""", "Total: 8,05 s."))
    h.append(P(
        "Observe, nas duas saídas, que as cinco conexões chegam praticamente "
        "no mesmo instante — todas dentro de poucos milissegundos — e ainda "
        "assim os atendimentos saem separados por 2 segundos. É exatamente o "
        "que o enunciado pede."))

    h.append(P("7.3 Teste de interoperabilidade", "h2"))
    h.append(P(
        "Com o servidor rodando no <b>Linux</b> e quatro clientes no "
        "<b>Windows</b>, a serialização se manteve e as horas trafegaram "
        "corretamente nos dois sentidos. Isso comprova que a correção do "
        "protocolo (item 4 da seção 6) tornou o formato de fio compatível "
        "entre sistemas operacionais diferentes — algo que o código original "
        "não conseguiria."))
    h.append(P(
        "Durante esse teste o servidor recebeu, por acaso, uma conexão que "
        "fechou sem enviar dados. Ele tratou o erro de leitura, liberou o "
        "semáforo e seguiu atendendo normalmente, sem travar nem perder o "
        "recurso — um caso de robustez que vale mencionar na apresentação."))

    # ----------------------------------------------- 8. ROTEIRO
    h.append(P("8. Roteiro sugerido para a apresentação", "h1"))
    h.append(tabela(
        ["Passo", "O que fazer", "O que destacar"],
        [["1", "Abrir <font face=\"%s\">src/servidor.c</font> na função "
               "<font face=\"%s\">atende_cliente()</font>" % (M, M),
          "A região crítica: P(), atendimento, sleep de 2 s, V()"],
         ["2", "Rodar <font face=\"%s\">.\\scripts\\rodar_demo.ps1 -N 5</font>" % M,
          "As 5 conexões chegam juntas; os atendimentos saem de 2 em 2 s"],
         ["3", "Mostrar a janela do servidor",
          "Linhas \"conectado\" quase simultâneas vs. \"RECURSO ADQUIRIDO\" espaçadas"],
         ["4", "Mostrar a saída dos clientes",
          "O campo \"esperou N s\" crescendo: 0, 2, 4, 6, 8"],
         ["5", "Comentar a tabela da seção 6",
          "Por que o laço vazio do original não funcionaria"]],
        [1.4 * cm, 7.0 * cm, 8.0 * cm]))

    h.append(Spacer(1, 10))
    h.append(P("8.1 Perguntas prováveis", "h2"))
    for q, a in [
        ("E se o cliente travar no meio do atendimento?",
         "O servidor usa <font face=\"%s\">recv</font> bloqueante, então a "
         "thread ficaria presa segurando o semáforo. Uma evolução natural "
         "seria aplicar <font face=\"%s\">SO_RCVTIMEO</font> ao socket." % (M, M)),
        ("Por que o semáforo começa em 1, e não em N?",
         "Valor 1 significa exclusão mútua — um atendimento por vez. Um "
         "valor N permitiria N atendimentos simultâneos, o que não é o que "
         "o enunciado pede."),
        ("Os clientes são atendidos na ordem em que chegaram?",
         "Não necessariamente. O semáforo garante <i>exclusão mútua</i>, não "
         "ordem de chegada — quem acorda primeiro depende do escalonador do "
         "sistema operacional. Isso aparece nas saídas: os números dos "
         "clientes nem sempre saem em sequência."),
        ("Daria para usar processos em vez de threads?",
         "Sim, com <font face=\"%s\">fork()</font>, mas o semáforo teria de "
         "ficar em memória compartilhada "
         "(<font face=\"%s\">sem_open</font> ou "
         "<font face=\"%s\">shmget</font>). Threads compartilham o espaço de "
         "endereçamento de graça, e a aula anterior já levantava o custo dos "
         "\"processos pesados\"." % (M, M, M)),
    ]:
        h.append(P("<b>%s</b>" % q, "h3"))
        h.append(P(a))

    # ----------------------------------------------- 9. REFERENCIAS
    h.append(P("9. Referências", "h1"))
    for r in [
        "Material da disciplina — <i>Comunicação entre processos usando "
        "Sockets</i>: API socket, ordenação de bytes e a aplicação de tempo "
        "que serviu de base para este trabalho.",
        "Material da disciplina — <i>Sistemas Distribuídos</i>: definição, "
        "propriedades e transparência de concorrência.",
        "COMER, Douglas E. <i>Internetworking with TCP/IP</i>, vol. 1.",
        "TANENBAUM, Andrew. <i>Sistemas Distribuídos</i>.",
    ]:
        h.append(P("•&nbsp;&nbsp;" + r))

    return h

# ------------------------------------------------------------- montagem
def main():
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    doc = BaseDocTemplate(
        SAIDA, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="Semaforo rudimentar sobre sockets TCP",
        author=AUTOR,
        subject="Trabalho Pratico - Sistemas Distribuidos")

    quadro_capa = Frame(2 * cm, 2 * cm, A4[0] - 4 * cm, A4[1] - 4 * cm,
                        id="capa", showBoundary=0)
    quadro = Frame(2 * cm, 1.85 * cm, A4[0] - 4 * cm, A4[1] - 3.85 * cm,
                   id="normal", showBoundary=0)

    doc.addPageTemplates([
        PageTemplate(id="capa", frames=[quadro_capa], onPage=capa_fundo),
        PageTemplate(id="miolo", frames=[quadro], onPage=moldura),
    ])

    historia = construir()
    # a partir da 2a pagina usa o template do miolo
    historia.insert(len(historia), Spacer(1, 1))
    doc.build(historia)
    print("PDF gerado:", SAIDA)
    print("Fontes TrueType:", "sim" if TEM_TTF else "nao (fallback Helvetica)")

if __name__ == "__main__":
    main()
