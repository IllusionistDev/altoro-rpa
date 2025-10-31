# ===== Altoro RPA: Makefile (docker compose only) =====
COMPOSE := docker compose
SERVICE := altoro-rpa

# Helper: run a python module inside a one-off container
define RUN_PY
	$(COMPOSE) run --rm $(SERVICE) bash -lc "python3 -m $(1)"
endef

.PHONY: help
help:
	@echo ""
	@echo "Altoro RPA — docker compose commands"
	@echo "------------------------------------"
	@echo "make build        Build the image"
	@echo "make up           Run full pipeline (run_all)"
	@echo "make down         Stop/remove container"
	@echo "make logs         Tail logs"
	@echo "make ps           Show service status"
	@echo "make shell        Interactive shell"
	@echo "make clean        Remove local artifacts"
	@echo "make pyver        Quick sanity check (python -V)"
	@echo "make run PART=... Run custom module (e.g., PART=src.orchestration.transaction)"
	@echo ""
	@echo "Run parts:"
	@echo "  make part1      Login (happy + negative)"
	@echo "  make part2      Account summary -> Excel"
	@echo "  make part3      Transactions + filters + high-value"
	@echo "  make part4      Transfer funds + verify"
	@echo "  make part5      Product catalog"
	@echo "  make part6      API reconciliation"
	@echo ""

.PHONY: build
build:
	$(COMPOSE) build

.PHONY: up
up: build
	# Use the service CMD (python -m src.orchestration.run_all from Dockerfile)
	$(COMPOSE) up --abort-on-container-exit --remove-orphans

.PHONY: down
down:
	$(COMPOSE) down --remove-orphans

.PHONY: ps
ps:
	$(COMPOSE) ps

.PHONY: logs
logs:
	$(COMPOSE) logs -f $(SERVICE)

.PHONY: shell
shell: build
	$(COMPOSE) run --rm $(SERVICE) bash

.PHONY: clean
clean:
	rm -rf artifacts/*
	@mkdir -p artifacts/logs artifacts/screenshots artifacts/traces artifacts/outputs
	@echo "Cleaned ./artifacts"

# ---------- Diagnostics ----------
.PHONY: pyver
pyver: build
	$(COMPOSE) run --rm $(SERVICE) bash -lc "python -V && which python && pwd && ls -la"

.PHONY: run
run: build
	$(COMPOSE) run --rm $(SERVICE) bash -lc "python3 -m $(PART)"

# ---------- Parts (use bash -lc to ensure PYTHONPATH + shell resolution) ----------
.PHONY: part1
part1: build
	$(call RUN_PY,src.orchestration.account_login)

.PHONY: part2
part2: build
	$(call RUN_PY,src.orchestration.accounts_summary)

.PHONY: part3
part3: build
	$(call RUN_PY,src.orchestration.transaction)

.PHONY: part4
part4: build
	$(call RUN_PY,src.orchestration.transfer)

.PHONY: part5
part5: build
	$(call RUN_PY,src.orchestration.products)

.PHONY: part6
part6: build
	$(call RUN_PY,src.orchestration.api_validate)

.PHONY: lintfix
fix-lint:
	black . && ruff check . --fix
