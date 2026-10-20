# Semáforo rudimentar sobre sockets TCP

> Controle de acesso concorrente a um recurso distribuído, implementado em C com
> sockets TCP, threads e semáforos — portável entre Windows e Linux a partir do
> mesmo código-fonte.

![C](https://img.shields.io/badge/C-00599C?style=flat&logo=c&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-0078D6?style=flat&logo=windows&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat&logo=linux&logoColor=black)
![GCC](https://img.shields.io/badge/GCC-4EAA25?style=flat&logo=gnu&logoColor=white)
![Make](https://img.shields.io/badge/Make-427819?style=flat&logo=gnu&logoColor=white)

Trabalho prático da disciplina de **Sistemas Distribuídos — Comunicação e
Concorrência**.

---

## Sumário

- [Sobre](#sobre)
- [Demonstração](#demonstração)
- [Tecnologias utilizadas](#tecnologias-utilizadas)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Como executar](#como-executar)
- [Como funciona](#como-funciona)
- [Resultados dos testes](#resultados-dos-testes)
- [Correções em relação ao código original](#correções-em-relação-ao-código-original)
- [Documentação](#documentação)
- [Autor](#autor)

---

## Sobre

**N clientes** se conectam simultaneamente a um servidor e solicitam a hora
local dele. O servidor atende **um cliente por vez** e, após cada atendimento,
mantém o recurso bloqueado por **2 segundos** — de modo que o 2º cliente só seja
atendido dois segundos após o 1º, o 3º dois segundos após o 2º, e assim por
diante.

O ponto central é que os clientes chegam **ao mesmo tempo**, mas são servidos
**em fila**. Quem impõe essa ordem é um semáforo de contagem 1.

O servidor é concorrente de verdade: cada conexão é tratada por uma thread
dedicada. A serialização não vem da arquitetura — vem do semáforo, que é o
objeto de estudo do trabalho.

---

## Demonstração

Saída do servidor com 5 clientes disparados simultaneamente. As conexões chegam
praticamente no mesmo instante, mas os atendimentos saem de 2 em 2 segundos:

```text
[  1.024s] cliente 1 (127.0.0.1:46182) conectado -- aguardando o recurso...
[  1.024s] cliente 2 (127.0.0.1:46184) conectado -- aguardando o recurso...
[  1.024s] cliente 3 (127.0.0.1:46188) conectado -- aguardando o recurso...
[  1.024s] cliente 4 (127.0.0.1:46198) conectado -- aguardando o recurso...
[  1.024s] cliente 5 (127.0.0.1:46204) conectado -- aguardando o recurso...
[  1.024s] cliente 1 >>> RECURSO ADQUIRIDO
           cliente 1: hora remota = 1792454091 (19/10/2026 20:54:51)
           cliente 1: hora local  = 1792454091 (19/10/2026 20:54:51)
[  1.024s] cliente 1: recurso bloqueado por 2000 ms...
[  3.024s] cliente 1 <<< recurso liberado
[  3.024s] cliente 2 >>> RECURSO ADQUIRIDO
[  5.025s] cliente 3 >>> RECURSO ADQUIRIDO
[  7.025s] cliente 4 >>> RECURSO ADQUIRIDO
[  9.026s] cliente 5 >>> RECURSO ADQUIRIDO
```

Do lado do cliente, o tempo de espera cresce de 2 em 2 segundos:

| Porta local | Esperou |
|-------------|---------|
| 46182       | 0,016 s |
| 46184       | 2,016 s |
| 46188       | 4,016 s |
| 46198       | 6,017 s |
| 46204       | 8,002 s |

---

## Tecnologias utilizadas

### Linguagem e APIs

| Tecnologia | Uso no projeto |
|---|---|
| **C** | Linguagem única do projeto, sem dependências externas |
| **TCP/IP** | Transporte confiável e orientado a conexão (`SOCK_STREAM`) |
| **Winsock2** (`ws2_32`) | API de sockets no Windows |
| **BSD Sockets** | API de sockets no Linux (`sys/socket.h`, `netinet/in.h`) |
| **Win32 Threads** | `CreateThread` — uma thread por conexão no Windows |
| **POSIX Threads** (pthreads) | `pthread_create` / `pthread_detach` no Linux |
| **Win32 Semaphore** | `CreateSemaphore` / `WaitForSingleObject` / `ReleaseSemaphore` |
| **POSIX Semaphores** | `sem_init` / `sem_wait` / `sem_post` |

A seleção entre as duas pilhas acontece em **tempo de compilação**, por
diretivas `#ifdef _WIN32`. O mesmo arquivo-fonte compila nos dois sistemas sem
nenhuma alteração manual.

### Ferramentas de build e automação

| Ferramenta | Uso no projeto |
|---|---|
| **GCC / MinGW-w64** | Compilação (`-O2 -Wall`) nas duas plataformas |
| **GNU Make** | Build e demonstração no Linux |
| **PowerShell** | Scripts de build e demonstração no Windows |
| **WSL2 (Ubuntu)** | Ambiente Linux usado para desenvolvimento e testes |
| **Python + ReportLab** | Geração da documentação em PDF |

### Versões verificadas

| | Windows | Linux |
|---|---|---|
| Compilador | gcc 16.1.0 (MinGW-W64 x86_64-ucrt-posix-seh) | gcc 15.2.0 (Ubuntu 26.04.1 LTS) |
| Build | `scripts/compilar.ps1` | GNU Make 4.4.1 |
| Padrão C | compila de `gnu99` a `gnu23` | requer `gnu99`+ (usa `usleep`) |

Compilação com `-O2 -Wall`: **sem erros e sem avisos** nos dois sistemas.

---

## Estrutura do projeto

```text
.
├── src/
│   ├── servidor.c          servidor multithread com semáforo (362 linhas)
│   └── cliente.c           cliente de tempo (218 linhas)
├── scripts/
│   ├── compilar.ps1        compila src/ → bin/ (Windows)
│   ├── rodar_demo.ps1      sobe o servidor e dispara N clientes
│   └── gerar_pdf.py        gera a documentação em PDF
├── docs/
│   ├── Documentacao_Trabalho.pdf   documentação completa (8 páginas)
│   └── Trabalho.md                 enunciado do trabalho
├── bin/                    binários gerados pela compilação
├── .vscode/tasks.json      tarefas de build do VS Code
├── Makefile                build e demo no Linux/WSL
└── README.md
```

---

## Pré-requisitos

**Windows**
- GCC para Windows — [MinGW-w64 (WinLibs)](https://winlibs.com/), variante UCRT + POSIX threads
- PowerShell 5.1 ou superior (já incluso no Windows)

**Linux / WSL**
- `build-essential` (gcc + make)

```bash
sudo apt install build-essential
```

**Opcional** — para regenerar o PDF da documentação:

```bash
pip install reportlab
```

---

## Como executar

### Windows

```powershell
.\scripts\compilar.ps1          # gera bin\servidor.exe e bin\cliente.exe
.\scripts\rodar_demo.ps1 -N 5   # sobe o servidor e dispara 5 clientes
```

No VS Code: `Ctrl+Shift+B` compila; a tarefa **"Rodar demo (5 clientes)"**
executa a demonstração.

Manualmente, em duas janelas:

```powershell
# janela 1 — servidor
.\bin\servidor.exe

# janela 2 — cinco clientes ao mesmo tempo
1..5 | ForEach-Object { Start-Process -NoNewWindow .\bin\cliente.exe -ArgumentList $_ }
```

### Linux / WSL

```bash
make                 # compila para bin/
make servidor        # roda o servidor     (terminal 1)
make demo N=5        # dispara 5 clientes  (terminal 2)
make clean           # remove os binários do Linux
```

### Argumentos do cliente

```text
cliente [rotulo] [host] [porta]

cliente 3                      # rótulo "3", conecta em 127.0.0.1:6090
cliente A 192.168.0.10 6090    # conecta em outra máquina da rede
```

Sem argumentos, assume rótulo `1` e servidor em `127.0.0.1:6090`.

---

## Como funciona

### Arquitetura

```text
thread principal                    thread de atendimento (uma por cliente)
----------------                    ----------------------------------------
accept()  ..... conexão 1 ------->  sem_descer()   <-- bloqueia aqui
accept()  ..... conexão 2 ------->  sem_descer()       se o recurso
accept()  ..... conexão 3 ------->  sem_descer()       estiver ocupado
accept()  ..... conexão 4 ------->  sem_descer()
   (nunca espera 2 s)                  │
                                       ├──> lê a hora, responde ao cliente
                                       ├──> sleep 2 s  (recurso retido)
                                       └──> sem_subir()  libera o próximo
```

### O semáforo

Criado com valor inicial **1**: exatamente um atendimento por vez. A região
crítica está em `atende_cliente()`, em [`src/servidor.c`](src/servidor.c):

```c
/* ===================== REGIÃO CRÍTICA ===================== */
sem_descer(&recurso);            /* P()  -- só uma thread passa     */

    ... lê o relógio local e responde ao cliente ...

/* O cliente já foi atendido, mas o recurso segue retido por 2 s.
   Só então o próximo passa pelo sem_descer. */
sleep_ms(TEMPO_LOCK_MS);         /* 2000 ms                         */

sem_subir(&recurso);             /* V()  -- libera o próximo        */
/* =================== FIM DA REGIÃO CRÍTICA ================= */
```

O `sleep` fica **dentro** da região crítica, antes do `sem_subir()`. É isso que
produz o espaçamento de 2 em 2 segundos: não é o atendimento que demora, é o
recurso que permanece bloqueado.

### Protocolo

Cliente e servidor trocam **8 bytes** em cada sentido, em *network byte order*:

```c
struct wire_time {
    uint32_t sec;    /* segundos desde 01/01/1970        */
    uint32_t usec;   /* microssegundos dentro do segundo */
};
```

Formato de fio explícito em vez de enviar `struct timeval` direto — o tamanho
dessa struct difere entre Windows e Linux, e `htonl()` converteria apenas 32 dos
64 bits de `time_t`.

### Sobre a ordem de atendimento

O semáforo garante **exclusão mútua**, não **ordem de chegada**. Os clientes
podem ser atendidos fora da sequência numérica, nos dois sistemas operacionais.

Medindo 5 execuções em cada plataforma, a ordem de concessão do semáforo bateu
com a ordem de chegada das threads em **10 de 10 rodadas** — o semáforo é FIFO
na prática. O embaralhamento ocorre *antes*, no escalonamento das threads entre
o `accept()` e o `sem_descer()`, e é mais frequente no Linux apenas porque os
processos sobem mais rápido (espalhamento de ~0 ms entre as conexões, contra
~55 ms no Windows), tornando a disputa mais acirrada.

---

## Resultados dos testes

| Teste | Resultado |
|---|---|
| Windows — 5 clientes simultâneos | 9,95 s; intervalos 2,022 / 2,008 / 2,023 / 2,014 s |
| Linux — 5 clientes simultâneos | 8,05 s; intervalos 2,015 / 2,001 / 2,000 / 2,001 s |
| Linux — `make demo N=3` | esperas de 0,001 / 2,001 / 4,002 s |
| Compilação (ambos, `-O2 -Wall`) | sem erros, sem avisos |

### Interoperabilidade entre sistemas

Com o **servidor no Linux** e **4 clientes no Windows**, a serialização se
manteve e as horas trafegaram corretamente nos dois sentidos. Isso comprova que
o formato de fio é compatível entre sistemas operacionais diferentes — algo que
o código original não conseguiria.

Durante esse teste o servidor recebeu uma conexão que fechou sem enviar dados.
Ele tratou o erro de leitura, liberou o semáforo e seguiu atendendo, sem travar.

---

## Correções em relação ao código original

O código fornecido na disciplina (`servidor_tempo.c` / `cliente_tempo.c`) não
compilava no Windows e tinha defeitos que impediriam o trabalho de funcionar
mesmo em Linux.

| # | Problema no original | Correção |
|---|---|---|
| 1 | Código POSIX puro; não compila no Windows | camada `#ifdef _WIN32` com Winsock2 |
| 2 | `for (j=0;j<1000000;j++);` não dá 2 s e é eliminado pelo otimizador | `Sleep(2000)` / `usleep(2000000)` |
| 3 | Servidor iterativo: sem concorrência e sem semáforo | uma thread por conexão + semáforo de contagem 1 |
| 4 | `htonl()` sobre `time_t` de 64 bits truncava o valor | struct `wire_time` com dois `uint32_t` |
| 5 | `accept(..., (int *)0)` — tipo errado (`socklen_t *`) | `accept()` com `struct sockaddr_in` real |
| 6 | Sem `SO_REUSEADDR`: "Address already in use" ao reiniciar | `setsockopt(SO_REUSEADDR)` |
| 7 | `read`/`write` podiam transferir menos bytes que o pedido | laços `recebe_tudo` / `envia_tudo` |
| 8 | `bzero` e `<strings.h>` (obsoletos) | `memset` e `<string.h>` |
| 9 | `for (i=1; i<=50000; i++)` — limite arbitrário | laço infinito; encerra com `Ctrl+C` |

O item 2 merece destaque: o laço vazio é removido pelo compilador com `-O1` ou
maior, porque não produz efeito observável. Mesmo sem otimização, um milhão de
iterações vazias leva poucos milissegundos num processador atual — nunca 2
segundos.

---

## Documentação

O arquivo [`docs/Documentacao_Trabalho.pdf`](docs/Documentacao_Trabalho.pdf)
traz a documentação completa em 8 páginas: objetivo, estrutura, como usar, como
funciona, protocolo, tabela de correções, resultados dos testes e um roteiro
sugerido para apresentação.

Para regenerá-lo:

```bash
pip install reportlab
python scripts/gerar_pdf.py
```

---

## Autor

**Kayruan da Cruz Soares**

Trabalho acadêmico — Sistemas Distribuídos, Comunicação e Concorrência.
