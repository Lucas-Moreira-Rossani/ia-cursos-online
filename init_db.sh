#!/bin/bash

# Script para inicializar o banco de dados e executar migrações
# Este script deve ser executado após o deploy no Render

# Inicializar as migrações (executado apenas uma vez)
echo "Inicializando migrações..."
flask --app src.migrations db init

# Criar a migração inicial
echo "Criando migração inicial..."
flask --app src.migrations db migrate -m "Migração inicial"

# Aplicar a migração
echo "Aplicando migrações..."
flask --app src.migrations db upgrade

echo "Configuração do banco de dados concluída!"
