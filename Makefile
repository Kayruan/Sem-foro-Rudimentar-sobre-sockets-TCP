# Makefile para Linux / WSL
#
#   make          compila para bin/
#   make servidor roda o servidor
#   make demo     dispara N clientes simultaneos (padrao 5)
#   make clean    remove bin/

CC     = gcc
CFLAGS = -O2 -Wall -g
SRC    = src
BIN    = bin
N      = 5

all: $(BIN)/servidor $(BIN)/cliente

$(BIN):
	mkdir -p $(BIN)

# -pthread: o servidor usa threads e semaforos POSIX
$(BIN)/servidor: $(SRC)/servidor.c | $(BIN)
	$(CC) $(CFLAGS) $< -o $@ -pthread

$(BIN)/cliente: $(SRC)/cliente.c | $(BIN)
	$(CC) $(CFLAGS) $< -o $@

servidor: $(BIN)/servidor
	./$(BIN)/servidor

demo: $(BIN)/cliente
	@echo "Disparando $(N) clientes simultaneos..."
	@for i in $$(seq 1 $(N)); do ./$(BIN)/cliente $$i & done; wait

# Remove apenas os binarios do Linux. Nao apaga os .exe do Windows,
# que podem estar na mesma pasta bin/ (e ate em uso pelo sistema).
clean:
	rm -f $(BIN)/servidor $(BIN)/cliente

.PHONY: all servidor demo clean
