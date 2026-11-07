# ScamShield v1.0

**Know the risk before you trust.**

An educational tool for inspecting observable indicators in a public sample of Solana address activity. The application queries Mainnet using real blockchain data and provides verifiable evidence. It does not connect wallets, request seed phrases, sign transactions, or move funds.

The public interface is in English, including help pages, messages, and indicators. Summaries default to English; the language selector also supports explanations in Portuguese.

## Getting started

The ZIP contains the `scamshield` folder. Extract the entire ZIP and open that folder in VS Code or File Explorer.

Run the following commands in **PowerShell**, inside the folder containing `app.py`. Do not open `index.html` directly: Flask must be running.

### 1. Install Python on Windows 11

Install Python from the [official Windows downloads page](https://www.python.org/downloads/windows/), choosing a compatible stable version.

This project was tested with Python 3.12. Use an updated release of your chosen Python series. Rust, Node.js, React, and TypeScript are not required.

When using the classic installer, enable the Python launcher and the option to add Python to PATH, when available. On a school-managed computer, follow the authorized installation process.

Close and reopen PowerShell after installation.

```powershell
py -3.12 --version
```

This command checks whether Python 3.12 is installed.

If you have another compatible version, use `py -3 --version` and replace the environment creation command with `py -3 -m venv .venv`. Versions other than Python 3.12 were not verified in this delivery.

### 2. Open the project folder

```powershell
cd "C:\path\to\your\extracted\scamshield"
```

Replace the example path with the actual location.

Tip: open the folder in File Explorer, click the address bar, type `powershell`, and press Enter.

### 3. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

This creates a `.venv` folder containing an isolated Python environment for the project. Dependencies do not need to be installed globally.

The following commands call that Python executable directly. **You do not need to activate scripts or change PowerShell's execution policy.**

### 4. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

`pip` downloads Flask, Requests, python-dotenv, and Waitress. SQLite is included with Python.

An internet connection is required to install dependencies.

### 5. Configure the environment

```powershell
Copy-Item .env.example .env
notepad .env
```

Run `Copy-Item` only during initial setup. Do not overwrite an existing configured `.env` file.

Use Notepad to adjust the settings. To get started, keep:

```dotenv
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
RPC_TIMEOUT=8
TRUSTED_HOSTS=localhost,127.0.0.1,[::1]
LLM_ENABLED=false
LLM_URL=http://127.0.0.1:11434/api/chat
LLM_MODEL=qwen2.5:1.5b
LLM_API_KEY=
AI_DAILY_LIMIT=20
```

The public RPC endpoint works without an API key, but rate limits may apply.

If you use another provider, configure a **Solana Mainnet HTTPS endpoint**. The application verifies the network using `getGenesisHash`.

The provider URL is never sent to the browser. Do not publish `.env` if it contains API keys.

### 6. Start Flask

```powershell
.\.venv\Scripts\python.exe app.py
```

Keep this terminal open. The development server should announce:

```text
http://127.0.0.1:5000
```

Press Ctrl+C to stop the server. Debug mode is disabled.

### 7. Open the application

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000).

Paste a public address, select five transactions to get started, and click **Analyze Wallet**.

The status indicator at the top confirms only backend availability. Blockchain connectivity is checked during analysis.

Use the example button or paste:

```text
vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg
```

This address appears in the [official getAccountInfo documentation](https://solana.com/docs/rpc/http/getaccountinfo).

Its use here does not imply ownership, suspicion, or reputation. Its activity may change. Queries are strictly read-only.

## How it works

1. Validates Base58 characters and a decoded length of 32 bytes.
2. Verifies Mainnet, reads account metadata, and retrieves up to 25 recent signatures.
3. Retrieves transaction details using `getTransaction`, `jsonParsed`, `finalized` commitment, and legacy/v0 support.
4. Applies deterministic rules and reports missing data.
5. Displays evidence, the observed period, a local or optional AI explanation, and JSON export.

### The three indicators

| Indicator | Criteria | Interpretation |
| --- | --- | --- |
| Activity Burst | At least five signatures within 60 seconds, representing at least 50% of the dated sample; no missing timestamps | Observed concentration, not proof of authorship or fraud |
| Repetitive Transfers | The same destination and exact amount across three distinct transactions containing successful explicit outgoing SOL transfers | Repetition may represent legitimate payments |
| Limited Observed History | Fewer than ten signatures, less than 24 hours, or gaps in the available data | A coverage limitation that adds no points |

The parser recognizes outer and inner **System Program** instructions of type `transfer`, with a positive integer amount, the analyzed address as the source, and a different destination.

Transfers are not inferred from net balance changes. SPL tokens, swaps, `transferWithSeed`, NFTs, and arbitrary programs are not interpreted.

`insufficient_data` means the rule could not be calculated reliably.

`not_triggered` means the criterion was not observed within the analyzable subset.

**Neither status means “safe wallet.”**

### Experimental Alert Index

Each triggered behavioral rule adds 50 points. Coverage adds zero points.

The index ranges from 0 to 100 and is available only when both behavioral rules can be calculated. Otherwise, its value is `null`, and only explicitly partial observed points are shown.

This index is not a scam probability. Classification accuracy has not been validated.

## Optional AI with Ollama

Without Ollama, the application remains functional using a clearly identified **local rule-based explanation**. This is not generative AI.

The optional adapter uses the [Ollama chat API](https://docs.ollama.com/api/chat).

By default, the model runs locally on the computer, consuming memory, processing power, and energy without a per-token API charge. The model is not included in the ZIP.

### 1. Install Ollama

Follow the [official Windows installation instructions](https://docs.ollama.com/windows).

### 2. Download the model

With Ollama running, execute:

```powershell
ollama pull qwen2.5:1.5b
```

The first download may take some time. Disk requirements and performance depend on the computer.

This model is a small suggested starting point. Output quality requires human evaluation. Check the model's license before redistributing it.

### 3. Test and warm up the model

Before the demonstration, run:

```powershell
ollama run qwen2.5:1.5b "Explain in one sentence why unusual activity does not prove fraud."
```

### 4. Enable the integration

In `.env`, change:

```dotenv
LLM_ENABLED=false
```

to:

```dotenv
LLM_ENABLED=true
```

Restart Flask and select **Use optional AI explanation**.

The adapter sends only metrics and rule statuses. Addresses, signatures, memos, and program logs are not included in the prompt.

Responses are labelled `llm_unverified`. They do not change the index and are never executed as code.

The AI read timeout is 20 seconds. A cold model or a slow CPU may cause the application to use the local fallback.

Resource limits include:

- `num_predict=512`.
- A requested context size of 4,096 tokens.
- Input limited to 8,000 characters.
- Up to 20 attempts per day.
- Rejection of truncated responses.
- Optional explanation caching for one hour.

A compatible remote instance may use an HTTPS `LLM_URL` and a backend-only `LLM_API_KEY`. This option requires an authorized operator to review the service's terms and costs.

The URL is fixed in the server configuration. Users cannot submit provider URLs through the form.

**Validation status:** the LLM integration was tested with mocks. Inference using an actual Ollama model was not executed in this environment. Real blockchain analysis and the deterministic explanation were executed.

Do not present an execution as generative AI while its explanation `source` is `local`.

## Tests

Install the test dependencies and run the suite:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

The suite uses mocks and synthetic data, without network requests.

It covers:

- Address validation and invalid input.
- Incomplete RPC responses.
- Timeouts and HTTP 429.
- Caching.
- Repetitive transfers and activity bursts.
- Coverage limitations.
- Report generation.
- Quotas and optional AI behavior.

Executed commands and results are recorded in `docs/VALIDATION.md`.

### Separate live integration check

With the application dependencies installed, run:

```powershell
.\.venv\Scripts\python.exe scripts\live_smoke.py --limit 5 --output live_report.json
```

The script queries Mainnet and saves the report to the specified file.

It returns exit code 1 if the RPC request fails and exit code 2 if no transaction details are retrieved.

It is not automatically included in the pytest suite.

The included `docs/live_capture.json` is a **historical capture of real data from November 7, 2026**. It is not live data, and the dashboard never loads it automatically.

### PowerShell API example

With the server running, open another PowerShell window:

```powershell
$scamshieldBody = @{
    wallet = "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg"
    limit = 5
    language = "en"
    use_ai = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/analyze" -Method Post -ContentType "application/json" -Body $scamshieldBody
```

`ConvertTo-Json` converts the fields into JSON. `Invoke-RestMethod` sends the request.

The complete API contract is described in sections 25 and 26 of `docs/technical.md` and in the technical Word document.

## Cache, history, and privacy

The database at `instance/scamshield.sqlite3` is created automatically. MySQL and manual migrations are not required.

Storage limits:

- Signature and account metadata cache: 60 seconds.
- Transaction and genesis hash cache: one hour.
- Maximum cache size: 2,000 entries.
- Analysis history: up to seven days and 500 reports.
- Cleanup occurs during subsequent analyses.

Data may remain on disk if the application is not run again. There is no public history page.

The RPC provider receives the queried address. The database stores associations between queries and public addresses. Protect this file.

To delete local data:

1. Stop the server.
2. Delete `instance/scamshield.sqlite3`.
3. Delete its associated `-wal` and `-shm` files, if present.

This removes cache, history, and counters. It does not change the blockchain.

## Implemented security measures

- Base58, field, and type validation.
- JSON request bodies limited to 4 KiB.
- Up to 25 transaction details per analysis.
- A 45-second collection deadline checked between RPC calls.
- Connection and read timeouts.
- Up to one RPC retry and no automatic AI retries.
- Rate limits of six analyses per IP per minute and 30 globally per minute.
- Up to two concurrent analyses per process.
- Parameterized SQLite queries.
- Secrets stored only in the server environment.
- Error messages that avoid exposing provider details.
- Template escaping and frontend rendering with `textContent`.
- Explorer links constructed from validated Base58 values.
- Content Security Policy and protective response headers.
- Rejection of client-supplied provider URLs.
- Disabled HTTP redirects.
- An allowlist of read-only RPC methods.

The backend does not trust `X-Forwarded-For`.

When deployed behind a proxy, users may share the same per-IP limit unless the deployment is configured appropriately.

This MVP is not hardened as a public service against distributed attacks.

## Serving with Waitress

For a local WSGI deployment, stop the Flask development server and run:

```powershell
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 app:app
```

Public hosting requires:

- HTTPS.
- An allowed domain configured in `TRUSTED_HOSTS`.
- A reverse proxy with appropriate request limits.
- Persistent storage.

Use one application instance for this MVP. The concurrency semaphore does not coordinate separate processes.

Do not expose the Flask development server publicly.

Paid hosting is not required to present a locally recorded demonstration.

## Troubleshooting

| Symptom | Suggested action |
| --- | --- |
| `py` is not recognized | Reopen the terminal after installation and check the Python launcher and PATH |
| `ModuleNotFoundError` | Install requirements using the exact `.venv\Scripts\python.exe` executable |
| Port 5000 is already in use | Stop the previous process or run Waitress on port 5001 |
| HTTP 429 | Respect Retry-After, avoid repeated clicks, and use a sample limit of five |
| RPC unavailable or HTTP 403 | Check the internet connection and `.env`; public endpoints may block IP addresses |
| `wrong_network` | Configure Mainnet rather than Devnet; the application does not switch networks automatically |
| Insufficient data | Treat this as a valid outcome; do not force an index or invent activity |
| Explanation remains local | Check LLM_ENABLED, Ollama availability, the downloaded model, timeout, and fallback_reason |
| Database is locked | Avoid multiple processes and stop duplicate application instances |
| Host is not allowed | Use localhost or 127.0.0.1; configure TRUSTED_HOSTS for an authorized deployment |

## Limitations and roadmap

The MVP does not provide identity verification, support for every token, external reputation checks, pre-signing simulation, complete transaction history, or validated fraud detection accuracy.

The application trusts the RPC provider. It does not independently validate blockchain consensus.

Alerts describe observations, not accusations.

Planned improvements:

- Tested SPL token parsing.
- Bounded pagination.
- Collection of appropriately labelled evaluation data.
- Measurement of false positives.
- Pre-signing simulation as a separate module.

Login, a proprietary token, NFTs, and payments are outside the MVP scope.

## Hackathon participation and attribution

Read `docs/PITCH.md` and `docs/DEVELOPMENT_PLAN.md`.

Register the team, obtain parental permission where applicable, keep development within the official event window, and follow the submission portal linked by the event.

Beginner eligibility depends on the team, not simply on limited Solana experience.

The documentation distinguishes general rules from confirmed event-specific information.

**AI assistance:** ChatGPT substantially assisted with research, architecture, documentation, code generation, interface implementation, and tests for this version on November 7, 2026.

The developer must review the code, record subsequent changes, and disclose this assistance in the submission. Do not claim that all code was written manually.

Ollama is an optional runtime integration, separate from the AI assistance used to develop the project.

Libraries include Flask/Jinja/Werkzeug, Requests, python-dotenv, Waitress, and pytest. SQLite is part of Python's standard library.

No code from a previous personal project was imported into this delivery.

Preserve dependency and model licenses as applicable. This README does not assign a publication license to the project; the team should choose a repository license before publishing.

## Official references

- [Solana Hackathon event](https://events.mlh.com/events/15200-solana-hackathon)
- [MLH Standard Hackathon Rules](https://github.com/MLH/mlh-policies/blob/main/standard-hackathon-rules.md)
- [Solana RPC documentation](https://solana.com/docs/rpc)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Flask deployment documentation](https://flask.palletsprojects.com/en/stable/deploying/)

The complete reference list is available in `docs/technical.md`.
