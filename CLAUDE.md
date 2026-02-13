4# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hebrew-language Telegram bot for Jewish prayer schedule (Shabbat) templating. Users upload Word (.docx) or PowerPoint (.pptx) templates with `{{token}}` placeholders, specify a city in Israel, and the bot fills the template with prayer times from the yeshiva.org.il API. Supports scheduled weekly distribution via EventBridge.

## Build & Deploy Commands

```bash
# Build
sam build

# Build with container (for consistent env)
sam build --use-container

# Deploy (first time, interactive)
sam build && sam deploy --guided

# Deploy (subsequent, uses samconfig.toml)
sam build && sam deploy

# Invoke locally with test event
sam local invoke PTBFunction --event events/event.json

# Tail deployed logs
sam logs -n PTBFunction --stack-name TemplaterTelegramBotNew --tail

# Run tests
pip install -r tests/requirements.txt
python -m pytest tests/unit -v
AWS_SAM_STACK_NAME=<stack-name> python -m pytest tests/integration -v

# Delete stack
sam delete
```

## Architecture

**Runtime**: Python 3.13 on AWS Lambda with Function URL as Telegram webhook.

**Entry point**: `ptb/ptb_lambda.py::lambda_handler` — routes EventBridge triggers to `schedule_send_templates.send_all_templates()` and Telegram webhooks to the conversation handler.

**Conversation flow** (ConversationHandler states):
1. User uploads .docx/.pptx → `LOCATION` state (ask for city)
2. User enters city → template filled → `CHOOSING` state (subscribe to weekly schedule?)
3. User chooses → if yes, template saved to S3/DynamoDB → `DONE`

**Key modules under `ptb/`**:
- `ptb_lambda.py` — Lambda handler, Telegram bot setup, conversation state machine
- `templater/templater.py` — Template processing engine with class hierarchy: `Templater` (ABC) → `XMLTemplater` → `OfficeTemplater` (ABC) → `WordTemplater` / `PowerPointTemplater`. Top-level `fill_template(city, office_file_name, target_directory)` is the main API
- `templater/lex.py` — PLY-based lexer/parser for template expressions (e.g., `{{UP(צאת_שבת - 10)}}` rounds up a prayer time minus 10 minutes)
- `templater/places.txt` — HTML snippet mapping Israeli city names to yeshiva.org.il place IDs
- `template_manager.py` — DynamoDB/S3 persistence for scheduled templates
- `schedule_send_templates.py` — EventBridge-triggered weekly template distribution

**Template expression language** (parsed by `lex.py`):
- Variable names map to prayer times (Hebrew or English): `פרשה`, `כניסת_שבת`, `צאת_שבת`, `parasha`, `enter_time`, etc.
- Arithmetic: `{{כניסת_שבת - 10}}` subtracts 10 minutes
- Rounding: `{{UP(צאת_שבת)}}` rounds up to nearest 5 min, `{{DOWN(...)}}` rounds down

**AWS resources** (defined in `template.yaml`):
- Lambda function (`PTBFunction`) with Function URL (no auth)
- DynamoDB table `"template"` for schedule metadata
- S3 bucket for stored template files

**Environment variables** (loaded from `.env` via python-dotenv):
- `TELEGRAM_TOKEN` — Bot token from BotFather
- `YESHIVA_BOT_UA` — User-Agent header for yeshiva.org.il API requests (uses `curl_cffi` for browser impersonation)
