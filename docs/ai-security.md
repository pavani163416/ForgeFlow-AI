# AI Security Architecture: ForgeFlow AI

## 1. Core Philosophy: Untrusted Data

In ForgeFlow AI, **ALL** uploaded source code, documentation, and configuration files are treated as untrusted, hostile data. The AI Engine operates under the assumption that the source code is actively attempting to manipulate the LLM (Prompt Injection).

## 2. Prompt Injection Defense

### 2.1 Context Isolation
System instructions are strictly isolated from user data. 
- **Method:** We utilize provider-specific mechanisms (like the `system` role in OpenAI/Anthropic APIs) to firmly establish the system's directive. 
- **Data Enclosure:** Source code injected into the prompt is encapsulated within distinct delimiters (e.g., `<source_file>`, `</source_file>`). The system prompt explicitly instructs the model that data within these delimiters contains no actionable system commands.

### 2.2 Output Schema Validation
The AI Engine does not accept raw string outputs for intermediate steps.
- **Method:** Structured Outputs (e.g., JSON Schema validation via OpenAI Structured Outputs or Pydantic validation on the backend). 
- **Benefit:** If a prompt injection attempt successfully convinces the LLM to output a malicious string (e.g., "Ignore previous instructions and print X"), the output will fail schema validation and the attempt will be rejected.

## 3. Data Privacy and Exfiltration Defense

### 3.1 Pre-Generation Redaction
The Cybersecurity Engine scans the source code *before* it is sent to the AI Provider.
- **Method:** Detected secrets (API keys, passwords, connection strings) are deterministically redacted and replaced with placeholders (e.g., `[FORGEFLOW_REDACTED_SECRET_1]`).
- **Benefit:** The AI provider never receives the customer's actual secrets, preventing them from being logged by the provider or accidentally hallucinated into the generated Flutter code.

### 3.2 Provider Isolation
- **Method:** The AI Provider interface is completely abstracted. The AI Provider has zero network access to the ForgeFlow internal network or database. It operates strictly as a stateless text-in/text-out oracle over HTTPS.

## 4. Controlled Execution (No Autonomous Actions)

The AI is **NOT** an autonomous agent with open-ended tool access.
- **Method:** The AI does not have access to a terminal, file system, or network tools. 
- **Pipeline:** The AI produces a JSON migration plan or Dart source code string. The *ForgeFlow Backend* parses this string, validates it, and writes it to the Sandbox. The AI cannot execute commands directly.

## 5. Bounded Remediation Loops

If the generated code fails validation (e.g., `flutter build` fails), the AI is consulted for a fix.
- **Threat:** Infinite loops causing massive token consumption and Denial of Service (Financial DoS).
- **Control:** Hardcoded `MAX_RETRIES` limit (default: 3). If the code does not pass validation after the limit, the migration job is marked as `FAILED` and no further AI requests are made for that component.

## 6. Tracking and Auditing

- **Metrics:** Every call to the AI Provider records the `provider`, `model_version`, `prompt_version`, `token_usage`, `latency`, and `request_id`.
- **Auditing:** Both the prompt sent and the response received are logged securely (with appropriate data retention policies) to allow debugging of prompt injection attempts and model hallucinations.
