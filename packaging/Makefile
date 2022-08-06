NAME='ObjectViz'

ifdef WITH_NAME
	NAME=$(WITH_NAME)
endif

ifdef WITH_DEBUG
	NAME=$(NAME)-debug
endif

ifdef ComSpec
	RM=cmd /C del /F /Q
	RMDIR=cmd /C rd /S /Q
	MV=cmd /C move
	condiment=python -m condiment
	installer="\Program Files (x86)\Inno Setup 6\iscc.exe" packaging/$(NAME).iss
	requirements=packaging$(SEP)requirements_windows.txt
	SET=$(set)
	python=python
	SEP=$(strip '\\')
	pyinstaller=pyinstaller
else
	UNAME_S = $(shell uname -s)
	RM=rm -f
	RMDIR=rm -rf
	MV=mv
	installer=tar -C dist -caf dist/$(NAME).tar.bz2 $(NAME) --warning=no-file-changed || true
	make_icon=packaging/create_icon.sh
	python=python
	pyinstaller=$(python) -m PyInstaller
	condiment=$(python) -m condiment
	requirements=requirements_linux.txt
	kamidana=kamidana
	ifeq ($(UNAME_S), Darwin)
		requirements=requirements_osx.txt
		installer=packaging/fix_osx_package.sh; hdiutil create dist/$(NAME).dmg -srcfolder dist/$(NAME).app -ov
		make_icon=packaging/create_osx_icon.sh data/icons/icon1024.png
		python=python
		condiment=/usr/local/bin/condiment
		pyinstaller=pyinstaller
	endif
	SET=$(export)
	SEP='/'
endif

ifdef WINEARCH
	requirements=packaging$(SEP)requirements_windows.txt
	kamidana=wine kamidana
	installer=wine "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" packaging/project.iss
	SEP=/
endif

all: Deps BundleKV Prepare Templates Cythonize Package Installer Restore

Atlas:
	$(RM) src/data/theme-*.png
	$(python) -m kivy.atlas src/data/theme 4096 src/data/*.png src/data/menu/menu_*.png src/data/keys/*.png src/data/icons/*.png src/data/mone/*.png src/data/parts/*.png

BundleKV:
	$(python) packaging/bundle_kv.py

Deps:
	$(python) -m pip install -r $(requirements) | tee
	$(python) -m pip install -U -r packaging$(SEP)requirements_moving.txt | tee

Prepare:
	# main
	-$(MV) src$(SEP)main.py src$(SEP)_main.py
	$(condiment) src$(SEP)_main.py -o src$(SEP)main.py
	# config_patch
	-$(MV) src$(SEP)config_patch.py src$(SEP)_config_patch.py
	$(condiment) src$(SEP)_config_patch.py -o src$(SEP)config_patch.py
	-$(RM) src$(SEP)_config_patch.py src$(SEP)_main.py src$(SEP)_contact.py
	-$(RMDIR) src/data/menu src/data/keys src/data/parts src/data/mone/ src/data/icons/logo.svg

Templates:
	# prepare setup filespr
	git describe --tags > version.txt
	$(kamidana) --data=packaging/preprocess/$(NAME).json --additionals=packaging/preprocess/helpers.py packaging/preprocess/project.spec | cat > packaging/project.spec
	$(kamidana) --data=packaging/preprocess/$(NAME).json --additionals=packaging/preprocess/helpers.py packaging/preprocess/project.iss | cat > packaging/project.iss

Cythonize:
	$(python) packaging$(SEP)setup.py build_ext --inplace

Dev:
	env WITH_DEV=True $(python) packaging$(SEP)setup.py build_ext --inplace

Package:
	-$(RMDIR) build
	-$(RMDIR) dist/$(NAME)
	$(pyinstaller) packaging$(SEP)project.spec -y --clean
	git describe --tags > dist/$(NAME)$(SEP)version.txt

Installer:
	$(installer)

Restore:
	git checkout .

Icon:
	$(make_icon)

lint:
	pylint --rcfile .pylint-rc main.py

hook:
	# Install pre-commit git hook to check your changes for styleguide
	# consistency.
	# Thanks again, Kivy <3 -- Cheaterman
	cp tools/pep8checker/pre-commit.githook .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit


po:
	grep -e '^ *"\(tr_title\|tr_desc\)"' src/settings.json      |\
		sed -s 's/^ *[^:]*: \(.*\),*$$/tr._(\1)/'     |\
		sed -s 's/,)$$/)/'                            \
		> src/settings_tmp.py
	#
	xgettext -Lpython --from-code utf-8 --output=messages.pot **/*.py **/*.kv
	rm src/settings_tmp.py
	mkdir -p src/data/po/
	-msgmerge --update --no-fuzzy-matching --backup=off src/data/po/fr.po messages.pot
	-msgmerge --update --no-fuzzy-matching --backup=off src/data/po/en.po messages.pot
	-msgmerge --update --no-fuzzy-matching --backup=off src/data_override/cn/po/zh.po messages.pot
	-msgmerge --update --no-fuzzy-matching --backup=off src/data_override/cn_2/po/zh.po messages.pot

mo:
	mkdir -p src/data/locales/fr/LC_MESSAGES
	mkdir -p src/data/locales/en/LC_MESSAGES
	mkdir -p src/data_override/cn/locales/zh/LC_MESSAGES
	mkdir -p src/data_override/cn_2/locales/zh/LC_MESSAGES
	msgfmt -c -o src/data/locales/fr/LC_MESSAGES/app.mo src/data/po/fr.po
	msgfmt -c -o src/data/locales/en/LC_MESSAGES/app.mo src/data/po/en.po
	msgfmt -c -o src/data_override/cn/locales/zh/LC_MESSAGES/app.mo src/data_override/cn/po/zh.po
	msgfmt -c -o src/data_override/cn_2/locales/zh/LC_MESSAGES/app.mo src/data_override/cn_2/po/zh.po
