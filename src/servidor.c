/* ====================================================================
 * servidor.c -- Servidor de tempo com semaforo rudimentar
 *
 * Trabalho Pratico - Comunicacao e Concorrencia / Sistemas Distribuidos
 *
 * Aceita N clientes concorrentes (uma thread por conexao) e devolve a
 * hora local. O acesso ao relogio -- o "recurso" -- e protegido por um
 * semaforo de contagem 1, que fica retido por 2 s apos cada atendimento.
 * Assim o 1o cliente e atendido em t=0s, o 2o em t=2s, o 3o em t=4s...
 *
 * Compilacao:
 *   Windows: gcc -O2 -Wall src/servidor.c -o bin/servidor.exe -lws2_32
 *   Linux  : gcc -O2 -Wall src/servidor.c -o bin/servidor -pthread
 *
 * Os printf sao sem acentos de proposito: o console do Windows usa
 * code page 850/1252, nao UTF-8.
 * ==================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

/* -------------------------------------------------------------------
 * Portabilidade: uniformiza sockets, threads, semaforo e sleep.
 * ----------------------------------------------------------------- */
#ifdef _WIN32
  #include <winsock2.h>        /* precisa vir antes de windows.h */
  #include <ws2tcpip.h>
  #include <windows.h>
  typedef SOCKET socket_t;
  typedef HANDLE semaforo_t;
  typedef int    socklen_t_;
  #define INVALID_SOCK   INVALID_SOCKET
  #define close_socket   closesocket
  #define sock_errno()   WSAGetLastError()
  #define THREAD_RET     DWORD WINAPI
  #define THREAD_RESULT  0
  #define sleep_ms(ms)   Sleep(ms)
#else
  #include <unistd.h>
  #include <errno.h>
  #include <pthread.h>
  #include <semaphore.h>
  #include <sys/types.h>
  #include <sys/socket.h>
  #include <sys/time.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  typedef int       socket_t;
  typedef sem_t     semaforo_t;
  typedef socklen_t socklen_t_;
  #define INVALID_SOCK   (-1)
  #define close_socket   close
  #define sock_errno()   errno
  #define THREAD_RET     void *
  #define THREAD_RESULT  NULL
  #define sleep_ms(ms)   usleep((ms) * 1000)
#endif

#define MY_PORT_ID    6090
#define TEMPO_LOCK_MS 2000   /* duracao do bloqueio do recurso */

/* Formato de fio: 8 bytes fixos em network byte order.
   Nao se usa struct timeval porque seu tamanho varia entre
   plataformas e htonl() so converte 32 dos 64 bits de time_t. */
struct wire_time {
    uint32_t sec;
    uint32_t usec;
};

static semaforo_t recurso;    /* semaforo de contagem 1 */
static double     t_inicio;   /* instante em que o servidor subiu */

/* ---------------------------- tempo ------------------------------ */

/* Hora atual desde a epoca Unix. No Windows converte o FILETIME,
   que conta intervalos de 100 ns desde 1601. */
static void agora(uint32_t *sec, uint32_t *usec)
{
#ifdef _WIN32
    FILETIME       ft;
    ULARGE_INTEGER li;
    GetSystemTimeAsFileTime(&ft);
    li.LowPart  = ft.dwLowDateTime;
    li.HighPart = ft.dwHighDateTime;
    li.QuadPart -= 116444736000000000ULL;   /* 1601 -> 1970 */
    *sec  = (uint32_t)(li.QuadPart / 10000000ULL);
    *usec = (uint32_t)((li.QuadPart % 10000000ULL) / 10ULL);
#else
    struct timeval tp;
    gettimeofday(&tp, NULL);
    *sec  = (uint32_t)tp.tv_sec;
    *usec = (uint32_t)tp.tv_usec;
#endif
}

/* Segundos desde o inicio do servidor: evidencia o intervalo de 2 s. */
static double decorrido(void)
{
    uint32_t s, us;
    agora(&s, &us);
    return (double)s + (double)us / 1e6 - t_inicio;
}

/* localtime() nao e thread-safe, mas so e chamada dentro da regiao
   critica, onde roda uma thread por vez. */
static void formata_hora(uint32_t sec, char *buf, size_t n)
{
    time_t     t  = (time_t)sec;
    struct tm *lt = localtime(&t);
    if (lt == NULL || strftime(buf, n, "%d/%m/%Y %H:%M:%S", lt) == 0)
        snprintf(buf, n, "data indisponivel");
}

/* ------------------------- E/S confiavel -------------------------- */
/* recv/send podem transferir menos bytes que o pedido. */

static int recebe_tudo(socket_t s, void *buf, int n)
{
    char *p = (char *)buf;
    int   lidos = 0;
    while (lidos < n) {
        int r = recv(s, p + lidos, n - lidos, 0);
        if (r <= 0) return -1;   /* erro ou conexao fechada */
        lidos += r;
    }
    return lidos;
}

static int envia_tudo(socket_t s, const void *buf, int n)
{
    const char *p = (const char *)buf;
    int enviados = 0;
    while (enviados < n) {
        int w = send(s, p + enviados, n - enviados, 0);
        if (w <= 0) return -1;
        enviados += w;
    }
    return enviados;
}

/* --------------------------- semaforo ----------------------------- */

static int sem_criar(semaforo_t *s, unsigned valor)
{
#ifdef _WIN32
    *s = CreateSemaphore(NULL, (LONG)valor, (LONG)valor, NULL);
    return (*s == NULL) ? -1 : 0;
#else
    return sem_init(s, 0, valor);   /* 0 = compartilhado entre threads */
#endif
}

static void sem_descer(semaforo_t *s)   /* P() / wait / down */
{
#ifdef _WIN32
    WaitForSingleObject(*s, INFINITE);
#else
    while (sem_wait(s) == -1 && errno == EINTR) { }   /* retenta se sinal */
#endif
}

static void sem_subir(semaforo_t *s)    /* V() / post / up */
{
#ifdef _WIN32
    ReleaseSemaphore(*s, 1, NULL);
#else
    sem_post(s);
#endif
}

/* ---------------------- atendimento (thread) ---------------------- */

struct conexao {
    socket_t sock;
    int      id;          /* ordem de chegada */
    char     origem[32];  /* "IP:porta" do cliente */
};

static THREAD_RET atende_cliente(void *arg)
{
    struct conexao  *c    = (struct conexao *)arg;
    socket_t         sock = c->sock;
    int              id   = c->id;
    char             origem[32];
    struct wire_time w;
    uint32_t         sec, usec;
    char             hora[64];

    strcpy(origem, c->origem);
    free(c);

    /* Impressa antes da espera: mostra que os clientes chegaram juntos. */
    printf("[%7.3fs] cliente %d (%s) conectado -- aguardando o recurso...\n",
           decorrido(), id, origem);
    fflush(stdout);

    /* ===================== REGIAO CRITICA ===================== */
    sem_descer(&recurso);

    printf("[%7.3fs] cliente %d (%s) >>> RECURSO ADQUIRIDO\n",
           decorrido(), id, origem);

    if (recebe_tudo(sock, &w, (int)sizeof(w)) < 0) {
        printf("[%7.3fs] cliente %d: erro na leitura do socket (%d)\n",
               decorrido(), id, sock_errno());
    } else {
        /* hora que o cliente enviou */
        sec  = ntohl(w.sec);
        usec = ntohl(w.usec);
        formata_hora(sec, hora, sizeof(hora));
        printf("           cliente %d: hora remota = %lu (%s)\n",
               id, (unsigned long)sec, hora);

        /* le o relogio local -- o recurso protegido -- e devolve */
        agora(&sec, &usec);
        formata_hora(sec, hora, sizeof(hora));
        printf("           cliente %d: hora local  = %lu (%s)\n",
               id, (unsigned long)sec, hora);

        w.sec  = htonl(sec);
        w.usec = htonl(usec);
        if (envia_tudo(sock, &w, (int)sizeof(w)) < 0)
            printf("           cliente %d: erro ao escrever no socket (%d)\n",
                   id, sock_errno());
    }

    /* Nucleo do trabalho: o cliente ja foi atendido, mas o recurso
       segue retido por 2 s. So entao o proximo passa pelo sem_descer. */
    printf("[%7.3fs] cliente %d: recurso bloqueado por %d ms...\n",
           decorrido(), id, TEMPO_LOCK_MS);
    fflush(stdout);

    sleep_ms(TEMPO_LOCK_MS);

    printf("[%7.3fs] cliente %d <<< recurso liberado\n", decorrido(), id);
    fflush(stdout);

    sem_subir(&recurso);
    /* =================== FIM DA REGIAO CRITICA ================= */

    close_socket(sock);
    return THREAD_RESULT;
}

/* Thread destacada: ninguem faz join, ela se limpa sozinha. */
static int dispara_thread(struct conexao *c)
{
#ifdef _WIN32
    HANDLE h = CreateThread(NULL, 0, atende_cliente, c, 0, NULL);
    if (h == NULL) return -1;
    CloseHandle(h);
    return 0;
#else
    pthread_t tid;
    if (pthread_create(&tid, NULL, atende_cliente, c) != 0) return -1;
    pthread_detach(tid);
    return 0;
#endif
}

/* ------------------------------ main ------------------------------ */

int main(void)
{
    socket_t           sockid, newsockid;
    struct sockaddr_in ssock_addr;
    int                opt = 1;
    int                contador = 0;
    uint32_t           s0, us0;

    setvbuf(stdout, NULL, _IOLBF, 0);   /* saida linha a linha */

#ifdef _WIN32
    {
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
            printf("erro no WSAStartup: %d\n", WSAGetLastError());
            return 1;
        }
    }
#endif

    agora(&s0, &us0);
    t_inicio = (double)s0 + (double)us0 / 1e6;

    if (sem_criar(&recurso, 1) != 0) {
        printf("erro ao criar o semaforo\n");
        return 1;
    }

    if ((sockid = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCK) {
        printf("erro na criacao do socket: %d\n", sock_errno());
        return 1;
    }

    /* evita "Address already in use" ao reiniciar durante o TIME_WAIT */
    setsockopt(sockid, SOL_SOCKET, SO_REUSEADDR,
               (const char *)&opt, sizeof(opt));

    memset(&ssock_addr, 0, sizeof(ssock_addr));
    ssock_addr.sin_family      = AF_INET;
    ssock_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    ssock_addr.sin_port        = htons(MY_PORT_ID);

    if (bind(sockid, (struct sockaddr *)&ssock_addr,
             sizeof(ssock_addr)) < 0) {
        printf("erro no bind do socket: %d\n", sock_errno());
        close_socket(sockid);
        return 1;
    }

    if (listen(sockid, 64) < 0) {
        printf("erro no listen: %d\n", sock_errno());
        close_socket(sockid);
        return 1;
    }

    printf("Servidor de tempo ouvindo na porta %d\n", MY_PORT_ID);
    printf("Semaforo iniciado com valor 1 -- bloqueio de %d ms por atendimento\n",
           TEMPO_LOCK_MS);
    printf("(Ctrl+C para encerrar)\n\n");

    /* Este laco nunca bloqueia por 2 s: aceita na hora e delega.
       Quem espera no semaforo e a thread de atendimento. */
    for (;;) {
        struct conexao    *c;
        struct sockaddr_in cli_addr;
        socklen_t_         cli_len = (socklen_t_)sizeof(cli_addr);

        newsockid = accept(sockid, (struct sockaddr *)&cli_addr, &cli_len);
        if (newsockid == INVALID_SOCK) {
            printf("erro no accept: %d\n", sock_errno());
            continue;   /* uma falha nao derruba o servidor */
        }

        c = (struct conexao *)malloc(sizeof(*c));
        if (c == NULL) { close_socket(newsockid); continue; }
        c->sock = newsockid;
        c->id   = ++contador;   /* so a thread principal mexe aqui */

        /* identifica quem conectou: inet_ntoa() da a notacao de ponto
           decimal, ntohs() traz a porta para host byte order */
        snprintf(c->origem, sizeof(c->origem), "%s:%u",
                 inet_ntoa(cli_addr.sin_addr),
                 (unsigned)ntohs(cli_addr.sin_port));

        if (dispara_thread(c) != 0) {
            printf("erro ao criar a thread para o cliente %d\n", c->id);
            close_socket(newsockid);
            free(c);
        }
    }

    close_socket(sockid);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
