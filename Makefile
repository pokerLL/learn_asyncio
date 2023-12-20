REPO_URL := git@github.com:pokerLL/learn_asyncio.git

init:
	# git init
	poetry init

commit:
	git add .
	git commit -m 'update'


push: commit
	git push