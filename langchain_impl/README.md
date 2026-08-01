# Implementaciones con LangChain

Esta carpeta concentra implementaciones de los ejercicios de TravelOps usando componentes de LangChain.

## Archivos

- `exercise01_single_agent_langchain.py` — Agente único con memoria conversacional
- `exercise02_agent_with_tools_langchain.py` — Agente con herramientas usando `create_tool_calling_agent` + `AgentExecutor`
- `exercise03_multi_agent_langchain.py` — Orquestación multi-agente con especialistas
- `exercise04_rag_langchain.py` — Agente RAG con recuperación de contexto
- `exercise05_booking_workflow_langchain.py` — Workflow de reserva con estado y confirmación
- `common.py` — utilidades compartidas: configuración LLM, `get_langchain_model()`, `invoke_with_history()`

## Cómo se crean los agentes en LangChain

### Agente con herramientas (ejercicio 02)

LangChain proporciona funciones de fábrica en `langchain.agents` para crear agentes.
La forma recomendada para modelos que soportan tool calling (Anthropic, OpenAI) es:

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool

# 1. Definir herramientas
tools = [StructuredTool.from_function(mi_funcion), ...]

# 2. Construir prompt — DEBE incluir {input} y {agent_scratchpad}
prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un asistente de viajes..."),
    MessagesPlaceholder("chat_history", optional=True),   # historial
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),               # razonamiento del agente
])

# 3. Obtener el modelo de chat
from langchain_impl.common import get_langchain_model
llm = get_langchain_model(temperature=0.2)

# 4. Crear el agente y su ejecutor
agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. Invocar con historial
resultado = executor.invoke({
    "input": "Busca vuelos de Lima a Madrid",
    "chat_history": [],   # lista de BaseMessage previos
})
print(resultado["output"])
```

El `AgentExecutor` maneja automáticamente el ciclo
**Reason → Act (tool call) → Observe (tool result) → Respond**,
que en el ejercicio 02 se implementaba manualmente.

### Otras opciones de fábrica

| Función | Cuándo usarla |
|---|---|
| `create_tool_calling_agent` | Modelos con tool calling nativo (Anthropic, OpenAI) — **recomendado** |
| `create_react_agent` | Cualquier modelo; usa formato ReAct en texto plano |
| `create_json_chat_agent` | Modelos que responden en JSON |

### Agentes sin herramientas (ejercicios 01, 03, 04, 05)

Para agentes conversacionales sin uso de herramientas es suficiente con
invocar el modelo directamente usando `invoke_with_history()` de `common.py`:

```python
from langchain_impl.common import invoke_with_history

respuesta = invoke_with_history(
    system_prompt="Eres un experto en viajes...",
    history=[{"role": "user", "content": "¿Qué llevar a Tokio?"}],
)
```

## Ejecución rápida

```bash
python langchain_impl/exercise01_single_agent_langchain.py
python langchain_impl/exercise02_agent_with_tools_langchain.py
python langchain_impl/exercise03_multi_agent_langchain.py
python langchain_impl/exercise04_rag_langchain.py
python langchain_impl/exercise05_booking_workflow_langchain.py
```

## Dependencias

```bash
pip install langchain langchain-core langchain-text-splitters langchain-openai langchain-anthropic
```

> Si el endpoint no soporta tool calling nativo o `langchain.agents` no está
> instalado, `exercise02` cae automáticamente al ciclo manual original.
> `common.py` aplica un fallback HTTP cuando los clientes LangChain fallan.
