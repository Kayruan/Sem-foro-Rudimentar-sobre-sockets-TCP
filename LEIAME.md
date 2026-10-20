# Semáforo rudimentar sobre sockets TCP

Trabalho prático de Comunicação e Concorrência — Sistemas Distribuídos.

N clientes se conectam concorrentemente a um servidor e solicitam a hora
local dele. O servidor atende **um cliente por vez** e, após cada
atendimento, mantém o recurso bloqueado por **2 segundos** — de modo que
o 2º cliente só é atendido 2 s após o 1º, o 3º 2 s após o 2º, e assim
por diante.

## Estrutura

```
Trabalho CP/
├── src/
│   ├── servidor.c          servidor multithread com semáforo
│   └── cliente.c           cliente de tempo
├── scripts/
│   ├── compilar.ps1        compila src/ → bin/ (Windows)
│   ├── rodar_demo.ps1      sobe o servidor e dispara N clientes
│   └── gerar_pdf.py        gera a documentação em PDF
├── docs/
│   ├── Documentacao_Trabalho.pdf   documentação completa (8 páginas)
│   └── Trabalho.md                 enunciado do trabalho
├── bin/                    binários gerados pela compilação
├── Makefile                build e demo no Linux/WSL
└── LEIAME.md
```

## Como rodar

### Windows

```powershell
.\scripts\compilar.ps1
.\scripts\rodar_demo.ps1 -N 5
```

No VS Code: `Ctrl+Shift+B` compila; a tarefa **"Rodar demo (5 clientes)"**
executa a demonstração.

Manualmente:

```powershell
# janela 1
.\bin\servidor.exe

# janela 2
1..5 | ForEach-Object { Start-Process -NoNewWindow .\bin\cliente.exe -ArgumentList $_ }
```

### Linux / WSL

```bash
make
make servidor      # em um terminal
make demo N=5      # em outro terminal
```

## Documentação para apresentação

O arquivo [`docs/Documentacao_Trabalho.pdf`](docs/Documentacao_Trabalho.pdf)
traz a documentação completa em 8 páginas: objetivo, estrutura, como usar,
como funciona, protocolo, tabela de correções, resultados dos testes e um
roteiro sugerido para a apresentação com as perguntas mais prováveis.

Para regenerá-lo (por exemplo, após preencher o nome do aluno na variável
`AUTOR`, no topo do script):

```powershell
py -m pip install reportlab    # só na primeira vez
py scripts\gerar_pdf.py
```

## Onde está o semáforo

Em [`src/servidor.c`](src/servidor.c), função `atende_cliente()`:

```c
sem_descer(&recurso);          /* P() — só uma thread passa      */
  ... lê o relógio e responde ao cliente ...
  sleep_ms(TEMPO_LOCK_MS);     /* mantém o recurso preso por 2 s  */
sem_subir(&recurso);           /* V() — libera o próximo cliente  */
```

O semáforo é criado com valor inicial 1 em `main()`. No Windows é um
`CreateSemaphore` da Win32; no Linux, um `sem_t` POSIX.

**Por que threads e não um laço `accept()` sequencial?** Um servidor
iterativo também serializaria os clientes, mas por acidente da
arquitetura — não haveria semáforo nenhum. Com uma thread por conexão
existe concorrência real, e a exclusão mútua passa a ser de fato
responsabilidade do semáforo, que é o objeto de estudo do trabalho. O
material da disciplina cobre isso no slide *"Sockets Multithread"*.

## Resultado observado

Saída do servidor com 5 clientes: as conexões chegam quase juntas, mas
os atendimentos saem de 2 em 2 segundos.

```
[  1.024s] cliente 1 (127.0.0.1:46182) conectado -- aguardando o recurso...
[  1.024s] cliente 2 (127.0.0.1:46184) conectado -- aguardando o recurso...
[  1.024s] cliente 3 (127.0.0.1:46188) conectado -- aguardando o recurso...
[  1.024s] cliente 1 (127.0.0.1:46182) >>> RECURSO ADQUIRIDO
           cliente 1: hora remota = 1792454091 (19/10/2026 20:54:51)
           cliente 1: hora local  = 1792454091 (19/10/2026 20:54:51)
[  1.024s] cliente 1: recurso bloqueado por 2000 ms...
[  3.024s] cliente 1 <<< recurso liberado
[  3.024s] cliente 2 (127.0.0.1:46184) >>> RECURSO ADQUIRIDO
[  5.025s] cliente 3 (127.0.0.1:46188) >>> RECURSO ADQUIRIDO
[  7.025s] cliente 4 (127.0.0.1:46198) >>> RECURSO ADQUIRIDO
[  9.026s] cliente 5 (127.0.0.1:46204) >>> RECURSO ADQUIRIDO
```

Cada cliente imprime sua porta local e o servidor imprime o `IP:porta`
de quem conectou, o que permite casar as duas saídas. Isso responde, de
quebra, à pergunta do slide *"Sockets - dúvidas"* do material:
*"Como mostrar no servidor quem se conectou à sua máquina?"*

## Ambientes testados

Compilado e executado **nos dois sistemas**, sempre com `-O2 -Wall` e
**sem erros nem avisos**.

| | Windows | Linux |
|---|---|---|
| Compilador | gcc 16.1.0 (MinGW-W64 UCRT, WinLibs) | gcc 15.2.0 (Ubuntu 26.04.1 LTS, WSL2) |
| API de sockets | Winsock2 (`-lws2_32`) | BSD sockets |
| Threads | `CreateThread` | `pthread_create` (`-pthread`) |
| Semáforo | `CreateSemaphore` | `sem_init` / `sem_wait` / `sem_post` |
| Pausa de 2 s | `Sleep(2000)` | `usleep(2000000)` |

**Windows — 5 clientes simultâneos:** total 8,28 s; atendimentos em
1,217 / 3,224 / 5,235 / 7,250 / 9,264 s.

**Linux — 5 clientes simultâneos:** total 8,03 s; intervalos medidos de
**2,000 / 2,001 / 2,000 / 2,001 s**.

### Teste de interoperabilidade

Com o servidor no **Linux** e 4 clientes no **Windows**, a serialização
se manteve e as horas trafegaram corretamente nos dois sentidos.

Isso comprova que a correção do protocolo (a struct `wire_time` com dois
`uint32_t` em network byte order, no lugar do `htonl()` sobre `time_t`)
tornou o formato de fio compatível entre sistemas operacionais
diferentes — algo que o código original não conseguiria, já que o
tamanho de `struct timeval` difere entre Windows e Linux.

Durante esse teste o servidor também recebeu uma conexão que fechou sem
enviar dados. Ele tratou o erro de leitura, liberou o semáforo e seguiu
atendendo, sem travar.

## Correções em relação ao código original do Moodle

O código fornecido (`servidor_tempo.c` / `cliente_tempo.c`, reproduzido
nos slides da disciplina) tinha os seguintes problemas:

| # | Problema | Correção |
|---|---|---|
| 1 | Código POSIX puro, não compila no Windows | camada `#ifdef _WIN32` com Winsock2 |
| 2 | `for (j=0;j<1000000;j++);` não dá 2 s e é removido pelo otimizador | `Sleep(2000)` / `usleep(2000000)` |
| 3 | Sem concorrência e sem semáforo | uma thread por conexão + semáforo de contagem 1 |
| 4 | `htonl()` sobre `time_t` de 64 bits truncava o valor | struct `wire_time` com dois `uint32_t` |
| 5 | `accept(..., (int *)0)` — tipo errado (`socklen_t *`) | `accept()` com `struct sockaddr_in` real |
| 6 | Sem `SO_REUSEADDR` → "Address already in use" ao reiniciar | `setsockopt(SO_REUSEADDR)` |
| 7 | `read`/`write` podiam transferir menos bytes que o pedido | laços `recebe_tudo` / `envia_tudo` |
| 8 | `bzero` / `<strings.h>` (obsoletos) | `memset` / `<string.h>` |
| 9 | `for (i=1; i<=50000; i++)` — limite arbitrário | laço infinito, encerra com Ctrl+C |
