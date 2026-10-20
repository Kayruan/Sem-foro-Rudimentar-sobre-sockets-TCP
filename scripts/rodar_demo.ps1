# Sobe o servidor em uma janela separada e dispara N clientes
# simultaneos nesta janela.
#
# Uso:  .\scripts\rodar_demo.ps1          (5 clientes)
#       .\scripts\rodar_demo.ps1 -N 8     (8 clientes)

param([int]$N = 5)

$ErrorActionPreference = "Stop"
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz

if (-not (Test-Path .\bin\servidor.exe)) { .\scripts\compilar.ps1 }

# servidor em janela propria, para a saida nao se misturar
Start-Process powershell -ArgumentList `
    "-NoExit", "-Command", "Set-Location '$raiz'; .\bin\servidor.exe"

Start-Sleep -Milliseconds 800   # da tempo do listen() ficar pronto

"Disparando $N clientes simultaneos..."
""
$exe = Join-Path $raiz "bin\cliente.exe"
$procs = 1..$N | ForEach-Object {
    Start-Process -FilePath $exe -ArgumentList $_ -NoNewWindow -PassThru
}
$procs | Wait-Process

""
"Pronto. Na janela do servidor os atendimentos saem de 2 em 2 s,"
"e aqui acima o campo 'esperou N s' cresce de 2 em 2 segundos."
