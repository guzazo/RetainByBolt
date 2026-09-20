# Aplicação das 10 heurísticas de Nielsen

Este documento registra como as heurísticas foram traduzidas para a interface do Copiloto de Retenção.

1. **Visibilidade do estado:** a faixa superior informa que a base foi carregada, o volume analisado e o caráter demonstrativo do modelo. Ações registradas geram confirmação imediata.
2. **Correspondência com o mundo real:** a interface usa os termos da rotina de CS — fila, risco, mensalidade, valor exposto e próxima ação — e explica as fórmulas em linguagem direta.
3. **Controle e liberdade:** o gestor pode alternar os pesos, restaurar a recomendação, escolher um cliente e desfazer o registro de uma ação.
4. **Consistência e padrões:** estados, badges, botões, cores de risco, títulos de etapa e controles de explicação seguem os mesmos padrões visuais e verbais.
5. **Prevenção de erros:** o cálculo é interrompido com uma mensagem clara quando todos os fatores estão desativados; ações já registradas não podem ser duplicadas.
6. **Reconhecimento em vez de memorização:** o fluxo permanece visível, os clientes exibem contexto essencial e métricas e conceitos têm ajuda no próprio ponto de uso.
7. **Flexibilidade e eficiência:** a pessoa escolhe entre leitura Essencial e Detalhada, usa pesos recomendados ou ajustados e acessa a metodologia sem sair da tarefa.
8. **Estética e design minimalista:** explicações longas foram movidas para popovers, ajuda contextual e um controle de metodologia recolhido por padrão.
9. **Reconhecer e recuperar erros:** configurações inválidas têm mensagem acionável; registros podem ser desfeitos; a fila vazia orienta o próximo passo.
10. **Ajuda e documentação:** a barra lateral contém uma ajuda rápida e a metodologia completa preserva cálculos, fontes, limitações e tabelas.

## Princípio de conteúdo

Nenhuma explicação foi removida. O conteúdo foi organizado por divulgação progressiva:

- decisão e sinais essenciais ficam visíveis;
- contexto curto aparece em ajuda contextual;
- diagnósticos e justificativas abrem em badges clicáveis;
- cálculos e limitações completas ficam no controle **Ver transparência e metodologia**.
