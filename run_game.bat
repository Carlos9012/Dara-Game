@echo off
SET VENV_PATH=.venv

echo ======================================================
echo [INFO] Script de Inicializacao Dara v1.0 executado.
echo ======================================================

IF NOT EXIST %VENV_PATH% (
    echo [SISTEMA] Ambiente virtual (.venv) nao encontrado.
    echo [SISTEMA] Criando novo ambiente...
    python -m venv %VENV_PATH%
    
    echo [SISTEMA] Instalando dependencias do requirements.txt...
    %VENV_PATH%\Scripts\pip install -r requirements.txt
    
    echo [SUCESSO] Ambiente configurado e pronto!
) ELSE (
    echo [SISTEMA] Ambiente virtual (.venv) ja existente e detectado.
)

echo [SISTEMA] Localizando interpretador Python na venv...
echo [SISTEMA] Comando: %VENV_PATH%\Scripts\python.exe main.py

echo.
echo ------------------------------------------------------
echo [STATUS] TUDO PRONTO! Iniciando o jogo agora...
echo ------------------------------------------------------
echo.

%VENV_PATH%\Scripts\python.exe main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] O jogo fechou com um erro (Codigo: %ERRORLEVEL%).
) ELSE (
    echo.
    echo [SISTEMA] Jogo finalizado normalmente.
)

pause