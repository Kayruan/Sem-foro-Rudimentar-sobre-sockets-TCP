# Trabalho Prático - Comunicação e Concorrência
# Objetivo: Implementar um semáforo rudimentar, para controlar o acesso a recursos distribuídos de forma concorrente.

Devem ser utilizados os códigos-fonte disponíveis no Moodle (servidor_tempo.c e cliente_tempo.c);
Como: N clientes devem se conectar a um servidor e solicitar a hora do servidor.
Quando o primeiro cliente for atendido, o servidor deve bloquear o recurso por 2 segundos, de forma que o 2º cliente só possa ser atendido após estes dois segundos
após os dois segundos de bloqueio, o 2º cliente pode ser atendido (e assim, sucessivamente)
O atendimento do servidor consiste em fornecer a hora local para os clientes... e os clientes imprimem esta hora em suas telas (conforme o código fonte fornecido) 