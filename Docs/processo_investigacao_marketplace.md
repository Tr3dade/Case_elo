# Processo de Investigação — Narrativa Margem + Marketplace

**Artefato de processo · Vértice Retail · BootCamp Nova Geração, Elo Group**
**Documento:** rastreabilidade completa do raciocínio, da ideia inicial à conclusão final dos 3 pilares testados.

---

## 1. Ponto de partida

O case pediu uma resposta objetiva em até 90 dias para: *como usar dados e IA para melhorar rentabilidade, eficiência operacional e qualidade de tomada de decisão da Vértice Retail?*

A squad chegou com uma ideia inicial de solução: um dashboard de margem por canal/categoria/mês, com alerta automático quando a margem cruzasse um threshold de 53%.

## 2. Crítica externa que redirecionou a investigação

Na mentoria com Claudio Azzi (Elo Group), a ideia inicial foi questionada diretamente:

> "É o risco de você construir a solução antes de entender o problema."

A recomendação foi decompor o problema (margem = receita − despesa, estratificado por canal, categoria, cliente) antes de propor qualquer solução — usando frameworks clássicos de consultoria como guia, não para copiar a resposta, mas para saber quais perguntas fazer. Essa recomendação foi confirmada por escrito na monitoria seguinte.

## 3. Duas investigações independentes, feitas em paralelo

Vale registrar que as duas não se alimentaram uma da outra — cada uma partiu direto dos CSVs brutos, por caminhos diferentes:

- **Conselho de 5 perspectivas** (duas rodadas, `relatorio_conselho_vertice2.md`): decidiu manter Margem+E-commerce/Marketplace como narrativa central e o classificador de atendimento como agente de IA principal, usando como critério a grade de avaliação do bootcamp (8 blocos, 5 dimensões), não o ROI de negócio real.
- **Análise quantitativa do Matheus** (`Analise_Indicadores_Vertice.md`): script mais direto sobre os 5 CSVs, com achados adicionais — margem fantasma de devolução e o achado crítico que reabriu toda essa investigação: a receita "gerada" reportada por marketing é ~46x maior que a receita líquida real de vendas.

**Convergência real entre as duas:** bater em número exato de margem por canal (51,4% no Marketplace, em ambos os documentos) é esperado — é o mesmo cálculo sobre a mesma base, não é descoberta independente. O que é de fato valioso é que, entre várias hipóteses possíveis (categoria, SKU, sazonalidade, canal), **as duas análises, sem se cruzar, isolaram o mesmo recorte como relevante**: devolução não descontada da margem reportada, e canal Marketplace como o outlier de margem.

## 4. O problema do "duplo sinal" — o ROAS não sustentava sozinho

A narrativa original se apoiava em dois sinais simultâneos do Marketplace: pior margem de venda **e** pior ROAS de marketing. Mas o achado do Matheus (receita de marketing 46x maior que a venda real) colocava em dúvida se o ROAS reportado era confiável o suficiente pra sustentar essa segunda perna do argumento.

Isso levou à definição de um framework de 3 pilares para testar a narrativa antes de fechar a solução:

| Pilar | Pergunta | Status inicial |
|---|---|---|
| 1. Margem | Marketplace tem margem estruturalmente pior? | A testar |
| 2. ROAS/CAC | Marketplace tem pior retorno de mídia mesmo com receita real? | A testar |
| 3. Causa-raiz | Por que o Marketplace performa pior — canal, mix de produto, mix de cliente, ou custo de plataforma? | Pilar adicionado depois — o conselho já havia identificado como "causa-raiz pouco clara fora do Marketplace" |

## 5. Scripts desenvolvidos para testar os pilares

Dois scripts complementares, no mesmo padrão de pastas do projeto (`data/` + `metrics/output/`):

- **`analise_convergencia.py`** — 3 blocos de teste:
  - **Bloco A** (escala/granularidade entre `vendas.csv` e `marketing.csv`) — checagem necessária antes de confiar em qualquer reconciliação de ROAS.
  - **Bloco B** (causa-raiz da margem do Marketplace) — testou 5 hipóteses: mix de categoria, composição de custo, mix de cliente/RFM, desconto por categoria, ticket médio/método de pagamento.
  - **Bloco C** (cruzamentos entre bases) — atendimento x canal, motivo de devolução x canal, estoque crítico x categoria mais vendida no Marketplace.
- **`analise_final.py`** — consolida os 3 pilares num relatório único, incluindo o cálculo que faltava (ROAS reconciliado, filtrado ao período correto).

## 6. Resultados

### Bloco A — o problema de escala explicava parte da distorção, não tudo
`marketing.csv` cobre até dezembro/2025, enquanto `vendas.csv` só vai até janeiro/2024 — quase 2 anos de campanhas sem venda correspondente na base. Filtrando só campanhas dentro do período de vendas, o fator de distorção caiu de 46,5x para 16,7x — ainda alto, mas a maior parte do exagero veio do período errado, não de um erro sistemático de atribuição.

### Bloco B — causa-raiz encontrada: frete/logística do Marketplace
Quatro hipóteses testadas e descartadas (mix de categoria, mix de cliente, desconto por categoria, ticket médio/pagamento — todas com diferença desprezível ou na direção contrária do esperado). A quinta hipótese foi a resposta: **custo de frete do Marketplace é 4,93% da receita, contra 0,42%–1,12% dos demais canais** — quase 5x maior, isolado, sem afetar o custo de produto (praticamente idêntico entre canais).

### Bloco C — achado de apoio
"Atraso na entrega" é proporcionalmente mais comum nas devoluções do Marketplace (23,6%) do que na média geral (19,6%) — mesmo sintoma logístico, capturado de forma independente em outra base.

### Pilar 2 fechado — ROAS reconciliado por período
Com o filtro de período corrigido, o Marketplace passou da **pior posição** (3,02x, o mais baixo entre os 7 canais no ROAS bruto) para a **2ª melhor posição** em ROAS reconciliado com receita real de venda. O "duplo sinal" não se sustenta — o Marketplace não é ruim nos dois lados, é ruim só na margem.

**Ressalva documentada:** mesmo com o filtro por período de início de campanha, 30,3% das campanhas incluídas ainda têm término posterior ao fim de `vendas.csv` (R$ 23,3M de R$ 75,3M de investimento no filtro) — um resíduo de imprecisão que não muda a conclusão (a inversão de ranking foi grande demais pra ser explicada por esse resíduo), mas que deve ser citado como limitação de dado conhecida, não escondido.

## 7. Conclusão final

| Pilar | Status | Achado |
|---|---|---|
| 1. Margem | **Confirmado** | Marketplace: 51,42% vs. 55,22% dos demais canais (gap de 3,79pp) |
| 2. ROAS reconciliado | **Não sustenta** | Marketplace na posição 2 de 7 (1 = melhor) — descartado como evidência de pitch |
| 3. Causa-raiz | **Confirmado** | Frete/logística do Marketplace desproporcional — R$ 158.789,76 de margem recuperável estimada |

**Narrativa final:** abrir com o sintoma (margem do Marketplace abaixo dos demais canais), fechar com a causa-raiz (custo de frete/logística desproporcional, provavelmente ligado à estrutura de comissão da plataforma), com oportunidade quantificada. O ROAS não entra como evidência central — vira conteúdo de Governança e Riscos, documentando a limitação de dado encontrada (atribuição de marketing não confiável sem reconciliação).

---

## 8. Alinhamento — o que já dá para trabalhar vs. o que ainda precisa de investigação

### ✅ Já dá para avançar com isso

- **Diagnóstico Executivo e Pitch:** narrativa fechada — sintoma (margem) → causa-raiz (frete/logística) → oportunidade (R$ 158,8 mil). Não depende de mais dados.
- **Business Case:** a oportunidade quantificada do Marketplace (R$ 158,8 mil) já pode entrar como o número central dessa vertente.
- **Governança e Riscos:** dois conteúdos prontos para essa seção — (1) a limitação de confiabilidade do ROAS/CAC de marketing, incluindo o porquê (mismatch de período + possível problema de atribuição); (2) o viés de priorização e risco de alucinação do classificador de atendimento (já estava mapeado no relatório do conselho).
- **Dashboard de gestão:** os dados de margem por canal, causa-raiz de frete, e os cruzamentos do Bloco C já estão prontos pra virar visualizações — cobre margem, canal e uma camada de atendimento/estoque, como a banca pede.

### 🔲 Ainda precisa de investigação ou decisão

- **Confirmar com a organização do bootcamp** se "Agentes desenvolvidos" (plural, na grade de nota) implica expectativa de mais de um agente de IA — isso ficou pendente desde o relatório do conselho e ainda não foi resolvido.
- **Reconciliação de ROAS mais rigorosa (opcional):** dá para apertar o filtro do Pilar 2 exigindo que a campanha também *termine* dentro do período de vendas.csv (não só comece) — reduziria ainda mais o resíduo de 30,3%. Não é bloqueante pra conclusão atual, mas fortaleceria a evidência se houver tempo.
- **Causa da comissão/frete do Marketplace:** os dados mostram o sintoma (frete 5x maior), mas não explicam o mecanismo exato (comissão de plataforma, transportadora terceirizada, etc.) — isso não está nos CSVs; se quiserem aprofundar, seria via pesquisa de mercado sobre estrutura de custo típica de marketplaces de moda/beleza, não via dados.
- **Log de prompts do classificador de atendimento:** ação recomendada pelo próprio conselho ("primeira coisa a fazer") e que, pelo que constava até aqui, ainda não tinha sido formalmente iniciada como artefato de processo.
- **Agente de atendimento:** ainda não construído — é a próxima peça grande do escopo (Módulo B do case), separada de toda essa investigação de margem.

---

*Documento gerado como artefato de processo — consolida o raciocínio completo da conversa entre Tinoco e Claude, da crítica inicial de Claudio Azzi até o fechamento dos 3 pilares via `analise_convergencia.py` e `analise_final.py`.*
