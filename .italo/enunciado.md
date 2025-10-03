1)   CHALLENGE REPLY

Chegamos à quarta e última entrega do seu desafio em parceria com a Hermes Reply. Agora é a hora de integrar o que foi feito nas fases anteriores em um fluxo fim-a-fim: dos sensores (simulados/ESP32) → ingestão → armazenamento em banco → modelo de ML → exposição de resultados em dashboard/relatórios e alertas.

Esta entrega consolida a visão de arquitetura (Entrega 1), a simulação e coleta (Entrega 2) e a modelagem + ML (Entrega 3) em um MVP funcional e coerente com o contexto industrial digitalizado.



2)   CONTEXTO

Sugerimos que você e seu grupo revisite os contextos das FASES anteriores para relembrar e completar o entendimento desta entrega.

Na Indústria 4.0, sensores conectados geram dados que precisam fluir de forma confiável até camadas analíticas e de decisão (ML, dashboards, alertas). Esse é exatamente o cenário que vocês já planejaram (arquitetura e pipeline), simularam (ESP32 + sensores) e modelaram (banco relacional + ML). Agora, vamos “costurar” tudo em um MVP integrado, com ênfase em observabilidade e reprodutibilidade.



3)   OBJETIVOS

Os objetivos desta entrega são:

Integrar os componentes das Entregas 1, 2 e 3 em um pipeline executável (simulado ou real), contemplando:
Coleta/ingestão de dados do ESP32/simulação (Wokwi/VSCode/PlatformIO);
Persistência no banco relacional modelado;
Treino e/ou inferência do modelo de ML básico;
Dashboard/relatório com KPIs e alertas (thresholds ou regra simples).
Vocês deverão:

1. Publicar a arquitetura final (app.diagrams.net) com o encadeamento dos blocos (fonte de dados → ingestão → armazenamento → ML → visualização/alerta).

2. Demonstrar o fluxo completo com dados percorrendo o pipeline até um resultado visível (gráfico/métrica/alerta).

3. Documentar decisões técnicas e como as peças se integram (ligação explícita com as entregas anteriores).



4)   REQUISITOS TÉCNICOS E FUNCIONAIS

4.1) Arquitetura Integrada

Diagrama no app.diagrams.net (ou equivalente) incluindo: origem (ESP32/sim), transporte (exemplo: MQTT/HTTP/serial), ETL/ELT simples, banco relacional (tabelas da Entrega 3), bloco de ML (treino ou inferência) e camada de visualização/alertas. Evidencie fluxos de dados, formatos (CSV/JSON) e periodicidades.

4.2) Coleta e Ingestão

Circuito/simulação com ESP32 e pelo menos 1 sensor ativo, reproduzindo leituras variáveis (Wokwi/VSCode/PlatformIO), com registro/stream para posterior carga no banco. Inclua prints do Monitor Serial ou logs e um gráfico inicial da série lida (linha/barra/disp.).

4.3) Banco de Dados

Utilizar o DER e tabelas definidos anteriormente; prover script SQL de criação e carga (bulk ou INSERTs). Explique as chaves e as restrições relevantes para integridade e consulta.

4.4) ML Básico Integrado

Operacionalizar treino e/ou inferência sobre dados do banco (pode ser batch simples). Exibir ao menos 1 métrica (por exemplo: acurácia, MAE) e 1 visualização pertinente (por exemplo: curva de previsão, matriz de confusão). Indicar o dataset utilizado e o passo a passo.

4.5) Visualização e Alertas

Dashboard/relatório (Streamlit/Dash/Gráfico em notebook) exibindo KPI(s) do processo (por exemplo: média/variação do sensor, score do modelo, número de alertas).

Alerta mínimo: defina um threshold simples (por exemplo: temperatura > X) e mostre o evento (banner/log/email fictício/print).

4.6) Reprodutibilidade e Organização

README detalhando: setup local, ordem de execução (coleta → carga → ML → dashboard/alerta), parametrizações e referências às Entregas 1, 2 e 3.

Scripts versionados e prints que evidenciem cada etapa do fluxo.



5)   ENTREGÁVEIS

5.1) Repositório GitHub Público (recomendado)

/docs/arquitetura: diagrama (.drawio/.png) com o fluxo integrado.
/ingest/: código de coleta/ingestão (ESP32/sim), prints de execução e 1 gráfico simples.
/db/: script CREATE TABLE, script/código de carga e evidências (SELECT/prints).
/ml/: notebook ou .py com treino/inferência, métrica(s) e visualização(ões).
/dashboard/: app/relatório com KPI(s) e alerta mínimo demonstrado.
README com: visão geral, como rodar, decisões, vínculo com as Entregas 1-3 e o link do vídeo (de até 5 minutos postado como “não listado” no YouTube).
5.2) Vídeo explicativo

Vídeo (de até 5 minutos postado como “não listado” no YouTube);
Demonstração do fluxo ponta-a-ponta, como (coleta→banco→ML→dashboard/alerta) + arquitetura + principais decisões.




6)   REGRAS GERAIS

O repositório não poderá sofrer alterações após a data limite de entrega;
Todos os integrantes devem participar da criação e documentação da modelagem;
A avaliação irá considerar: qualidade técnica da modelagem, funcionamento do código de ML, clareza na documentação e organização geral do repositório.