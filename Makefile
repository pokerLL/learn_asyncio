REPO_URL := git@github.com:pokerLL/learn_asyncio.git

init:
	git init
	git remote add origin $(REPO_URL)
	poetry init

commit:
	git add .
	@if [ "$(msg)" != "" ]; then \
		git commit -m "$(msg)"; \
	else \
		git commit -m "update"; \
	fi


push: commit
	git push