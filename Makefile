IMAGE      := pada-diit
DATA       := $(CURDIR)/data
OUTPUT     := $(CURDIR)/output

REGISTERED := $(DATA)/registered.csv
PENDING    := $(DATA)/pending.csv
DB         := $(OUTPUT)/diit_contracts.db
FIGURES    := $(OUTPUT)/figures

SOURCES    ?= $(wildcard $(DATA)/*.xlsx)

.PHONY: build rebuild stats clean help

help:
	@echo ""
	@echo "Usage:"
	@echo "  make build      Build docker image"
	@echo "  make rebuild    Entire pipeline load sources, build db, run all analyses"
	@echo "  make stats      Re run stat tests only against existing db (faster)"
	@echo "  make clean      Remove output db and figures"
	@echo ""
	@echo "Overrides (optional):"
	@echo "  REGISTERED=path/to/registered.csv"
	@echo "  PENDING=path/to/pending.csv"
	@echo "  SOURCES='file1.xlsx file2.xlsx ...'"
	@echo "  DB=path/to/output.db"
	@echo "  FIGURES=path/to/figures/dir"
	@echo ""

build:
	docker build --network=host -t $(IMAGE) .

rebuild: build
	mkdir -p $(OUTPUT)
	docker run --rm \
		--user "$(shell id -u):$(shell id -g)" \
		-v "$(DATA):/app/data" \
		-v "$(OUTPUT):/app/output" \
		$(IMAGE) \
		--registered $(subst $(DATA),/app/data,$(REGISTERED)) \
		--pending $(subst $(DATA),/app/data,$(PENDING)) \
		$(if $(SOURCES),--sources $(subst $(DATA),/app/data,$(SOURCES)),) \
		--db $(subst $(OUTPUT),/app/output,$(DB)) \
		--figures-dir $(subst $(OUTPUT),/app/output,$(FIGURES))

stats: build
	mkdir -p $(OUTPUT)
	docker run --rm \
		--user "$(shell id -u):$(shell id -g)" \
		-v "$(OUTPUT):/app/output" \
		$(IMAGE) \
		--db $(subst $(OUTPUT),/app/output,$(DB)) \
		--figures-dir $(subst $(OUTPUT),/app/output,$(FIGURES))

clean:
	rm -f $(DB)
	rm -rf $(FIGURES)
