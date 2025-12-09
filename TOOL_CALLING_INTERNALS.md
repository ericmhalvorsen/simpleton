# Tool Calling Deep Dive: What Really Happens Under the Hood

## TL;DR

**Tool calling is a coordination between three layers**:
1. **Model**: Generates structured text that *looks like* function calls (doesn't execute anything)
2. **Inference Engine**: Parses function schemas, formats prompts, extracts structured tool calls from model output
3. **Client Library**: Sends function schemas, receives parsed tool calls, **actually executes the functions**

**The model never executes code** - it just generates JSON. The client does the real work.

---

## The Three Layers of Tool Calling

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT APPLICATION                      │
│  - Defines functions (Python/JS/etc.)                       │
│  - Sends function schemas to API                            │
│  - ACTUALLY EXECUTES functions when model requests them     │
│  - Sends results back to model                              │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP/API
┌───────────────────────▼─────────────────────────────────────┐
│                    INFERENCE ENGINE                          │
│  (vLLM, llama.cpp, OpenAI API, etc.)                        │
│  - Receives function schemas as JSON                        │
│  - Formats them into the model's prompt                     │
│  - Parses model output for function calls                   │
│  - Returns structured tool_calls objects (not raw text)     │
└───────────────────────┬─────────────────────────────────────┘
                        │ Tokens
┌───────────────────────▼─────────────────────────────────────┐
│                         MODEL                                │
│  - Sees function schemas in its context                     │
│  - Generates TEXT that looks like function calls            │
│  - Outputs JSON with function name + parameters             │
│  - DOES NOT execute anything - just predicts tokens         │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step: What Happens When You Use Tools

### 1. Client Defines Functions

```python
# This is real Python code that lives in your application
def get_weather(location: str, unit: str = "celsius") -> dict:
    """Get the current weather in a given location."""
    # Actually calls weather API, returns real data
    return {"temp": 22, "condition": "sunny"}
```

### 2. Client Sends Function Schema to Inference Engine

**What the client sends** (OpenAI format):
```json
{
  "messages": [
    {"role": "user", "content": "What's the weather in Paris?"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
          },
          "required": ["location"]
        }
      }
    }
  ]
}
```

**Key point**: The inference engine receives a **schema** (metadata), not the actual function code.

### 3. Inference Engine Formats the Prompt

The engine transforms the request into text that the model understands. Different models use different formats:

#### Example: Llama 3.1 Format (with special tokens)
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You have access to the following functions:

{"name": "get_weather", "description": "Get the current weather in a given location",
 "parameters": {"type": "object", "properties": {...}}}

When you want to call a function, respond with:
<function=get_weather>{"location": "Paris", "unit": "celsius"}</function>

<|start_header_id|>user<|end_header_id|>
What's the weather in Paris?
<|eot_id|><|start_header_id|>assistant<|end_header_id|>
```

#### Example: Generic Format (models without special tool tokens)
```
System: You are a helpful assistant with access to functions. When you need to call
a function, output ONLY a JSON object in this exact format:
{"function": "function_name", "parameters": {...}}

Available functions:
- get_weather(location: str, unit: str) - Get weather for a location

User: What's the weather in Paris?
Assistant:
```

**What's happening**:
- Function schemas are injected into the system prompt or special format
- The model sees them as regular text (it doesn't "know" about tools inherently)
- Instruction-tuned models learn to recognize this pattern from training data

### 4. Model Generates Text (Looks Like a Function Call)

The model doesn't "call" anything. It generates tokens that happen to look like JSON:

```
<function=get_weather>{"location": "Paris", "unit": "celsius"}</function>
```

Or in generic format:
```json
{"function": "get_weather", "parameters": {"location": "Paris", "unit": "celsius"}}
```

**This is just text prediction**. The model has learned from training examples that:
- When it sees function schemas in the prompt
- And the user asks a question that matches a function's purpose
- It should output structured JSON instead of natural language

**The model has no idea what `get_weather` actually does**. It just learned the pattern.

### 5. Inference Engine Parses the Response

The engine detects the function call pattern and transforms it into structured data:

**What vLLM/OpenAI API returns**:
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\": \"Paris\", \"unit\": \"celsius\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

**Key transformation**:
- **Model output** (raw text): `{"function": "get_weather", "parameters": {...}}`
- **API response** (structured): A `tool_calls` array with parsed function name and arguments

The inference engine:
- Detects function call syntax (special tokens or JSON pattern)
- Extracts function name and parameters
- Validates against the schema you provided
- Returns structured objects instead of raw text

### 6. Client Executes the Function

**This is where the actual "calling" happens** - in your application, not in the model:

```python
# Client library (e.g., OpenAI SDK) receives the response
response = client.chat.completions.create(...)

# Check if model wants to call a function
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]

    # Parse the arguments
    function_name = tool_call.function.name  # "get_weather"
    arguments = json.loads(tool_call.function.arguments)  # {"location": "Paris", ...}

    # YOU execute the function (in your Python runtime)
    if function_name == "get_weather":
        result = get_weather(**arguments)  # ← ACTUAL EXECUTION HAPPENS HERE
        # result = {"temp": 22, "condition": "sunny"}
```

**The model never executed anything**. Your client code did.

### 7. Client Sends Function Result Back

You send the result back to the model as a new message:

```python
# Send function result back
messages.append({
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps(result)  # {"temp": 22, "condition": "sunny"}
})

# Get final response
final_response = client.chat.completions.create(
    messages=messages,
    tools=tools
)
```

### 8. Model Generates Final Natural Language Response

The inference engine formats this as:

```
<|start_header_id|>user<|end_header_id|>
What's the weather in Paris?
<|start_header_id|>assistant<|end_header_id|>
<function=get_weather>{"location": "Paris"}</function>
<|start_header_id|>tool<|end_header_id|>
{"temp": 22, "condition": "sunny"}
<|start_header_id|>assistant<|end_header_id|>
```

The model generates:
```
The weather in Paris is currently sunny with a temperature of 22°C.
```

---

## Where Does a "Vanilla" Model Fall Apart?

A vanilla model (e.g., base Llama 3 without instruction tuning) **can technically output the same format**. But it fails in practice because:

### 1. **No Training on Tool Calling Patterns**

**Vanilla model output** (when given function schemas):
```
I'd be happy to help! To get the weather in Paris, you could use the get_weather
function. The function takes a location parameter which should be "Paris" and
optionally a unit parameter. If you call it, it will return...
```

**Tool-trained model output**:
```json
{"function": "get_weather", "parameters": {"location": "Paris", "unit": "celsius"}}
```

**Why the difference?**
- Vanilla model treats function schemas as documentation, explains them
- Tool-trained model has seen thousands of examples where the correct response is structured JSON
- It learned: "When function schema present + user question matches → output JSON, not explanation"

### 2. **Inconsistent JSON Format**

**Vanilla model** might output:
```json
{
  "function_name": "get_weather",  // ← Wrong key
  "params": {"location": "Paris"},  // ← Wrong key
  "unit": "celsius"  // ← Parameter in wrong place
}
```

**Tool-trained model** consistently outputs:
```json
{"function": "get_weather", "parameters": {"location": "Paris", "unit": "celsius"}}
```

The tool-trained model learned the **exact schema** from fine-tuning examples.

### 3. **Invalid JSON Syntax**

**Vanilla model**:
```json
{"function": "get_weather", "parameters": {"location": "Paris",}}  // ← Trailing comma
```

Or even worse:
```
Let me call get_weather for you with Paris as the location...
{"function": "get_weather", "parameters": {"location": "Paris"}}
```

**Tool-trained model**: Reliably outputs valid JSON, nothing else.

### 4. **Wrong Tool Selection**

Given multiple tools, vanilla model might:
- Call the wrong function
- Call multiple functions when only one is needed
- Forget to call a function and just answer directly (hallucinate data)

**Tool-trained model**: Better at reasoning about which tool to use when.

### 5. **Parameter Type Errors**

**Vanilla model**:
```json
{"function": "get_weather", "parameters": {"location": "Paris", "unit": "22"}}
                                                                         ↑
                                                                    String "22" instead of enum
```

**Tool-trained model**: Understands parameter types from schema, outputs correct types.

---

## How Do Models Learn Tool Calling?

### Fine-Tuning Process

Models are fine-tuned with examples like:

**Training example**:
```
Input:
System: You have access to: get_weather(location: str, unit: str)
User: What's the weather in Tokyo?

Expected output:
{"function": "get_weather", "parameters": {"location": "Tokyo", "unit": "celsius"}}
```

After seeing thousands of these examples, the model learns:
1. When function schemas are present
2. When user query matches a function's purpose
3. Output structured JSON with function name and parameters
4. Use the exact format from training data

### Special Training Data

Tool-capable models (GPT-4, Claude, Llama 3.1, etc.) are trained on:
- Millions of function calling examples
- Varied function schemas
- Multi-turn conversations with function results
- Error cases (wrong parameters, missing functions, etc.)

This is why they're reliable at tool calling and vanilla models aren't.

---

## Inference Engine Capabilities

Different engines handle tools differently:

### vLLM
```python
# Supports function calling via chat template
# Parses tool calls from model output
# Returns structured tool_calls in OpenAI format
response = vllm.chat.completions.create(
    model="meta-llama/Llama-3.1-70B-Instruct",
    messages=[...],
    tools=[...]  # ← vLLM handles formatting and parsing
)
```

**What vLLM does**:
1. Takes your `tools` array
2. Injects them into the model's chat template (uses model's built-in format)
3. Runs inference
4. Parses model output using regex or the model's chat template
5. Returns structured `tool_calls` objects

### llama.cpp
```bash
# Supports function calling with --chat-template
llama-server --model model.gguf --chat-template llama3.1
```

**What llama.cpp does**:
1. Uses Jinja2 chat template (defines tool format)
2. Formats tools into prompt
3. Parses model output for function calls
4. Returns structured response

**Example chat template** (Llama 3.1):
```jinja2
{% if tools %}
<|start_header_id|>system<|end_header_id|>

You have access to the following functions:
{% for tool in tools %}
{{ tool.function | tojson }}
{% endfor %}
{% endif %}
```

### OpenAI API
Fully managed - handles everything internally:
- Proprietary function calling format
- Custom parsing logic
- Potentially uses constrained generation (forces valid JSON)

---

## Advanced: Constrained Generation

Some engines use **guided decoding** to ensure valid tool calls:

### Example: Grammar-Based Sampling

Instead of letting the model freely generate any token, constrain it to valid JSON:

```python
# Pseudo-code of what some engines do
grammar = """
tool_call := '{' ws '"function"' ws ':' ws string ws ',' ws '"parameters"' ws ':' ws object ws '}'
string := '"' [a-z_]+ '"'
object := '{' (key_value (',' key_value)*)? '}'
...
"""

# Model can ONLY generate tokens that match this grammar
output = model.generate(prompt, grammar=grammar)
# Guaranteed valid JSON
```

**Engines that support this**:
- llama.cpp (with grammars)
- vLLM (with guided decoding)
- Guidance library
- Outlines library

**Benefit**: Even vanilla models can output perfect JSON with constrained generation.

---

## Special Tokens for Tool Calling

Some models have dedicated tokens:

### Llama 3.1
```
<|python_tag|>  # Indicates Python code execution
```

### Command R+
```
<|START_TOOL_USE|>
tool_name
<|START_TOOL_ARGS|>
{"arg": "value"}
<|END_TOOL_ARGS|>
<|END_TOOL_USE|>
```

These tokens help the inference engine:
- Detect when a tool call starts/ends
- Parse the content between tokens
- Distinguish tool calls from regular text

**Vanilla models don't have these tokens** - they'd output them as regular text if prompted.

---

## Real Example: Full Tool Calling Flow

### Client Code (Python)
```python
import openai

# 1. Define your function
def get_current_weather(location: str, unit: str = "fahrenheit"):
    # Real API call
    return {"temperature": 72, "condition": "sunny"}

# 2. Define function schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    }
]

# 3. Initial request
messages = [{"role": "user", "content": "What's the weather in Boston?"}]
response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools
)

# 4. Check for tool calls
message = response.choices[0].message
if message.tool_calls:
    # 5. Execute the function (CLIENT DOES THIS)
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "get_current_weather":
            function_response = get_current_weather(**arguments)

        # 6. Send result back
        messages.append(message)  # Assistant's tool call
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(function_response)
        })

    # 7. Get final response
    final_response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools
    )

    print(final_response.choices[0].message.content)
    # "The weather in Boston is currently sunny with a temperature of 72°F."
```

### What Happened Behind the Scenes

**Request 1 to OpenAI**:
```
POST /v1/chat/completions
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "What's the weather in Boston?"}],
  "tools": [...]
}
```

**OpenAI's inference engine**:
1. Formats tools into GPT-4's internal prompt format
2. Runs inference
3. Model outputs: `{"function": "get_current_weather", "parameters": {"location": "Boston"}}`
4. Engine parses this into structured tool_calls
5. Returns response with `finish_reason: "tool_calls"`

**Your client**:
1. Sees `tool_calls` in response
2. Calls your Python function `get_current_weather("Boston")`
3. Gets result: `{"temperature": 72, "condition": "sunny"}`

**Request 2 to OpenAI**:
```
POST /v1/chat/completions
{
  "messages": [
    {"role": "user", "content": "What's the weather in Boston?"},
    {"role": "assistant", "tool_calls": [...]},
    {"role": "tool", "content": "{\"temperature\": 72, \"condition\": \"sunny\"}"}
  ],
  "tools": [...]
}
```

**OpenAI's inference engine**:
1. Model sees the tool result in context
2. Generates natural language response using the data
3. Returns final answer

---

## Summary: Who Does What

| Layer | Responsibility | What It Does | What It Doesn't Do |
|-------|---------------|--------------|-------------------|
| **Model** | Text generation | Generates JSON-like text with function name & params | Execute functions, parse JSON, validate schemas |
| **Inference Engine** | Prompt formatting & parsing | Injects tools into prompt, extracts tool calls, validates format | Execute functions, know what functions do |
| **Client** | Orchestration & execution | Sends schemas, **executes functions**, sends results back | Generate text, parse model output |

**The "magic" is coordination**:
- Client defines what functions exist
- Inference engine tells the model about them
- Model decides when to use them (generates JSON)
- Inference engine structures the response
- Client executes the actual code
- Model uses results to answer the user

**Vanilla models fail** because they weren't trained on this coordination dance. They can output JSON, but not reliably, not in the right format, and not at the right times.

**Tool-capable models** are fine-tuned with thousands of examples teaching them:
- When to call functions vs answer directly
- How to format function calls exactly
- How to use function results in their response
- How to handle errors and edge cases

The inference engine makes it seamless by handling the formatting and parsing, so you don't have to manually inject function schemas into prompts or parse messy JSON from raw model output.
