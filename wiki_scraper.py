import os
import shutil

from git.repo.base import Repo

import markdown_inserter

WIKI_URL = "https://github.com/{}/{}/wiki/{}"
GIT_WIKI_URL= "https://github.com/{}/{}.wiki.git"


def get_all_wiki_page_content(user, repo):
    dest_folder = "./{}_{}".format(user, repo)

    clone_wiki_content(user, repo, dest_folder)

    for path in get_all_files_path(dest_folder):
        file = open(path, "r")
        link_path = path.replace(dest_folder + '/', '').replace('.md', '')

        yield {
            'title': link_path.replace('-', ' '),
            'url': WIKI_URL.format(user, repo, link_path),
            'content': file.read()
        }


def clone_wiki_content(user, repo, dest_folder):
    # clear the dest directory if it exists
    shutil.rmtree(dest_folder, ignore_errors=True)

    repo = GIT_WIKI_URL.format(user, repo)
    print('Cloning repository {} into folder {} ...'.format(repo, dest_folder))
    Repo.clone_from(repo, dest_folder)
    print('Cloning successful!')


def get_all_files_path(path):
    files = []

    # r=root, d=directories, f = files
    for r, d, f in os.walk(path):
        for file in f:
            if '.md' in file:
                files.append(os.path.join(r, file))

    return files


if __name__ == '__main__':
    import es

    es.delete()
    es.create()

    for wiki in get_all_wiki_page_content('junegunn', 'fzf'):
        markdown_inserter.insert_markdown_doc('junegunn', wiki['content'], wiki['title'], wiki['url'])
