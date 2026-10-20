# Compila src/ para bin/ usando o gcc do WinLibs (MinGW-w64).
# Uso:  .\scripts\compilar.ps1

$ErrorActionPreference = "Stop"
$raiz = Split-Path $PSScriptRoot -Parent
Set-Location $raiz

$gcc = "C:\Users\kayru\AppData\Local\Microsoft\WinGet\Packages\" +
       "BrechtSanders.WinLibs.POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\" +
       "mingw64\bin\gcc.exe"

if (-not (Test-Path $gcc)) {
    $c = Get-Command gcc -ErrorAction SilentlyContinue
    if ($c) { $gcc = $c.Source } else { throw "gcc nao encontrado" }
}

New-Item -ItemType Directory -Force -Path "bin" | Out-Null

# -lws2_32 (Winsock) precisa vir DEPOIS do arquivo-fonte
& $gcc -O2 -Wall -g src\servidor.c -o bin\servidor.exe -lws2_32
if ($LASTEXITCODE -ne 0) { throw "falha ao compilar o servidor" }

& $gcc -O2 -Wall -g src\cliente.c -o bin\cliente.exe -lws2_32
if ($LASTEXITCODE -ne 0) { throw "falha ao compilar o cliente" }

"Compilado: bin\servidor.exe e bin\cliente.exe"
