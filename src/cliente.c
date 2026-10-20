/* ====================================================================
 * cliente.c -- Cliente do servidor de tempo
 *
 * Trabalho Pratico - Comunicacao e Concorrencia / Sistemas Distribuidos
 *
 * Conecta ao servidor, envia a propria hora local, le de volta a hora
 * do servidor e imprime na tela. Mede tambem quanto tempo ficou
 * bloqueado esperando o semaforo: disparando N clientes juntos, as
 * esperas saem ~0s, 2s, 4s, 6s...
 *
 * Uso: cliente [rotulo] [host] [porta]
 *      cliente 3                    -> rotulo "3", 127.0.0.1:6090
 *      cliente A 192.168.0.10 6090
 *
 * Compilacao:
 *   Windows: gcc -O2 -Wall src/cliente.c -o bin/cliente.exe -lws2_32
 *   Linux  : gcc -O2 -Wall src/cliente.c -o bin/cliente
 * ==================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <stdint.h>

/* ------- portabilidade (mesma logica do servidor, sem threads) ----- */
#ifdef _WIN32
  #include <winsock2.h>
  #include <ws2tcpip.h>
  #include <windows.h>
  typedef SOCKET socket_t;
  #define INVALID_SOCK  INVALID_SOCKET
  #define close_socket  closesocket
  #define sock_errno()  WSAGetLastError()
#else
  #include <unistd.h>
  #include <errno.h>
  #include <sys/types.h>
  #include <sys/socket.h>
  #include <sys/time.h>
  #include <netinet/in.h>
  #include <arpa/inet.h>
  typedef int socket_t;
  #define INVALID_SOCK  (-1)
  #define close_socket  close
  #define sock_errno()  errno
#endif

#define SERV_HOST_ADDR "127.0.0.1"
#define SERV_PORT_ID   6090

/* mesmo formato de fio do servidor: 8 bytes em network byte order */
struct wire_time {
    uint32_t sec;
    uint32_t usec;
};

/* Hora atual desde a epoca Unix (ver comentario em servidor.c). */
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

/* relogio em ponto flutuante, para cronometrar a espera */
static double relogio(void)
{
    uint32_t s, us;
    agora(&s, &us);
    return (double)s + (double)us / 1e6;
}

static void formata_hora(uint32_t sec, char *buf, size_t n)
{
    time_t     t  = (time_t)sec;
    struct tm *lt = localtime(&t);
    if (lt == NULL || strftime(buf, n, "%d/%m/%Y %H:%M:%S", lt) == 0)
        snprintf(buf, n, "data indisponivel");
}

/* recv/send podem transferir menos bytes que o pedido */

static int recebe_tudo(socket_t s, void *buf, int n)
{
    char *p = (char *)buf;
    int   lidos = 0;
    while (lidos < n) {
        int r = recv(s, p + lidos, n - lidos, 0);
        if (r <= 0) return -1;
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

int main(int argc, char *argv[])
{
    socket_t           sockid;
    struct sockaddr_in ssock_addr;
    struct wire_time   w;
    uint32_t           sec, usec;
    char               hora[64];
    double             t0, t1;

    const char *rotulo = (argc > 1) ? argv[1] : "1";
    const char *host   = (argc > 2) ? argv[2] : SERV_HOST_ADDR;
    int         porta  = (argc > 3) ? atoi(argv[3]) : SERV_PORT_ID;

    setvbuf(stdout, NULL, _IOLBF, 0);

#ifdef _WIN32
    {
        WSADATA wsa;
        if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
            printf("erro no WSAStartup: %d\n", WSAGetLastError());
            return 1;
        }
    }
#endif

    if ((sockid = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCK) {
        printf("cliente %s: erro na criacao do socket: %d\n",
               rotulo, sock_errno());
        return 1;
    }

    memset(&ssock_addr, 0, sizeof(ssock_addr));
    ssock_addr.sin_family      = AF_INET;
    ssock_addr.sin_addr.s_addr = inet_addr(host);   /* ja devolve em NBO */
    ssock_addr.sin_port        = htons((unsigned short)porta);

    printf("cliente %s: conectando em %s:%d ...\n", rotulo, host, porta);

    /* O connect retorna rapido mesmo com o semaforo ocupado: o servidor
       aceita todas as conexoes na hora. A espera acontece no recv. */
    if (connect(sockid, (struct sockaddr *)&ssock_addr,
                sizeof(ssock_addr)) < 0) {
        printf("cliente %s: erro ao conectar no servidor: %d\n",
               rotulo, sock_errno());
        close_socket(sockid);
        return 1;
    }

    /* porta local: permite casar esta saida com a do servidor */
    {
        struct sockaddr_in minha;
#ifdef _WIN32
        int len = (int)sizeof(minha);
#else
        socklen_t len = (socklen_t)sizeof(minha);
#endif
        if (getsockname(sockid, (struct sockaddr *)&minha, &len) == 0)
            printf("cliente %s: minha porta local e %u\n",
                   rotulo, (unsigned)ntohs(minha.sin_port));
    }

    /* envia a hora local */
    agora(&sec, &usec);
    formata_hora(sec, hora, sizeof(hora));
    printf("cliente %s: hora local  = %lu (%s)\n",
           rotulo, (unsigned long)sec, hora);

    w.sec  = htonl(sec);
    w.usec = htonl(usec);
    if (envia_tudo(sockid, &w, (int)sizeof(w)) < 0) {
        printf("cliente %s: erro ao escrever no socket\n", rotulo);
        close_socket(sockid);
        return 1;
    }

    /* bloqueia aqui ate o semaforo do servidor liberar */
    printf("cliente %s: pedido enviado, aguardando o servidor...\n", rotulo);
    t0 = relogio();

    if (recebe_tudo(sockid, &w, (int)sizeof(w)) < 0) {
        printf("cliente %s: erro na leitura do socket\n", rotulo);
        close_socket(sockid);
        return 1;
    }
    t1 = relogio();

    sec  = ntohl(w.sec);
    usec = ntohl(w.usec);
    formata_hora(sec, hora, sizeof(hora));
    printf("cliente %s: hora remota = %lu (%s)\n",
           rotulo, (unsigned long)sec, hora);
    printf("cliente %s: esperou %.3f s pelo recurso\n", rotulo, t1 - t0);

    close_socket(sockid);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
