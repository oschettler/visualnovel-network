.PHONY: help alles deck test art portraits geruest watch clean

help:
	@echo "Ziele:"
	@echo "  make alles      Grafik erzeugen, Tests laufen lassen, Deck bauen"
	@echo "  make art        SVG nach GIF wandeln (tools/render_art.py)"
	@echo "  make portraits  Portraits neu zeichnen (tools/portraits.py)"
	@echo "  make test       Engine-Tests (game/lil/vn_test.lil)"
	@echo "  make deck       Deck bauen (game/build/netzwerk.deck und .html)"
	@echo "  make geruest    Twee-Geruest aus der Novelle erzeugen (einmalig)"
	@echo "  make watch      Bei jeder Aenderung an Daten oder Lil neu bauen"
	@echo "  make clean      Erzeugte Dateien loeschen"
	@echo ""
	@echo "Nach jedem Bau das Deck in Decker neu oeffnen: die App kann"
	@echo "Dateien aus Sicherheitsgruenden nicht selbst nachladen."

alles: art test deck

art:
	python3 tools/render_art.py --pruefen

portraits:
	python3 tools/portraits.py

test:
	lilt game/lil/vn_test.lil

deck:
	lilt game/build/build_vn.lil

geruest:
	python3 tools/kapitel_zu_twee.py

# Braucht entr (brew install entr).
watch:
	@echo "Beobachte game/data und game/lil, Strg-C zum Beenden."
	@find game/data game/lil game/build -type f \( -name '*.twee' -o -name '*.lil' -o -name '*.csv' -o -name '*.txt' \) \
		| entr -c sh -c 'lilt game/lil/vn_test.lil && lilt game/build/build_vn.lil'

clean:
	rm -f game/build/netzwerk.deck game/build/netzwerk.html
	rm -rf game/data/art
