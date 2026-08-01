# Implementaciones con LangChain

Esta carpeta concentra implementaciones **desde cero** de los ejercicios de TravelOps usando componentes de LangChain.

## Archivos

- `exercise01_single_agent_langchain.py` — Agente único con memoria conversacional
- `exercise02_agent_with_tools_langchain.py` — Agente con herramientas (tool use)
- `exercise03_multi_agent_langchain.py` — Orquestación multi-agente con especialistas
- `exercise04_rag_langchain.py` — Agente RAG con recuperación de contexto
- `exercise05_booking_workflow_langchain.py` — Workflow de reserva con estado y confirmación
- `common.py` — utilidades compartidas de configuración e invocación LLM

## Ejecución rápida

```bash
python /home/runner/work/ia360_agents/ia360_agents/langchain_impl/exercise01_single_agent_langchain.py
python /home/runner/work/ia360_agents/ia360_agents/langchain_impl/exercise02_agent_with_tools_langchain.py
python /home/runner/work/ia360_agents/ia360_agents/langchain_impl/exercise03_multi_agent_langchain.py
python /home/runner/work/ia360_agents/ia360_agents/langchain_impl/exercise04_rag_langchain.py
python /home/runner/work/ia360_agents/ia360_agents/langchain_impl/exercise05_booking_workflow_langchain.py
```

## Dependencias sugeridas

```bash
pip install langchain langchain-core langchain-text-splitters langchain-openai langchain-anthropic
```

> Si un backend de LangChain falla por compatibilidad de endpoint, `common.py` aplica un fallback HTTP para mantener la ejecución.
